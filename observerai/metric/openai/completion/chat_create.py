
import time
import traceback
from functools import wraps
from typing import Callable, Any, Dict, Optional
from unittest.mock import patch

from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.completion_usage import CompletionUsage
from openai.resources.chat.completions import Completions

from observerai.schema.metric import ResponseMetric, LatencyMetric, ExceptionMetric
from observerai.schema.model_metric import (
    ModelMetric,
    ConversationMetric,
    TokenUsageMetric,
)
from observerai.context.trace_context import get_trace_id, get_span_id, get_flow_id
from observerai.driver.log_driver import LogDriver

MESSAGE = "observerai.openai.chat_create"
logger = LogDriver().get_logger()

try:
    import openai
except ImportError:
    openai = None


def intercept_openai_chat_completion(
    captured: Dict[str, Any], original_create: Callable
) -> Callable[..., ChatCompletion]:
    def interceptor(self, *args, **kwargs) -> ChatCompletion:
        print("✅ Interceptor ativado")
        captured["model"] = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        captured["prompt"] = messages[-1]["content"] if messages else ""

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

        return response

    return interceptor


def metric_chat_create(metadata: Optional[Dict[str, Any]] = None) -> Callable[..., ChatCompletion]:
    if metadata is not None and not isinstance(metadata, dict):
        metadata = None

    def decorator(func: Callable[..., ChatCompletion]) -> Callable[..., ChatCompletion]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> ChatCompletion:
            if openai is None:
                raise ImportError(
                    "observerai: missing optional dependency 'openai'. "
                    "Install it with: pip install observerai[openai]"
                )

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

                metric = ModelMetric(
                    trace_id=get_trace_id(),
                    span_id=get_span_id(),
                    flow_id=get_flow_id(),
                    name=captured.get("model", "unknown"),
                    provider="openai",
                    endpoint="/chat/completions",
                    response=ResponseMetric(
                        status_code=200, latency=LatencyMetric(time=latency)
                    ),
                    conversation=ConversationMetric(
                        question=captured.get("prompt", ""),
                        answer=captured.get("answer", ""),
                    ),
                    token=TokenUsageMetric(
                        prompt=usage_data.get("prompt_tokens", 0),
                        completion=usage_data.get("completion_tokens", 0),
                        total=usage_data.get("total_tokens", 0),
                    ),
                    evaluation=None,
                    metadata=metadata,
                )

            except Exception as e:
                latency = int((time.time() - start_time) * 1000)
                metric = ModelMetric(
                    trace_id=get_trace_id(),
                    span_id=get_span_id(),
                    flow_id=get_flow_id(),
                    name="unknown",
                    provider="openai",
                    endpoint="/chat/completions",
                    response=ResponseMetric(
                        status_code=500, latency=LatencyMetric(time=latency)
                    ),
                    exception=ExceptionMetric(
                        type=type(e).__name__,
                        message=str(e),
                        traceback=traceback.format_exc(),
                    ),
                    metadata=metadata,
                )
                logger.info(MESSAGE, **metric.model_dump())
                raise

            logger.info(MESSAGE, **metric.model_dump())
            return result

        return wrapper

    return decorator
