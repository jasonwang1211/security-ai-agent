"""Focused tests for v2.9 evidence-grounded brief generation."""

import json
from types import SimpleNamespace

import pytest

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


# --- v2.9-M2 guardrail hardening ------------------------------------------


def _brief_with_next_step(text: str) -> GroundedAnalystBrief:
    """Generate a brief from an otherwise-valid LLM payload whose
    ``recommended_next_steps`` carries ``text`` (the field under test)."""

    payload = valid_payload()
    payload["recommended_next_steps"] = [{"text": text, "citation_ids": ["rule-001"]}]
    return generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)


# Non-negated unsafe assertions the hardened guardrail must block, including
# synonyms the original regex missed.
BLOCKED_UNSAFE_WORDING = [
    # real enforcement on security controls (imperative + synonyms)
    "Update the firewall rules to block the source IP.",
    "Deploy the EDR policy to isolate the host.",
    "Modify the WAF configuration to enforce the rule.",
    # account / credential manipulation (beyond reset/disable)
    "Change the user password immediately.",
    "Reset the account credentials now.",
    "Disable the user account.",
    "Revoke the user session.",
    # graph claimed as detection of the attack (revealed/identified/detected)
    "Graph revealed the attack across the hosts.",
    "Graph identified the attack path.",
    "The graph detected the attack.",
    "Graph is the detection source for this incident.",
    # similar cases claimed as proof (indicate/suggest/confirm)
    "Similar cases indicate compromise of the host.",
    "Similar cases suggest the attack succeeded.",
    "Similar cases confirm compromise.",
    # offensive generation
    "Generate exploit PoC traffic for validation.",
]


@pytest.mark.parametrize("text", BLOCKED_UNSAFE_WORDING)
def test_synonym_unsafe_enforcement_or_overclaim_is_blocked(text: str) -> None:
    brief = _brief_with_next_step(text)

    assert brief.llm_status == "blocked_by_guardrail"
    # the unsafe LLM text never reaches the rendered brief (deterministic fallback)
    assert text not in brief.model_dump_json()
    # the official deterministic verdict is preserved
    assert brief.official_verdict.risk_level == "HIGH"
    assert brief.official_verdict.decision == "BLOCK"


# Defensive negated wording that must be allowed; each exercises a required
# marker: do not / must not / should not / never / not / without / avoid /
# prevent / refrain from.
ALLOWED_DEFENSIVE_WORDING = [
    "Do not update the firewall rules automatically.",
    "Must not change the user password without approval.",
    "Should not reset the account.",
    "Never run load testing against production.",
    "Graph context is not the detection source.",
    "Similar cases do not prove compromise.",
    "Provide guidance without running exploit PoC tooling.",
    "Avoid running load testing in production.",
    "Prevent any change to the user password without a ticket.",
    "Refrain from updating the firewall rules.",
]


@pytest.mark.parametrize("text", ALLOWED_DEFENSIVE_WORDING)
def test_defensive_negated_wording_is_allowed(text: str) -> None:
    brief = _brief_with_next_step(text)

    assert brief.llm_status == "used"
    # the defensive wording is preserved in the used brief
    assert any(text in item.text for item in brief.recommended_next_steps)


def test_graph_and_similar_overclaim_blocked_in_advisory_context() -> None:
    # The guardrail applies regardless of which narrative field carries the
    # claim; advisory_context is the natural home for graph / similar-case text.
    payload = valid_payload()
    payload["advisory_context"] = [
        {"text": "Similar cases demonstrate the intrusion.", "citation_ids": ["rule-001"]},
    ]

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)

    assert brief.llm_status == "blocked_by_guardrail"


def test_official_verdict_immutable_even_with_clean_hardened_wording() -> None:
    # Verdict tampering is still blocked and the deterministic verdict preserved,
    # even when the rest of the narrative is clean defensive wording.
    payload = valid_payload()
    payload["recommended_next_steps"] = [
        {"text": "Do not update the firewall rules.", "citation_ids": ["rule-001"]},
    ]
    payload["official_verdict"]["risk_level"] = "LOW"
    payload["official_verdict"]["decision"] = "ALLOW"

    brief = generate_grounded_analyst_brief(bundle(), llm_client=lambda _prompt: payload)

    assert brief.llm_status == "blocked_by_guardrail"
    assert brief.official_verdict.risk_level == "HIGH"
    assert brief.official_verdict.decision == "BLOCK"
