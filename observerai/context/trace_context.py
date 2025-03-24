from contextvars import ContextVar
from typing import Optional

# Context vars for isolated trace/span by thread/async
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
flow_id_var: ContextVar[Optional[str]] = ContextVar("flow_id", default=None)


class TraceContext:
    """
    Class to manage the trace context in operations
    The values are stored in contextvars for isolation by thread/async
    """

    @classmethod
    def set_trace_id(cls, trace_id: str) -> None:
        """Define the trace_id in the current context"""
        trace_id_var.set(trace_id)

    @classmethod
    def set_span_id(cls, span_id: str) -> None:
        """Define the span_id in the current context"""
        span_id_var.set(span_id)

    @classmethod
    def set_flow_id(cls, flow_id: str) -> None:
        """Define the flow_id in the current context"""
        flow_id_var.set(flow_id)


# Functions for internal use
def get_trace_id() -> Optional[str]:
    """Get the trace_id of the current context (internal use)"""
    return trace_id_var.get()


def get_span_id() -> Optional[str]:
    """Get the span_id of the current context (internal use)"""
    return span_id_var.get()


def get_flow_id() -> Optional[str]:
    """Get the flow_id of the current context (internal use)"""
    return flow_id_var.get()
