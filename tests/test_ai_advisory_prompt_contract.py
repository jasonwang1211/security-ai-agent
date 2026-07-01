"""Focused tests for v3.1 prompt contract safety boundaries."""

from modules.ai_advisory.evidence_bundle import EvidenceGroundingBundle, build_evidence_grounding_bundle
from modules.ai_advisory.prompt_contract import (
    build_grounded_brief_user_prompt,
    build_soc_copilot_system_prompt,
)
from modules.ai_advisory.types import AIAdvisoryInput, EvidenceGapAnalysis


def _bundle() -> EvidenceGroundingBundle:
    return build_evidence_grounding_bundle(
        AIAdvisoryInput(
            event_kind="payload_or_event",
            attack_type="Command Injection",
            risk_label="HIGH",
            decision_label="BLOCK",
            matched_rule_ids=["CMD-001"],
            matched_signatures=["; rm -rf"],
            evidence_labels=["shell_metacharacter_payload"],
            detection_source="rule_based_detection",
            source_label="active_event_context",
        ),
        evidence_gap=EvidenceGapAnalysis(
            confirmed_facts=["Rule CMD-001 matched."],
            missing_evidence=["Process execution telemetry is missing."],
            recommended_checks=["Review process creation logs."],
            unsafe_assumptions=["Do not claim command execution from payload alone."],
        ),
    )


def test_english_system_prompt_contains_required_safety_boundary() -> None:
    prompt = build_soc_copilot_system_prompt("en")
    lowered = prompt.lower()

    assert "defensive soc analyst copilot" in lowered
    assert "rule-based detector is the detection authority" in lowered
    assert "risk level and decision are deterministic" in lowered
    assert "must be copied exactly" in lowered
    assert "must not change" in lowered
    assert "similar cases" in lowered and "not proof" in lowered
    assert "graph is not a detection source" in lowered
    assert "no real firewall" in lowered
    assert "waf" in lowered and "edr" in lowered and "siem" in lowered and "soar" in lowered
    assert "exploit" in lowered and "poc" in lowered
    assert "traffic generation" in lowered and "load testing" in lowered
    assert "offensive automation" in lowered
    assert "human review is required" in lowered


def test_zh_tw_system_prompt_contains_equivalent_safety_boundary() -> None:
    prompt = build_soc_copilot_system_prompt("zh-TW")

    assert "\u9632\u79a6\u6027 SOC analyst copilot" in prompt
    assert "Rule-Based Detector \u662f\u5075\u6e2c\u6b0a\u5a01" in prompt
    assert "Risk Level \u8207 Decision \u662f deterministic" in prompt
    assert "official verdict \u5b8c\u5168\u8907\u88fd" in prompt
    assert "\u4e0d\u5f97\u4fee\u6539" in prompt and "\u8986\u84cb Risk Level / Decision" in prompt
    assert "Similar Cases" in prompt and "\u4e0d\u662f compromise" in prompt
    assert "Graph is not a detection source" in prompt
    assert "firewall" in prompt and "WAF" in prompt and "EDR" in prompt
    assert "account" in prompt and "cloud" in prompt and "SIEM" in prompt and "SOAR" in prompt
    assert "exploit" in prompt and "PoC" in prompt
    assert "traffic generation" in prompt and "load testing" in prompt
    assert "offensive automation" in prompt
    assert "Human review" in prompt


def test_prompts_do_not_include_vendor_identity_or_enforcement_authority() -> None:
    text = "\n".join(
        [
            build_soc_copilot_system_prompt("en"),
            build_soc_copilot_system_prompt("zh-TW"),
        ]
    ).casefold()

    assert "vendor-specific model identity" not in text
    assert "you may enforce" not in text
    assert "execute firewall" not in text
    assert "perform real enforcement" not in text


def test_user_prompt_serializes_bundle_and_preserves_ids() -> None:
    bundle = _bundle()
    prompt = build_grounded_brief_user_prompt(bundle, "en")

    assert "EvidenceGroundingBundle JSON:" in prompt
    assert "CMD-001" in prompt
    assert "rule-001" in prompt
    assert "ev-001" in prompt
    assert "gap-001" in prompt
    assert "copy official_verdict exactly" in prompt.lower()


def test_zh_tw_user_prompt_requests_citation_grounding() -> None:
    prompt = build_grounded_brief_user_prompt(_bundle(), "zh-TW")

    assert "EvidenceGroundingBundle" in prompt
    assert "official_verdict \u5fc5\u9808\u5b8c\u5168\u8907\u88fd" in prompt
    assert "citation IDs" in prompt
    assert "CMD-001" in prompt
