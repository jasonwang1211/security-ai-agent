import pytest
from pydantic import ValidationError

from modules.types import (
    EvidenceBundle,
    EvidenceItem,
    Finding,
    GenerationMetadata,
    Incident,
    LLMAssessment,
)


def test_evidence_item_accepts_stable_id_and_description():
    item = EvidenceItem(
        id="EV-001",
        type="failed_count",
        description="Ten failed authentication attempts were observed.",
        value=10,
    )

    assert item.id == "EV-001"
    assert item.type == "failed_count"
    assert item.value == 10
    assert item.source_event_ids == []


def test_evidence_bundle_available_ids_and_get():
    first_item = EvidenceItem(
        id="EV-001",
        type="failed_count",
        description="Multiple failed logins were observed.",
    )
    second_item = EvidenceItem(
        id="EV-002",
        type="same_source_ip",
        description="Failures came from the same source IP.",
    )
    bundle = EvidenceBundle(items=[first_item, second_item])

    assert bundle.available_ids == {"EV-001", "EV-002"}
    assert bundle.get("EV-001") == first_item
    assert bundle.get("EV-999") is None


def test_finding_can_reference_evidence_ids_and_explain_topics():
    finding = Finding(
        id="F-001",
        finding_type="possible_account_compromise",
        title="Possible account compromise",
        status="SUSPICIOUS",
        risk_level="HIGH",
        decision="MONITOR",
        evidence_ids=["EV-001", "EV-003"],
        explain_topics=["risk_level_decision", "investigation_checklist"],
    )

    assert finding.evidence_ids == ["EV-001", "EV-003"]
    assert "risk_level_decision" in finding.explain_topics


def test_generation_metadata_default_generated_at_is_populated():
    metadata = GenerationMetadata()

    assert metadata.generated_at is not None
    assert metadata.generated_at.tzinfo is not None


def test_incident_model_can_be_created_and_serialized():
    evidence = EvidenceItem(
        id="EV-001",
        type="matched_signature",
        description="A known suspicious payload signature matched.",
    )
    finding = Finding(
        id="F-001",
        finding_type="payload_alert",
        title="Suspicious payload detected",
        status="ALERT",
        risk_level="HIGH",
        decision="BLOCK",
        evidence_ids=["EV-001"],
    )
    incident = Incident(
        id="INC-20260512-001",
        title="Suspicious payload incident",
        status="ALERT",
        risk_level="HIGH",
        decision="BLOCK",
        findings=[finding],
        evidence_bundle=EvidenceBundle(incident_id="INC-20260512-001", items=[evidence]),
    )

    dumped = incident.to_json_dict()

    assert dumped["id"] == "INC-20260512-001"
    assert dumped["findings"][0]["id"] == "F-001"
    assert dumped["evidence_bundle"]["items"][0]["id"] == "EV-001"
    assert "generated_with" in dumped
    assert isinstance(dumped["generated_with"]["generated_at"], str)


def test_llm_assessment_requires_evidence_references_when_suspicious():
    assessment = LLMAssessment(
        is_suspicious=True,
        possible_attack_types=["brute_force"],
        confidence="high",
        reasoning="Repeated failures followed by a successful login.",
        recommended_risk="HIGH",
        recommended_action="MONITOR",
        evidence_references=["EV-001"],
    )

    assert assessment.is_suspicious is True
    assert assessment.evidence_references == ["EV-001"]

    with pytest.raises(ValidationError):
        LLMAssessment(
            is_suspicious=True,
            possible_attack_types=["brute_force"],
            confidence="high",
            reasoning="Repeated failures followed by a successful login.",
            recommended_risk="HIGH",
            recommended_action="MONITOR",
            evidence_references=[],
        )


@pytest.mark.parametrize("confidence", ["0.9", "super_high"])
def test_llm_assessment_rejects_invalid_confidence(confidence):
    with pytest.raises(ValidationError):
        LLMAssessment(
            is_suspicious=False,
            confidence=confidence,
            reasoning="No strong suspicious pattern was identified.",
            recommended_risk="LOW",
            recommended_action="ALLOW",
            evidence_references=[],
        )
