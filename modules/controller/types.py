"""Typed controller contracts for deterministic helper dispatch."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

InputKind = Literal[
    "payload_or_event",
    "raw_log_line",
    "log_file_path",
    "security_knowledge_question",
    "report_followup",
    "case_draft_request",
    "unknown",
]
RouterConfidence = Literal["LOW", "MEDIUM", "HIGH"]
ControllerStatus = Literal["ok", "error", "clarification_required"]
ToolSafetyLevel = Literal[
    "safe_local_analysis",
    "advisory_explanation",
    "draft_write_review_required",
    "export_only",
]
CaseDraftAction = Literal["request", "approve", "cancel"]


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class ControllerInput(BaseModel):
    """Raw controller request plus optional local context."""

    raw_text: str
    context: dict[str, Any] = Field(default_factory=dict)
    last_incident_id: str | None = None

    @field_validator("raw_text")
    @classmethod
    def raw_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "raw_text")


class RouterDecision(BaseModel):
    """Deterministic route decision; unknown input must request clarification."""

    input_kind: InputKind
    selected_tool: str | None = None
    confidence: RouterConfidence
    reason: str
    requires_clarification: bool = False

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "reason")

    @model_validator(mode="after")
    def unknown_input_requires_clarification(self) -> "RouterDecision":
        if self.input_kind == "unknown":
            if self.selected_tool is not None:
                raise ValueError("unknown input must not select a tool")
            if not self.requires_clarification:
                raise ValueError("unknown input requires clarification")
        return self


class PayloadTriageInput(BaseModel):
    """Input for deterministic payload or event triage."""

    raw_text: str

    @field_validator("raw_text")
    @classmethod
    def raw_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "raw_text")


class RawLogInput(BaseModel):
    """Input for translating one raw log line."""

    raw_log: str

    @field_validator("raw_log")
    @classmethod
    def raw_log_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "raw_log")


class LogFileInput(BaseModel):
    """Input for local log file ingestion."""

    path: str

    @field_validator("path")
    @classmethod
    def path_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "path")


class KnowledgeQuestionInput(BaseModel):
    """Input for advisory security knowledge Q&A."""

    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "question")


class ReportFollowupInput(BaseModel):
    """Input for report-aware follow-up over existing context."""

    question: str
    last_incident_id: str | None = None

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "question")


class CaseDraftInput(BaseModel):
    """Input for approval-gated local case draft capture."""

    model_config = ConfigDict(extra="forbid")

    action: CaseDraftAction
    user_text: str

    @field_validator("user_text")
    @classmethod
    def user_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "user_text")


class IncidentJsonExportInput(BaseModel):
    """Input for export-only incident JSON handling."""

    incident_id: str | None = None
    incident: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def incident_id_or_incident_required(self) -> "IncidentJsonExportInput":
        if self.incident_id is None and not self.incident:
            raise ValueError("incident_id or incident must be provided")
        return self


class ToolExecutionResult(BaseModel):
    """Normalized result returned by controller skill wrappers."""

    status: ControllerStatus
    output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None


class RouteExplanation(BaseModel):
    """Human-readable route explanation for controller output."""

    input_kind: InputKind
    selected_tool: str | None = None
    reason: str
    confidence: RouterConfidence

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "reason")


class ControllerOutput(BaseModel):
    """Controller response envelope with route and structured result details."""

    status: ControllerStatus
    selected_tool: str | None = None
    response_text: str
    structured_result: dict[str, Any] = Field(default_factory=dict)
    route: RouterDecision
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def response_text_required_unless_error(self) -> "ControllerOutput":
        if self.status != "error" and not self.response_text.strip():
            raise ValueError("response_text must not be empty unless status is error")
        return self


class ToolSpec(BaseModel):
    """Typed tool registration contract for explicit controller dispatch."""

    name: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    safety_level: ToolSafetyLevel
    requires_llm: bool = False
    requires_rag: bool = False
    deterministic: bool = True
    allowed_input_kinds: list[InputKind] = Field(default_factory=list)
    notes: str = ""

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "name")

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "description")

    @field_validator("allowed_input_kinds")
    @classmethod
    def allowed_input_kinds_must_not_be_empty(cls, value: list[InputKind]) -> list[InputKind]:
        if not value:
            raise ValueError("allowed_input_kinds must not be empty")
        return value
