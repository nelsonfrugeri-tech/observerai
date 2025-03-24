from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime, timezone


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
    # trace_id: Optional[str] = None
    # flow_id: Optional[str] = None
    # span_id: Optional[str] = None
    response: Optional[ResponseMetric] = None
    exception: Optional[ExceptionMetric] = None
    version: str = "0.0.1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, str]] = None
