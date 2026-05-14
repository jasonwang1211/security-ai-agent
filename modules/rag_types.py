from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

RAGIntent = Literal[
    "report_question",
    "evidence_question",
    "finding_question",
    "rule_question",
    "attack_knowledge",
    "incident_response",
    "false_positive_question",
    "unknown",
]
RAGConfidence = Literal["LOW", "MEDIUM", "HIGH"]
CitationKind = Literal[
    "knowledge_doc",
    "detection_rule",
    "incident_evidence",
    "incident_finding",
    "mitre_technique",
]
IDKind = Literal[
    "evidence_id",
    "finding_id",
    "incident_id",
    "rule_id",
    "mitre_technique_id",
]


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _remove_blank_strings(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def _normalize_upper_ids(values: list[str]) -> list[str]:
    return [value.upper() for value in _remove_blank_strings(values)]


class SourceCitation(BaseModel):
    source: str
    kind: CitationKind
    heading: str | None = None
    identifier: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source")
    @classmethod
    def source_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "source")

    @field_validator("heading", "identifier")
    @classmethod
    def optional_text_must_not_be_empty(cls, value: str | None) -> str | None:
        if value is not None:
            return _require_non_blank(value, "optional text")
        return value


class ExtractedId(BaseModel):
    value: str
    kind: IDKind
    normalized: str

    @field_validator("value")
    @classmethod
    def value_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "value")

    @field_validator("normalized")
    @classmethod
    def normalized_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "normalized").strip()

    @model_validator(mode="after")
    def normalize_operational_ids(self) -> "ExtractedId":
        if self.kind != "incident_id":
            self.normalized = self.normalized.upper()
        return self


class ExtractedIds(BaseModel):
    items: list[ExtractedId] = Field(default_factory=list)

    def values_by_kind(self, kind: IDKind) -> list[str]:
        seen: set[str] = set()
        values: list[str] = []
        for item in self.items:
            if item.kind == kind and item.normalized not in seen:
                values.append(item.normalized)
                seen.add(item.normalized)
        return values

    def has_any(self) -> bool:
        return bool(self.items)


class RAGIntentDecision(BaseModel):
    intent: RAGIntent
    confidence: RAGConfidence
    reason: str
    requires_context: bool = False

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "reason")

    @model_validator(mode="after")
    def unknown_intent_requires_low_confidence(self) -> "RAGIntentDecision":
        if self.intent == "unknown" and self.confidence != "LOW":
            raise ValueError("unknown intent requires LOW confidence")
        return self


class RAGRetrievalPlan(BaseModel):
    intent: RAGIntent
    query: str
    metadata_filters: dict[str, Any] = Field(default_factory=dict)
    exact_ids: ExtractedIds = Field(default_factory=ExtractedIds)
    preferred_doc_types: list[str] = Field(default_factory=list)
    use_vector_search: bool = True
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "query")


class AnswerWithSources(BaseModel):
    """RAG answer envelope. confidence is answer support, not a security verdict."""

    answer: str
    sources: list[SourceCitation]
    evidence_ids: list[str] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    confidence: RAGConfidence
    limitations: list[str] = Field(default_factory=list)

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "answer")

    @field_validator("sources")
    @classmethod
    def sources_must_not_be_empty(cls, value: list[SourceCitation]) -> list[SourceCitation]:
        if not value:
            raise ValueError("sources must not be empty")
        return value

    @field_validator("evidence_ids", "finding_ids", "rule_ids")
    @classmethod
    def ids_should_be_uppercase_without_blanks(cls, value: list[str]) -> list[str]:
        return _normalize_upper_ids(value)

    @field_validator("limitations")
    @classmethod
    def limitations_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return _remove_blank_strings(value)


def make_insufficient_answer(
    message: str,
    source: SourceCitation | None = None,
) -> AnswerWithSources:
    citation = source or SourceCitation(source="insufficient_information", kind="knowledge_doc")
    return AnswerWithSources(
        answer=message,
        sources=[citation],
        confidence="LOW",
        limitations=["Information is insufficient from available sources."],
    )
