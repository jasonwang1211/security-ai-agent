import json

from modules.evidence_correlator import correlate_auth_sequence
from modules.llm_assist import (
    LLMAssist,
    build_evidence_assessment_context,
    parse_llm_assessment_json,
)
from modules.types import EvidenceBundle, Finding, Incident, LLMAssessment


def make_auth_event(event_type: str, timestamp: str) -> dict:
    return {
        "event_type": event_type,
        "source_ip": "10.0.0.5",
        "target": "/login",
        "user": "admin",
        "timestamp": timestamp,
        "raw": f"{timestamp} {event_type} src_ip=10.0.0.5 user=admin endpoint=/login",
    }


def make_incident() -> Incident:
    events = [
        make_auth_event("auth_failure", "2026-05-01T10:00:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:01:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:02:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:03:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:04:00Z"),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z"),
    ]
    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)
    assert incident is not None
    return incident


def make_context() -> tuple[EvidenceBundle, Finding]:
    incident = make_incident()
    return incident.evidence_bundle, incident.findings[0]


def make_fallback() -> LLMAssessment:
    return LLMAssessment(
        is_suspicious=True,
        possible_attack_types=["Possible Account Compromise"],
        confidence="medium",
        reasoning="Fallback advisory assessment based on deterministic finding and cited evidence.",
        recommended_risk="HIGH",
        recommended_action="MONITOR",
        evidence_references=["EV-001"],
    )


def test_build_evidence_assessment_context_includes_finding_and_evidence():
    evidence_bundle, finding = make_context()

    context = build_evidence_assessment_context(evidence_bundle, finding)

    assert context["finding_id"] == "F-001"
    assert context["finding_type"] == "possible_account_compromise"
    evidence_items = context["evidence_items"]
    assert isinstance(evidence_items, list)
    assert any(item["id"] == "EV-001" for item in evidence_items)
    assert context["constraints"]["advisory_only"] is True


def test_assess_evidence_fallback_returns_valid_llm_assessment():
    evidence_bundle, finding = make_context()

    assessment = LLMAssist().assess_evidence(evidence_bundle, finding)

    assert isinstance(assessment, LLMAssessment)
    assert assessment.metadata["advisory_only"] is True
    assert assessment.metadata["llm_status"] == "FALLBACK"
    assert assessment.recommended_risk == finding.risk_level
    assert assessment.recommended_action == finding.decision
    assert assessment.evidence_references


def test_parse_llm_assessment_json_accepts_valid_json():
    fallback = make_fallback()
    raw_output = json.dumps(
        {
            "is_suspicious": True,
            "possible_attack_types": ["Possible Account Compromise"],
            "confidence": "high",
            "reasoning": "The evidence is grounded in repeated failures followed by success.",
            "recommended_risk": "HIGH",
            "recommended_action": "MONITOR",
            "evidence_references": ["EV-001", "EV-003"],
        }
    )

    assessment = parse_llm_assessment_json(raw_output, fallback)

    assert assessment.confidence == "high"
    assert assessment.evidence_references == ["EV-001", "EV-003"]


def test_parse_llm_assessment_json_returns_fallback_on_invalid_json():
    fallback = make_fallback()

    assessment = parse_llm_assessment_json("not-json", fallback)

    assert assessment is fallback


def test_parse_llm_assessment_json_returns_fallback_on_invalid_confidence():
    fallback = make_fallback()
    raw_output = json.dumps(
        {
            "is_suspicious": True,
            "possible_attack_types": ["Possible Account Compromise"],
            "confidence": "super_high",
            "reasoning": "Invalid confidence should be rejected.",
            "recommended_risk": "HIGH",
            "recommended_action": "MONITOR",
            "evidence_references": ["EV-001"],
        }
    )

    assessment = parse_llm_assessment_json(raw_output, fallback)

    assert assessment is fallback


def test_assess_evidence_with_guardrails_accepts_grounded_matching_assessment(monkeypatch):
    evidence_bundle, finding = make_context()
    assistant = LLMAssist()

    def fake_invoke(context: dict[str, object]) -> str:
        return json.dumps(
            {
                "is_suspicious": True,
                "possible_attack_types": ["Possible Account Compromise"],
                "confidence": "high",
                "reasoning": "Grounded in EV-001 and EV-003.",
                "recommended_risk": "HIGH",
                "recommended_action": "MONITOR",
                "evidence_references": ["EV-001", "EV-003"],
            }
        )

    monkeypatch.setattr(assistant, "_invoke_llm_for_evidence", fake_invoke)

    assessment, result = assistant.assess_evidence_with_guardrails(evidence_bundle, finding)

    assert assessment.metadata == {}
    assert result.valid is True
    assert result.action == "accept"


def test_assess_evidence_with_guardrails_flags_unilateral_block(monkeypatch):
    evidence_bundle, finding = make_context()
    assistant = LLMAssist()

    def fake_invoke(context: dict[str, object]) -> str:
        return json.dumps(
            {
                "is_suspicious": True,
                "possible_attack_types": ["Possible Account Compromise"],
                "confidence": "high",
                "reasoning": "Grounded but recommends stronger advisory action.",
                "recommended_risk": "HIGH",
                "recommended_action": "BLOCK",
                "evidence_references": ["EV-001", "EV-003"],
            }
        )

    monkeypatch.setattr(assistant, "_invoke_llm_for_evidence", fake_invoke)

    assessment, result = assistant.assess_evidence_with_guardrails(evidence_bundle, finding)

    assert assessment.recommended_action == "BLOCK"
    assert finding.decision == "MONITOR"
    assert result.valid is True
    assert result.action == "downgrade_confidence"


def test_assess_evidence_with_guardrails_rejects_nonexistent_evidence_reference(monkeypatch):
    evidence_bundle, finding = make_context()
    assistant = LLMAssist()

    def fake_invoke(context: dict[str, object]) -> str:
        return json.dumps(
            {
                "is_suspicious": True,
                "possible_attack_types": ["Possible Account Compromise"],
                "confidence": "high",
                "reasoning": "This cites evidence that is not in the bundle.",
                "recommended_risk": "HIGH",
                "recommended_action": "MONITOR",
                "evidence_references": ["EV-999"],
            }
        )

    monkeypatch.setattr(assistant, "_invoke_llm_for_evidence", fake_invoke)

    assessment, result = assistant.assess_evidence_with_guardrails(evidence_bundle, finding)

    assert assessment.evidence_references == ["EV-999"]
    assert result.valid is False
    assert result.action == "reject_to_fallback"


def test_assess_evidence_does_not_mutate_finding():
    evidence_bundle, finding = make_context()
    before = finding.model_dump(mode="json")

    LLMAssist().assess_evidence(evidence_bundle, finding)

    assert finding.model_dump(mode="json") == before


def test_assess_evidence_does_not_mutate_evidence_bundle():
    evidence_bundle, finding = make_context()
    before = evidence_bundle.model_dump(mode="json")

    LLMAssist().assess_evidence(evidence_bundle, finding)

    assert evidence_bundle.model_dump(mode="json") == before
