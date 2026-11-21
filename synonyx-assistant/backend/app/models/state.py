from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from app.models.usage import TimingSummary, UsageSummary


class NetworkItem(BaseModel):
    id: Literal["open", "closed"]
    name: str
    trust: Literal["open", "closed"]


class DeviceItem(BaseModel):
    id: str
    network_id: Literal["open", "closed"]
    name: str
    role_hint: str = ""


class FlowDraft(BaseModel):
    """Промежуточное описание потока, извлечённое из диалога."""
    flow_key: str
    type: Literal["data", "file", "unknown"] = "unknown"
    from_network: Optional[Literal["open", "closed"]] = None
    to_network: Optional[Literal["open", "closed"]] = None
    source_devices: list[str] = Field(default_factory=list)
    target_devices: list[str] = Field(default_factory=list)
    mode: Optional[Literal["one-way", "two-way"]] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    description: str = ""
    send_method: Optional[Literal["manual", "pull", "usb"]] = None
    send_protocol: Optional[Literal["SFTP", "FTP", "SMB", "USB"]] = None
    receive_method: Optional[Literal["manual", "push", "usb"]] = None
    receive_protocol: Optional[Literal["SFTP", "FTP", "SMB", "USB"]] = None
    checks_send: list[str] = Field(default_factory=list)
    checks_receive: list[str] = Field(default_factory=list)
    isolate_groups: Optional[bool] = None
    access_groups_count: int = 1
    manual_users_count: Optional[int] = None
    manual_users_range: Optional[dict[str, Optional[int]]] = None
    is_ntp: bool = False


class RuleItem(BaseModel):
    id: int
    type: Literal["data", "file"]
    from_net: Literal["open", "closed"] = Field(alias="from")
    to_net: Literal["open", "closed"] = Field(alias="to")
    mode: Literal["one-way", "two-way"]
    protocol: Any
    port: Optional[int] = None
    description: str
    checks: list[str] = Field(default_factory=list)
    checks_by_node: Optional[dict[str, list[str]]] = None
    source_devices: list[str] = Field(default_factory=list)
    target_device: Optional[str] = None
    uses_usb: bool = False

    model_config = {"populate_by_name": True}


class ClarifyOption(BaseModel):
    id: str
    label: str


class ClarifyQuestion(BaseModel):
    question_id: str
    flow_key: Optional[str] = None
    field: str
    text: str
    options: list[ClarifyOption]
    allow_unknown: bool = True
    allow_other: bool = True


class SourceRef(BaseModel):
    file: str
    section: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    turn_id: int
    questions: list[ClarifyQuestion] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)


class SessionState(BaseModel):
    schema_version: str = "1.1"
    session_id: str
    turn_counter: int = 0
    status: Literal["needs_clarification", "preliminary", "completed", "unsupported"] = "needs_clarification"
    networks: list[NetworkItem] = Field(default_factory=list)
    both_initially_open: bool = False
    firewall_side: Literal["open", "both"] = "open"
    devices: list[DeviceItem] = Field(default_factory=list)
    flows: list[FlowDraft] = Field(default_factory=list)
    rules: list[RuleItem] = Field(default_factory=list)
    rules_count: int = 0
    file_users_count: Optional[int] = 0
    file_users_range: Optional[dict[str, Optional[int]]] = None
    unknowns: list[str] = Field(default_factory=list)
    dismissed_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    requests_for_vendor: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    messages: list[ChatMessage] = Field(default_factory=list)
    pending_questions: list[ClarifyQuestion] = Field(default_factory=list)
    last_explanation: str = ""
    drawio_xml: str = ""
    usage: UsageSummary = Field(default_factory=UsageSummary)
    timing: TimingSummary = Field(default_factory=TimingSummary)


class TurnRequest(BaseModel):
    message: str
    clarification_answers: dict[str, dict[str, Any]] = Field(default_factory=dict)
