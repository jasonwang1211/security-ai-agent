from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

InputKind = Literal[
    "payload_or_event",
    "raw_log_line",
    "log_file_path",
    "security_knowledge_question",
    "report_followup",
    "unknown",
]
RouterConfidence = Literal["LOW", "MEDIUM", "HIGH"]
ControllerStatus = Literal["ok", "error", "clarification_required"]
ToolSafetyLevel = Literal[
    "safe_local_analysis",
    "advisory_explanation",
    "export_only",
]


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class ControllerInput(BaseModel):
    raw_text: str
    context: dict[str, Any] = Field(default_factory=dict)
    last_incident_id: str | None = None

    @field_validator("raw_text")
    @classmethod
    def raw_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "raw_text")


class RouterDecision(BaseModel):
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
    raw_text: str

    @field_validator("raw_text")
    @classmethod
    def raw_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "raw_text")


class RawLogInput(BaseModel):
    raw_log: str

    @field_validator("raw_log")
    @classmethod
    def raw_log_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "raw_log")


class LogFileInput(BaseModel):
    path: str

    @field_validator("path")
    @classmethod
    def path_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "path")


class KnowledgeQuestionInput(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "question")


class ReportFollowupInput(BaseModel):
    question: str
    last_incident_id: str | None = None

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "question")


class ToolExecutionResult(BaseModel):
    status: ControllerStatus
    output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None


class RouteExplanation(BaseModel):
    input_kind: InputKind
    selected_tool: str | None = None
    reason: str
    confidence: RouterConfidence

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "reason")


class ControllerOutput(BaseModel):
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
