from typing import Optional
from observerai.schema.metric import Metric


class VectorStoreMetric(Metric):
    name: str
    index: Optional[str] = None
    retrieved_documents: Optional[int] = None
