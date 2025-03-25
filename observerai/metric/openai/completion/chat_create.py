import time
import traceback
from functools import wraps
from typing import Callable, Any, Dict, Optional
from unittest.mock import patch

from openai.types.chat.chat_completion import ChatCompletion
from openai.types.completion_usage import CompletionUsage
from openai.resources.chat.completions import Completions

from observerai.schema.metric import ResponseMetric, LatencyMetric, ExceptionMetric
from observerai.schema.model_metric import (
    ModelMetric,
    ConversationMetric,
    TokenUsageMetric,
    UserMessage,
    AssistantMessage,
    Parameters,
    ToolCall,
    FunctionCall,
    Tool,
)
from observerai.context.trace_context import get_trace_id, get_span_id, get_flow_id
from observerai.driver.log_driver import LogDriver

logger = LogDriver().get_logger()

try:
    import openai
except ImportError:
    openai = None


def intercept_openai_chat_completion(
    captured: Dict[str, Any], original_create: Callable
) -> Callable[..., ChatCompletion]:
    def interceptor(self, *args, **kwargs) -> ChatCompletion:
        captured["model"] = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        captured["prompt"] = messages[-1]["content"] if messages else ""
        captured["tools"] = kwargs.get("tools", [])

        response: ChatCompletion = original_create(self, *args, **kwargs)

        try:
            captured["answer"] = response.choices[0].message.content
        except Exception:
            captured["answer"] = ""

        try:
            usage: CompletionUsage = response.usage
            captured["usage"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        except Exception:
            captured["usage"] = {}

        try:
            tool_calls = response.choices[0].message.tool_calls
            captured["tool_calls"] = (
                [
                    ToolCall(
                        id=tool_call.id,
                        type=tool_call.type,
                        function=FunctionCall(
                            arguments=tool_call.function.arguments,
                            name=tool_call.function.name,
                        ),
                    )
                    for tool_call in tool_calls
                ]
                if tool_calls
                else []
            )
        except Exception:
            captured["tool_calls"] = []

        try:
            captured["params"] = {
                "temperature": kwargs.get("temperature"),
                "max_tokens": kwargs.get("max_tokens"),
                "top_p": kwargs.get("top_p"),
                "n": kwargs.get("n"),
                "stop": kwargs.get("stop"),
                "frequency_penalty": kwargs.get("frequency_penalty"),
                "presence_penalty": kwargs.get("presence_penalty"),
            }
        except Exception:
            captured["params"] = None

        return response

    return interceptor


def metric_chat_create(
    message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
) -> Callable[..., ChatCompletion]:
    if not isinstance(message, str):
        message = "observerai.openai.chat_create"

    if metadata is not None and not isinstance(metadata, dict):
        metadata = None

    def decorator(func: Callable[..., ChatCompletion]) -> Callable[..., ChatCompletion]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> ChatCompletion:
            if openai is None:
                logger.error(
                    "observerai: missing optional dependency 'openai'. "
                    "Install it with: pip install observerai[openai]"
                )
                return None

            start_time = time.time()
            captured: Dict[str, Any] = {}

            try:
                with patch.object(
                    Completions,
                    "create",
                    new=intercept_openai_chat_completion(captured, Completions.create),
                ):
                    result = func(*args, **kwargs)

                latency = int((time.time() - start_time) * 1000)
                usage_data = captured.get("usage", {})
                params = captured.get("params", {})
                parameters = Parameters(
                    temperature=params.get("temperature"),
                    max_tokens=params.get("max_tokens"),
                    top_p=params.get("top_p"),
                    n=params.get("n"),
                    stop=params.get("stop"),
                    frequency_penalty=params.get("frequency_penalty"),
                    presence_penalty=params.get("presence_penalty"),
                )

                metric = ModelMetric(
                    trace_id=get_trace_id(),
                    span_id=get_span_id(),
                    flow_id=get_flow_id(),
                    name=captured.get("model", "unknown"),
                    provider="openai",
                    endpoint="/chat/completions",
                    conversation=ConversationMetric(
                        question=UserMessage(
                            content=captured.get("prompt", ""),
                            tools=captured.get("tools", []),
                        ),
                        answer=AssistantMessage(
                            content=captured.get("answer", ""),
                            tool_calls=captured.get("tool_calls", []),
                        ),
                    ),
                    parameters=parameters,
                    token_usage=TokenUsageMetric(
                        prompt=usage_data.get("prompt_tokens", 0),
                        completion=usage_data.get("completion_tokens", 0),
                        total=usage_data.get("total_tokens", 0),
                    ),
                    response=ResponseMetric(
                        status_code=200, latency=LatencyMetric(time=latency)
                    ),
                    evaluation=None,
                    metadata=metadata,
                )

            except Exception as e:
                latency = int((time.time() - start_time) * 1000)
                if hasattr(e, "status_code"):
                    status_code = e.status_code
                elif hasattr(e, "http_status"):
                    status_code = e.http_status
                else:
                    status_code = 500

                metric = ModelMetric(
                    trace_id=get_trace_id(),
                    span_id=get_span_id(),
                    flow_id=get_flow_id(),
                    name=captured.get("model", "unknown"),
                    provider="openai",
                    endpoint="/chat/completions",
                    parameters=parameters,
                    response=ResponseMetric(
                        status_code=status_code, latency=LatencyMetric(time=latency)
                    ),
                    exception=ExceptionMetric(
                        type=type(e).__name__,
                        message=str(e),
                        traceback=traceback.format_exc(),
                    ),
                    metadata=metadata,
                )

                logger.info(message, **metric.model_dump())
                return None

            logger.info(message, **metric.model_dump())
            return result

        return wrapper

    return decorator
