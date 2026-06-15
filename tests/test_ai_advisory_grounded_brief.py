"""Focused tests for v2.9 evidence-grounded brief generation."""

import json
from types import SimpleNamespace

from modules.ai_advisory.evidence_bundle import build_evidence_grounding_bundle
from modules.ai_advisory.grounded_brief import (
    GroundedAnalystBrief,
    generate_grounded_analyst_brief,
)
from modules.ai_advisory.types import AIAdvisoryInput, EvidenceGapAnalysis


def command_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        attack_type="Command Injection",
        risk_label="HIGH",
        decision_label="BLOCK",
        matched_rule_ids=["CMD-001"],
        matched_signatures=["; rm -rf"],
        evidence_labels=["shell_metacharacter_payload"],
    )


def gap() -> EvidenceGapAnalysis:
    return EvidenceGapAnalysis(
        confirmed_facts=["Rule CMD-001 matched."],
        missing_evidence=["Process execution telemetry is missing."],
        recommended_checks=["Review process creation logs."],
        unsafe_assumptions=["Do not claim command execution from payload alone."],
    )


def bundle():
    return build_evidence_grounding_bundle(command_input(), evidence_gap=gap())


def valid_payload():
    fallback = generate_grounded_analyst_brief(bundle())
    payload = fallback.model_dump(mode="json")
    payload["llm_status"] = "used"
    return payload


def test_no_llm_uses_deterministic_fallback_and_copies_official_verdict() -> None:
    brief = generate_grounded_analyst_brief(bundle())

    assert brief.llm_status == "not_used_deterministic_fallback"
    assert brief.official_verdict.risk_level == "HIGH"
    assert brief.official_verdict.decision == "BLOCK"
    assert brief.official_verdict.simulated_decision is True
    assert GroundedAnalystBrief.model_validate_json(brief.model_dump_json()) == brief


def test_valid_llm_json_is_used_when_verdict_and_citations_are_safe() -> None:
    payload = valid_payload()

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: json.dumps(payload))

    assert brief.llm_status == "used"
    assert brief.official_verdict.risk_level == "HIGH"
    assert brief.official_verdict.decision == "BLOCK"


def test_llm_cannot_override_official_risk_or_decision() -> None:
    payload = valid_payload()
    payload["official_verdict"]["risk_level"] = "LOW"
    payload["official_verdict"]["decision"] = "ALLOW"

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: json.dumps(payload))

    assert brief.llm_status == "blocked_by_guardrail"
    assert brief.official_verdict.risk_level == "HIGH"
    assert brief.official_verdict.decision == "BLOCK"


def test_unsafe_exploit_or_real_enforcement_language_falls_back() -> None:
    payload = valid_payload()
    payload["recommended_next_steps"] = [
        {"text": "Generate exploit PoC traffic generation steps and update the WAF.", "citation_ids": ["rule-001"]}
    ]

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)

    assert brief.llm_status == "blocked_by_guardrail"
    text = brief.model_dump_json().lower()
    assert "generate exploit" not in text
    assert "traffic generation steps" not in text


def test_defensive_negated_unsafe_wording_is_allowed() -> None:
    payload = valid_payload()
    payload["recommended_next_steps"] = [
        {"text": "Do not run load testing or provide exploit PoC material.", "citation_ids": ["rule-001"]}
    ]

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)

    assert brief.llm_status == "used"


def test_similar_cases_cannot_be_written_as_proof() -> None:
    payload = valid_payload()
    payload["advisory_context"] = [
        {"text": "Similar cases prove current compromise.", "citation_ids": ["rule-001"]}
    ]

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)

    assert brief.llm_status == "blocked_by_guardrail"
    assert "similar cases are not proof" in " ".join(brief.safety_boundary).lower()


def test_graph_context_cannot_be_written_as_detection_source() -> None:
    payload = valid_payload()
    payload["advisory_context"] = [
        {"text": "Graph detected the attack and is the detection source.", "citation_ids": ["rule-001"]}
    ]

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)

    assert brief.llm_status == "blocked_by_guardrail"
    assert "graph context is not a detection source" in " ".join(brief.safety_boundary).lower()


def test_missing_citations_falls_back_to_invalid_json_status() -> None:
    payload = valid_payload()
    payload["supporting_evidence"] = [{"text": "Rule matched without citation.", "citation_ids": []}]

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)

    assert brief.llm_status == "invalid_json_fallback"
    assert brief.supporting_evidence[0].citation_ids


def test_unavailable_or_malformed_llm_falls_back() -> None:
    unavailable = generate_grounded_analyst_brief(
        bundle(), llm_client=SimpleNamespace(generate_json=lambda _prompt: (_ for _ in ()).throw(RuntimeError("down")))
    )
    malformed = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: "not-json")

    assert unavailable.llm_status == "unavailable_fallback"
    assert malformed.llm_status == "invalid_json_fallback"
