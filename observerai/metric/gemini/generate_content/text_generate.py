import json
import logging
import sys
import time
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional
from unittest.mock import patch

from observerai.context.trace_context import get_flow_id, get_span_id, get_trace_id
from observerai.driver.log_driver import LogDriver
from observerai.schema.metric import ExceptionMetric, LatencyMetric, ResponseMetric
from observerai.schema.model_metric import (
    AssistantMessage,
    ConversationMetric,
    FunctionCall,
    ModelMetric,
    Parameters,
    TokenUsageMetric,
    Tool,
    ToolCall,
    UserMessage,
)

logger = LogDriver().get_logger()

try:
    from google import genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None  # type: ignore


def _extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if hasattr(content, "text"):
        return getattr(content, "text") or ""
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        return content["text"]
    return ""


def _extract_tools_from_config(config: Any) -> Optional[list[Tool]]:
    if config is None:
        return None
    return getattr(config, "tools", None)


def intercept_gemini_generate_content(
    captured: Dict[str, Any], original_generate: Callable
) -> Callable:
    def interceptor(self, *args, **kwargs):
        captured["model"] = kwargs.get("model", "unknown")
        contents = kwargs.get("contents", [])
        if contents:
            captured["prompt"] = _extract_text_from_content(contents[0])
        else:
            captured["prompt"] = ""
        config = kwargs.get("config")
        captured["tools"] = _extract_tools_from_config(config)
        if config is not None:
            captured["params"] = {
                "temperature": getattr(config, "temperature", None),
                "max_tokens": getattr(config, "max_output_tokens", None),
                "top_p": getattr(config, "top_p", None),
                "n": getattr(config, "candidate_count", None),
                "stop": getattr(config, "stop_sequences", None),
                "frequency_penalty": getattr(config, "frequency_penalty", None),
                "presence_penalty": getattr(config, "presence_penalty", None),
            }
        else:
            captured["params"] = None

        response = original_generate(self, *args, **kwargs)

        try:
            captured["answer"] = getattr(response, "text", None) or ""
        except Exception:
            captured["answer"] = ""

        try:
            fcalls = getattr(response, "function_calls", None)
            captured["tool_calls"] = (
                [
                    ToolCall(
                        id=call.id or "",
                        type="function",
                        function=FunctionCall(
                            name=call.name or "",
                            arguments=json.dumps(call.args or {}),
                        ),
                    )
                    for call in fcalls
                ]
                if fcalls
                else []
            )
        except Exception:
            captured["tool_calls"] = []

        try:
            usage = getattr(response, "usage_metadata", None)
            captured["usage"] = (
                {
                    "prompt_tokens": getattr(usage, "prompt_token_count", 0),
                    "completion_tokens": getattr(usage, "candidates_token_count", 0),
                    "total_tokens": getattr(usage, "total_token_count", 0),
                }
                if usage
                else {}
            )
        except Exception:
            captured["usage"] = {}

        return response

    return interceptor


def metric_generate_content(
    message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
) -> Callable:
    if not isinstance(message, str):
        message = "observerai.gemini.generate_content"

    if metadata is not None and not isinstance(metadata, dict):
        metadata = None

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if genai is None:
                logger.error(
                    "observerai: missing optional dependency 'google-genai'. "
                    "Install it with: pip install observerai[gemini]"
                )
                return None

            start_time = time.time()
            captured: Dict[str, Any] = {}
            params_dict = None

            try:
                with patch.object(
                    genai.models.Models,
                    "generate_content",
                    new=intercept_gemini_generate_content(
                        captured, genai.models.Models.generate_content
                    ),
                ):
                    result = func(*args, **kwargs)

                latency = int((time.time() - start_time) * 1000)
                usage = captured.get("usage", {})
                params_dict = captured.get("params", {}) or {}
                parameters = Parameters(
                    temperature=params_dict.get("temperature"),
                    max_tokens=params_dict.get("max_tokens"),
                    top_p=params_dict.get("top_p"),
                    n=params_dict.get("n"),
                    stop=params_dict.get("stop"),
                    frequency_penalty=params_dict.get("frequency_penalty"),
                    presence_penalty=params_dict.get("presence_penalty"),
                )

                metric = ModelMetric(
                    trace_id=get_trace_id(),
                    span_id=get_span_id(),
                    flow_id=get_flow_id(),
                    name=captured.get("model", "unknown"),
                    provider="gemini",
                    endpoint="/generate_content",
                    conversation=ConversationMetric(
                        question=UserMessage(
                            content=captured.get("prompt", ""),
                            tools=captured.get("tools"),
                        ),
                        answer=AssistantMessage(
                            content=captured.get("answer", ""),
                            tool_calls=captured.get("tool_calls", []),
                        ),
                    ),
                    parameters=parameters,
                    token_usage=TokenUsageMetric(
                        prompt=usage.get("prompt_tokens", 0),
                        completion=usage.get("completion_tokens", 0),
                        total=usage.get("total_tokens", 0),
                    ),
                    response=ResponseMetric(
                        status_code=200,
                        latency=LatencyMetric(time=latency),
                    ),
                    evaluation=None,
                    metadata=metadata,
                )

            except Exception as e:
                latency = int((time.time() - start_time) * 1000)
                params_dict = params_dict or captured.get("params", {}) or {}
                if hasattr(e, "code"):
                    status_code = e.code
                elif hasattr(e, "status_code"):
                    status_code = e.status_code
                else:
                    status_code = 500

                parameters = (
                    Parameters(
                        temperature=params_dict.get("temperature"),
                        max_tokens=params_dict.get("max_tokens"),
                        top_p=params_dict.get("top_p"),
                        n=params_dict.get("n"),
                        stop=params_dict.get("stop"),
                        frequency_penalty=params_dict.get("frequency_penalty"),
                        presence_penalty=params_dict.get("presence_penalty"),
                    )
                    if params_dict
                    else None
                )

                metric = ModelMetric(
                    trace_id=get_trace_id(),
                    span_id=get_span_id(),
                    flow_id=get_flow_id(),
                    name=captured.get("model", "unknown"),
                    provider="gemini",
                    endpoint="/generate_content",
                    conversation=ConversationMetric(
                        question=UserMessage(
                            content=captured.get("prompt", ""),
                            tools=captured.get("tools"),
                        ),
                        answer=None,
                    ),
                    parameters=parameters,
                    response=ResponseMetric(
                        status_code=status_code,
                        latency=LatencyMetric(time=latency),
                    ),
                    exception=ExceptionMetric(
                        type=type(e).__name__,
                        message=str(e),
                        traceback=traceback.format_exc(),
                    ),
                    metadata=metadata,
                )

                logger.info(message, **metric.model_dump())
                print(traceback.format_exc(), file=sys.stderr)
                return None

            logger.info(message, **metric.model_dump())
            return result

        return wrapper

    return decorator
