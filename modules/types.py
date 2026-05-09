from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
Decision = Literal["ALLOW", "MONITOR", "BLOCK"]
DetectorStatus = Literal["ALERT", "CLEAN", "REVIEW", "SUSPICIOUS"]


class DetectorResultModel(BaseModel):
    status: str
    attack_types: list[str] = Field(default_factory=list)
    matched_signatures: dict[str, list[str]] = Field(default_factory=dict)
    original_input: str = ""


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
