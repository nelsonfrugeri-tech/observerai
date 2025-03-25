from typing import List, Optional, Union, Literal, Dict
from pydantic import BaseModel
from observerai.schema.metric import Metric
from observerai.schema.eval_metric import EvaluationMetric


# --- Tool definitions (sent by the user) ---


class ToolFunction(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict  # JSON Schema (livre)


class Tool(BaseModel):
    type: Literal["function"]
    function: ToolFunction


# --- Tool call (returned by the model) ---


class FunctionCall(BaseModel):
    name: str
    arguments: str  # JSON string


class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: FunctionCall


# --- Chat messages ---


class UserMessage(BaseModel):
    content: Optional[str] = None
    role: Literal["user"] = "user"
    tools: Optional[List[Tool]] = None  # available tools


class AssistantMessage(BaseModel):
    content: Optional[str] = None
    role: Literal["assistant"] = "assistant"
    tool_calls: Optional[List[ToolCall]] = None


# --- Conversation structure ---


class ConversationMetric(BaseModel):
    question: Optional[UserMessage] = None
    answer: Optional[AssistantMessage] = None


# --- Other data ---


class TokenUsageMetric(BaseModel):
    prompt: int
    completion: int
    total: int


class Parameters(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None


# --- Main model ---


class ModelMetric(Metric):
    name: str
    provider: str
    endpoint: str
    conversation: Optional[ConversationMetric] = None
    parameters: Optional[Parameters] = None
    token_usage: Optional[TokenUsageMetric] = None
    evaluation: Optional[EvaluationMetric] = None
