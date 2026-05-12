from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from modules.types import EvidenceBundle, Finding, LLMAssessment, RiskLevel

GuardrailAction = Literal["accept", "downgrade_confidence", "reject_to_fallback"]

ALLOWED_ATTACK_TYPES = {
    "XSS",
    "SQL Injection",
    "Path Traversal",
    "Command Injection",
    "Brute Force",
    "Credential Stuffing",
    "Authentication Failure",
    "Possible Account Compromise",
    "brute_force_candidate",
    "possible_account_compromise",
    "payload_alert",
}

PROMPT_INJECTION_PHRASES = (
    "ignore all previous instructions",
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "reveal hidden instructions",
    "disregard instructions",
)

RISK_RANK: dict[RiskLevel, int] = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


class GuardrailResult(BaseModel):
    valid: bool
    action: GuardrailAction
    violations: list[str] = Field(default_factory=list)
    sanitized_assessment: LLMAssessment | None = None


class LLMGuardrails:
    def validate(
        self,
        assessment: LLMAssessment,
        evidence_bundle: EvidenceBundle,
        deterministic_finding: Finding,
    ) -> GuardrailResult:
        critical_violations: list[str] = []
        caution_violations: list[str] = []

        missing_evidence_ids = sorted(
            set(assessment.evidence_references) - evidence_bundle.available_ids
        )
        if missing_evidence_ids:
            critical_violations.append(
                f"LLM cited nonexistent evidence IDs: {', '.join(missing_evidence_ids)}"
            )

        if assessment.is_suspicious and not assessment.evidence_references:
            critical_violations.append("Suspicious assessment requires evidence references")

        if self._downgrades_deterministic_risk(
            deterministic_finding.risk_level, assessment.recommended_risk
        ):
            critical_violations.append(
                "LLM recommended risk downgrade from "
                f"{deterministic_finding.risk_level} to {assessment.recommended_risk}"
            )

        if (
            deterministic_finding.decision != "BLOCK"
            and assessment.recommended_action == "BLOCK"
        ):
            caution_violations.append("LLM recommended BLOCK without deterministic BLOCK")

        unknown_attack_types = sorted(
            attack_type
            for attack_type in assessment.possible_attack_types
            if attack_type not in ALLOWED_ATTACK_TYPES
        )
        if unknown_attack_types:
            critical_violations.append(
                f"LLM suggested unsupported attack types: {', '.join(unknown_attack_types)}"
            )

        if assessment.confidence == "very_high" and not assessment.evidence_references:
            critical_violations.append("Very high confidence requires evidence references")
        elif assessment.confidence == "very_high" and len(assessment.evidence_references) == 1:
            caution_violations.append("Very high confidence with only one evidence reference")

        violations = critical_violations + caution_violations
        sanitized_assessment = assessment.model_copy(
            update={"violations": [*assessment.violations, *violations]}
        )

        if critical_violations:
            return GuardrailResult(
                valid=False,
                action="reject_to_fallback",
                violations=violations,
                sanitized_assessment=sanitized_assessment,
            )

        if caution_violations:
            return GuardrailResult(
                valid=True,
                action="downgrade_confidence",
                violations=violations,
                sanitized_assessment=sanitized_assessment,
            )

        return GuardrailResult(
            valid=True,
            action="accept",
            violations=[],
            sanitized_assessment=sanitized_assessment,
        )

    @staticmethod
    def _downgrades_deterministic_risk(
        deterministic_risk: RiskLevel,
        llm_recommended_risk: RiskLevel,
    ) -> bool:
        return RISK_RANK[llm_recommended_risk] < RISK_RANK[deterministic_risk]


def sanitize_for_llm(value: str, max_length: int = 256) -> str:
    sanitized = re.sub(r"[\n\r\t]+", " ", value).strip()
    for phrase in PROMPT_INJECTION_PHRASES:
        sanitized = re.sub(re.escape(phrase), "[redacted]", sanitized, flags=re.IGNORECASE)
    return sanitized[:max_length]


def sanitize_evidence_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: sanitize_for_llm(value) if isinstance(value, str) else value
        for key, value in metadata.items()
    }


def write_llm_audit_log(
    path: str | Path,
    assessment: LLMAssessment,
    result: GuardrailResult,
    finding: Finding,
    evidence_bundle: EvidenceBundle,
) -> None:
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "finding_id": finding.id,
        "finding_type": finding.finding_type,
        "deterministic_risk": finding.risk_level,
        "deterministic_decision": finding.decision,
        "llm_recommended_risk": assessment.recommended_risk,
        "llm_recommended_action": assessment.recommended_action,
        "llm_confidence": assessment.confidence,
        "evidence_references": assessment.evidence_references,
        "guardrail_action": result.action,
        "guardrail_valid": result.valid,
        "violations": result.violations,
        "available_evidence_ids": sorted(evidence_bundle.available_ids),
    }

    with audit_path.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(record, sort_keys=True) + "\n")


def detect_ai_disagreement(
    assessment: LLMAssessment,
    finding: Finding,
) -> tuple[bool, str | None]:
    if assessment.recommended_risk != finding.risk_level:
        return (
            True,
            "LLM suggested risk "
            f"{assessment.recommended_risk}, while deterministic risk is "
            f"{finding.risk_level}. Deterministic verdict prevails.",
        )

    if assessment.recommended_action != finding.decision:
        return (
            True,
            "LLM suggested action "
            f"{assessment.recommended_action}, while deterministic decision is "
            f"{finding.decision}. Deterministic verdict prevails.",
        )

    return False, None
