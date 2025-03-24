from contextvars import ContextVar
from typing import Optional
import uuid

# Context vars for isolated trace/span by thread/async
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
flow_id_var: ContextVar[Optional[str]] = ContextVar("flow_id", default=None)


def _generate_trace_id() -> str:
    """Generate a new trace ID with prefix."""
    return str(uuid.uuid4())


def set_ids(
    trace_id: str, span_id: Optional[str] = None, flow_id: Optional[str] = None
):
    """
    Set the trace_id and (optionally) span_id for the current context.
    These values will be automatically retrieved by the observerai decorators.
    """
    trace_id_var.set(trace_id)
    if span_id:
        span_id_var.set(span_id)
    if flow_id:
        flow_id_var.set(flow_id)


def get_trace_id() -> str | None:
    """Retrieve the trace_id from the context or generate a new one with prefix."""
    return trace_id_var.get() or None


def get_span_id() -> str | None:
    """Retrieve the span_id from the context or generate a new UUID."""
    return span_id_var.get() or None


def get_flow_id() -> str | None:
    """Retrieve the flow_id from the context or generate a new UUID."""
    return flow_id_var.get() or None
