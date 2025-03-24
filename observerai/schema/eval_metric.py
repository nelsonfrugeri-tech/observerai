from typing import Optional
from observerai.schema.metric import Metric


class EvaluationMetric(Metric):
    helpfulness: Optional[float] = None
    factuality: Optional[float] = None
    relevance: Optional[float] = None
    groundedness: Optional[float] = None
