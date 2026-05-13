from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
Decision = Literal["ALLOW", "MONITOR", "BLOCK"]
DetectorStatus = Literal["ALERT", "CLEAN", "REVIEW", "SUSPICIOUS"]
LLMConfidence = Literal["very_low", "low", "medium", "high", "very_high"]


class DetectorResultModel(BaseModel):
    status: str
    attack_types: list[str] = Field(default_factory=list)
    matched_signatures: dict[str, list[str]] = Field(default_factory=dict)
    original_input: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskResultModel(BaseModel):
    risk_level: RiskLevel
    reason: str = ""


class DecisionResultModel(BaseModel):
    decision: Decision
    reason: str = ""


class DefenseResultModel(BaseModel):
    action: str = ""
    status: str = ""
    summary: str = ""
    attack_types: list[str] = Field(default_factory=list)
    risk_level: str = ""


class LLMSuspiciousResultModel(BaseModel):
    is_suspicious: bool = False
    suggested_attack_types: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    anomaly_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    recommended_risk: RiskLevel = "LOW"
    recommended_action: Decision = "ALLOW"
    llm_status: str = "FALLBACK"


class LLMAlertExplanationResultModel(BaseModel):
    is_suspicious: bool = False
    possible_attack_types: list[str] = Field(default_factory=list)
    reasoning: str = ""
    recommended_decision: Decision = "ALLOW"
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)


class SecurityEventModel(BaseModel):
    event_type: str
    source_ip: str | None = None
    target: str | None = None
    user: str | None = None
    timestamp: str | None = None
    raw: str = ""


class AggregatedEventModel(BaseModel):
    event_type: str
    source_ip: str | None = None
    target: str | None = None
    user: str | None = None
    failed_count: int = 0
    evidence: str = ""
    raw_events: list[dict] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: str
    type: str
    description: str
    value: Any | None = None
    source_event_ids: list[str] = Field(default_factory=list)
    confidence: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_must_be_stable_evidence_id(cls, value: str) -> str:
        if not value.startswith("EV-"):
            raise ValueError("evidence id must start with EV-")
        return value

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description must not be empty")
        return value


class EvidenceBundle(BaseModel):
    incident_id: str | None = None
    items: list[EvidenceItem] = Field(default_factory=list)

    @property
    def available_ids(self) -> set[str]:
        return {item.id for item in self.items}

    def get(self, evidence_id: str) -> EvidenceItem | None:
        return next((item for item in self.items if item.id == evidence_id), None)


class Finding(BaseModel):
    id: str
    finding_type: str
    title: str
    status: DetectorStatus
    risk_level: RiskLevel
    decision: Decision
    attack_type: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    explain_topics: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_must_be_stable_finding_id(cls, value: str) -> str:
        if not value.startswith("F-"):
            raise ValueError("finding id must start with F-")
        return value

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def evidence_ids_must_be_stable_ids(cls, value: list[str]) -> list[str]:
        invalid_ids = [evidence_id for evidence_id in value if not evidence_id.startswith("EV-")]
        if invalid_ids:
            raise ValueError("evidence ids must start with EV-")
        return value


class GenerationMetadata(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    app_version: str = "v1.3"
    detector_rules_version: str = "python-signatures"
    triage_policy_version: str = "v1.3"
    kb_revision: str | None = None
    llm_model: str | None = None
    embedding_model: str | None = None
    source: str = "security-ai-agent"


class Incident(BaseModel):
    id: str
    title: str
    status: DetectorStatus
    risk_level: RiskLevel
    decision: Decision
    attack_type: str | None = None
    findings: list[Finding]
    evidence_bundle: EvidenceBundle
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    recommended_response: list[str] = Field(default_factory=list)
    simulation_notice: str = "This is a simulated training decision, not an enforcement action."
    generated_with: GenerationMetadata = Field(default_factory=GenerationMetadata)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def id_must_be_stable_incident_id(cls, value: str) -> str:
        if not value.startswith("INC-"):
            raise ValueError("incident id must start with INC-")
        return value

    @field_validator("title")
    @classmethod
    def incident_title_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value

    @field_validator("findings")
    @classmethod
    def findings_should_not_be_empty(cls, value: list[Finding]) -> list[Finding]:
        if not value:
            raise ValueError("incident must include at least one finding")
        return value

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class LLMAssessment(BaseModel):
    is_suspicious: bool
    possible_attack_types: list[str] = Field(default_factory=list)
    confidence: LLMConfidence
    reasoning: str
    recommended_risk: RiskLevel
    recommended_action: Decision
    evidence_references: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reasoning")
    @classmethod
    def reasoning_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reasoning must not be empty")
        return value

    @field_validator("evidence_references")
    @classmethod
    def evidence_references_must_be_stable_ids(cls, value: list[str]) -> list[str]:
        invalid_ids = [evidence_id for evidence_id in value if not evidence_id.startswith("EV-")]
        if invalid_ids:
            raise ValueError("evidence references must start with EV-")
        return value

    @model_validator(mode="after")
    def suspicious_assessment_requires_evidence(self) -> "LLMAssessment":
        if self.is_suspicious and not self.evidence_references:
            raise ValueError("suspicious assessment requires evidence references")
        return self
