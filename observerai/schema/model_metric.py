from pydantic import BaseModel
from typing import Optional
from observerai.schema.metric import Metric
from observerai.schema.eval_metric import EvaluationMetric


class TokenUsageMetric(BaseModel):
    prompt: int
    completion: int
    total: int


class ConversationMetric(BaseModel):
    question: str
    answer: str


class ModelMetric(Metric):
    name: str
    provider: str
    endpoint: str
    conversation: Optional[ConversationMetric] = None
    token: Optional[TokenUsageMetric] = None
    evaluation: Optional[EvaluationMetric] = None
