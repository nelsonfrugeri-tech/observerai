import time
import traceback
from functools import wraps
from typing import Callable, Any, Dict
from unittest.mock import patch

from openai.resources.chat.completions import Completions

from observerai.schema.metric import ResponseMetric, LatencyMetric, ExceptionMetric
from observerai.schema.model_metric import ModelMetric, ConversationMetric, TokenUsageMetric
# from observerai.context.trace_context import get_trace_id, get_span_id, get_flow_id
from observerai.driver.log_driver import LogDriver

MESSAGE = "observerai.model_metric"
logger = LogDriver().get_logger()

try:
    import openai
except ImportError:
    openai = None


def intercept_openai_chat_completion(
    captured: Dict[str, Any], original_create: Callable
):
    def interceptor(*args, **kwargs):
        print("✅ Interceptor ativado")
        captured["model"] = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        captured["prompt"] = messages[-1]["content"] if messages else ""

        response = original_create(*args, **kwargs)
        captured["answer"] = response.choices[0].message.content
        captured["usage"] = response.usage.model_dump() if hasattr(response, "usage") else {}
        return response

    return interceptor


def openai_completion(func: Callable):
    """
    Decorator with interceptor for openai.ChatCompletion.create()
    and register structured metrics (Log as Metric) via structlog.
    Requires the optional dependency: observerai[openai]
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if openai is None:
            raise ImportError(
                "observerai: missing optional dependency 'openai'. "
                "Install it with: pip install observerai[openai]"
            )

        start_time = time.time()
        captured: Dict[str, Any] = {}

        try:
            client = kwargs.get("client")
            if client is None:
                raise ValueError("Client OpenAI not passed as keyword argument `client`.")

            original_create = client.chat.completions.create

            with patch.object(
                client.chat.completions,
                "create",
                side_effect=intercept_openai_chat_completion(captured, original_create),
            ):
                result = func(*args, **kwargs)

            latency = int((time.time() - start_time) * 1000)

            metric = ModelMetric(
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
                    prompt=captured.get("usage", {}).get("prompt_tokens", 0),
                    completion=captured.get("usage", {}).get("completion_tokens", 0),
                    total=captured.get("usage", {}).get("total_tokens", 0),
                ),
                evaluation=None,
            )

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            metric = ModelMetric(
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
            )
            logger.info(MESSAGE, **metric.model_dump())
            raise

        logger.info(MESSAGE, **metric.model_dump())
        return result

    return wrapper

