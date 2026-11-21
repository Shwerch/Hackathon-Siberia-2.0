from typing import Literal, Optional
from pydantic import BaseModel, Field


class CallLogEntry(BaseModel):
    session_id: str
    turn_id: int
    call_id: str
    model_id: str
    openrouter_model_id: str
    provider: str
    purpose: Literal["extract_intent", "generate_reply", "kb_index"]
    started_at: str
    finished_at: str
    duration_ms: float
    status: Literal["ok", "error", "timeout"]
    provider_response_id: Optional[str] = None
    usage_status: Literal["confirmed", "unknown"] = "confirmed"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    input_price_per_1m: float
    output_price_per_1m: float
    evaluation_input_cost_usd: Optional[float] = None
    evaluation_output_cost_usd: Optional[float] = None
    evaluation_cost_usd: Optional[float] = None
    actual_cost_usd: Optional[float] = None
    error_message: Optional[str] = None


class TurnTiming(BaseModel):
    turn_id: int
    duration_seconds: float
    status: Literal["ok", "error"]


class UsageSummary(BaseModel):
    status: Literal["measured", "partial_unknown", "not_measured"] = "measured"
    input_tokens: int = 0
    output_tokens: int = 0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    evaluation_cost_usd: float = 0.0
    actual_cost_usd: Optional[float] = None
    calls: list[CallLogEntry] = Field(default_factory=list)


class TimingSummary(BaseModel):
    turns: list[TurnTiming] = Field(default_factory=list)
    mean_turn_seconds: Optional[float] = None
