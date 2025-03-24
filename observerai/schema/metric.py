from pydantic import BaseModel, Field
from typing import Optional


class LatencyMetric(BaseModel):
    time: int
    unit: str = "ms"


class ResponseMetric(BaseModel):
    status_code: int
    latency: LatencyMetric


class ExceptionMetric(BaseModel):
    type: str
    message: str
    traceback: Optional[str] = None


class Metric(BaseModel):
    trace_id: Optional[str] = None
    flow_id: Optional[str] = None
    span_id: Optional[str] = None
    response: Optional[ResponseMetric] = None
    exception: Optional[ExceptionMetric] = None
    version: str = "0.0.1"
    metadata: Optional[dict] = None
