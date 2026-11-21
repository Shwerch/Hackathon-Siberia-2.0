from __future__ import annotations

from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field


SessionStatus = Literal[
    "needs_clarification",
    "preliminary",
    "completed",
    "unsupported",
]
UsageStatus = Literal["confirmed", "partial", "unknown"]


class SourceRef(BaseModel):
    file: str
    section: str


class QuestionOption(BaseModel):
    id: str
    label: str


class ClarificationQuestion(BaseModel):
    question_id: str
    text: str
    multi_select: bool = False
    options: list[QuestionOption]
    allow_unknown: bool = True
    unknown_label: str = "Не знаю"
    allow_other: bool = True
    other_label: str = "Другое"


class QuestionAnswerPayload(BaseModel):
    question_id: str
    selected_options: list[str] = Field(default_factory=list)
    is_unknown: bool = False
    other_text: Optional[str] = None


class NetworkNode(BaseModel):
    id: str
    name: str
    trust: Literal["open", "closed"]


class FileProtocolSide(BaseModel):
    open: str
    closed: str


class RuleItem(BaseModel):
    id: int
    type: Literal["data", "file"]
    from_net: str = Field(alias="from")
    to_net: str = Field(alias="to")
    mode: Literal["one-way", "two-way"]
    protocol: Union[str, FileProtocolSide]
    port: Optional[int] = None
    checks: list[str] = Field(default_factory=list)
    checks_by_node: Optional[dict[str, list[str]]] = None
    description: str
    rationale: Optional[str] = None

    model_config = {"populate_by_name": True}


class FileUsersRange(BaseModel):
    min: int
    max: Optional[int] = None


class SystemDevice(BaseModel):
    name: str
    network: Literal["open", "closed"]
    role: str = ""


class ProjectResult(BaseModel):
    has_diagram: bool = False
    status_label: str = "Требуются уточнения"
    explanation: str = ""
    networks: list[NetworkNode] = Field(default_factory=list)
    firewall: dict[str, str] = Field(default_factory=lambda: {"side": "open"})
    synonyx: dict[str, str] = Field(
        default_factory=lambda: {
            "location": "closed",
            "node_a_faces": "open",
            "node_b_faces": "closed",
        }
    )
    rules: list[RuleItem] = Field(default_factory=list)
    rules_count: int = 0
    file_users_count: Optional[int] = 0
    file_users_range: Optional[FileUsersRange] = None
    checks_by_node: Optional[dict[str, Any]] = None
    devices: list[SystemDevice] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    requests_for_vendor: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    diagram_drawio_xml: Optional[str] = None


class ModelBreakdownItem(BaseModel):
    model_id: str
    provider: str
    calls_count: int
    input_tokens: int
    output_tokens: int
    cost_input_usd: Optional[float]
    cost_output_usd: Optional[float]
    cost_total_usd: Optional[float]


class TelemetryInfo(BaseModel):
    turn_timing_ms: Optional[int] = None
    usage_status: UsageStatus = "confirmed"
    total_cost_usd: Optional[float] = 0.0
    provider_actual_cost_usd: Optional[float] = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    models_breakdown: list[ModelBreakdownItem] = Field(default_factory=list)


class ChatMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    text: str
    sources: list[SourceRef] = Field(default_factory=list)
    clarification_questions: list[ClarificationQuestion] = Field(default_factory=list)
    timestamp: str


class CreateSessionResponse(BaseModel):
    session_id: str
    status: SessionStatus
    welcome_message: str
    example_prompt: str
    telemetry: TelemetryInfo


class SendMessageRequest(BaseModel):
    client_request_id: str
    text: str = ""
    answers: list[QuestionAnswerPayload] = Field(default_factory=list)


class AssistantMessageOut(BaseModel):
    text: str
    sources: list[SourceRef] = Field(default_factory=list)
    clarification_questions: list[ClarificationQuestion] = Field(default_factory=list)


class MessageResponse(BaseModel):
    session_id: str
    turn_id: int
    status: SessionStatus
    assistant_message: AssistantMessageOut
    result: Optional[ProjectResult] = None
    telemetry: TelemetryInfo


class SessionStateResponse(BaseModel):
    session_id: str
    status: SessionStatus
    welcome_message: str
    example_prompt: str
    messages: list[ChatMessage]
    result: Optional[ProjectResult] = None
    telemetry: TelemetryInfo
