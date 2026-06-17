"""Focused tests for v3.1 full AI-assisted result contract."""

from types import SimpleNamespace

from modules.ai_advisory.evidence_bundle import build_evidence_grounding_bundle
from modules.ai_advisory.full_ai_assisted import (
    FULL_AI_ASSISTED_SCHEMA_VERSION,
    FullAiAssistedRequest,
    FullAiAssistedResult,
    run_full_ai_assisted,
)
from modules.ai_advisory.grounded_brief import generate_grounded_analyst_brief
from modules.ai_advisory.llm_provider import FakeLLMProvider
from modules.ai_advisory.types import AIAdvisoryInput, EvidenceGapAnalysis


def bundle():
    rag = SimpleNamespace(
        answer="Use defensive telemetry only.",
        sources=[SimpleNamespace(source="knowledge/http2.md", kind="knowledge_doc", heading="Defense")],
        confidence="MEDIUM",
        limitations=["Advisory only."],
    )
    seed = SimpleNamespace(
        case_id="CASE-SEED-001",
        title="Command Injection Payload",
        outcome="Blocked in demo.",
        analyst_conclusion="Payload was suspicious.",
    )
    similar = SimpleNamespace(
        matches=[
            SimpleNamespace(
                seed=seed,
                score=120,
                reasons=("matched rule_ids: CMD-001",),
                differences=("Check execution telemetry.",),
            )
        ]
    )
    graph = SimpleNamespace(
        nodes=[
            SimpleNamespace(id="current", label="Current Event"),
            SimpleNamespace(id="CASE-SEED-001", label="CASE-SEED-001"),
        ],
        edges=[
            SimpleNamespace(
                source_node_id="current",
                target_node_id="CASE-SEED-001",
                kind="RELATED_TO",
            )
        ],
    )
    return build_evidence_grounding_bundle(
        AIAdvisoryInput(
            event_kind="payload_or_event",
            attack_type="Command Injection",
            risk_label="HIGH",
            decision_label="BLOCK",
            matched_rule_ids=["CMD-001"],
            matched_signatures=["; rm -rf"],
            evidence_labels=["shell_metacharacter_payload"],
        ),
        evidence_gap=EvidenceGapAnalysis(
            confirmed_facts=["Rule CMD-001 matched."],
            missing_evidence=["Process execution telemetry is missing."],
            recommended_checks=["Review process creation logs."],
            unsafe_assumptions=["Do not claim command execution from payload alone."],
        ),
        rag_answer=rag,
        similar_case_result=similar,
        graph_snapshot=graph,
    )


def valid_payload():
    fallback = generate_grounded_analyst_brief(bundle())
    payload = fallback.model_dump(mode="json")
    payload["llm_status"] = "used"
    payload["executive_summary"] = [
        {"text": "Provider generated a cited advisory summary.", "citation_ids": ["rule-001"]}
    ]
    return payload


def test_disabled_provider_returns_deterministic_fallback() -> None:
    result = run_full_ai_assisted(FullAiAssistedRequest(bundle=bundle()))

    assert result.schema_version == FULL_AI_ASSISTED_SCHEMA_VERSION
    assert result.provider_mode == "disabled"
    assert result.provider_status == "disabled"
    assert result.llm_status == "not_used_deterministic_fallback"
    assert result.guardrail_status == "not_run"
    assert result.official_verdict.risk_level == "HIGH"
    assert result.official_verdict.decision == "BLOCK"
    assert result.human_review_required is True
    assert result.no_enforcement is True


def test_fake_provider_valid_output_is_accepted() -> None:
    result = run_full_ai_assisted(
        FullAiAssistedRequest(bundle=bundle()),
        provider=FakeLLMProvider(valid_payload()),
    )

    assert result.provider_mode == "fake"
    assert result.provider_status == "success"
    assert result.llm_status == "used"
    assert result.guardrail_status == "passed"
    assert result.generated_summary[0].text == "Provider generated a cited advisory summary."
    assert result.official_verdict.risk_level == "HIGH"
    assert result.official_verdict.decision == "BLOCK"


def test_provider_cannot_change_official_risk_or_decision() -> None:
    payload = valid_payload()
    payload["official_verdict"]["risk_level"] = "LOW"
    payload["official_verdict"]["decision"] = "ALLOW"

    result = run_full_ai_assisted(
        FullAiAssistedRequest(bundle=bundle()),
        provider=FakeLLMProvider(payload),
    )

    assert result.llm_status == "blocked_by_guardrail"
    assert result.guardrail_status == "blocked"
    assert result.official_verdict.risk_level == "HIGH"
    assert result.official_verdict.decision == "BLOCK"


def test_unsafe_provider_output_falls_back() -> None:
    payload = valid_payload()
    payload["recommended_next_steps"] = [
        {"text": "Generate exploit PoC traffic and update the WAF.", "citation_ids": ["rule-001"]}
    ]

    result = run_full_ai_assisted(
        FullAiAssistedRequest(bundle=bundle()),
        provider=FakeLLMProvider(payload),
    )

    assert result.llm_status == "blocked_by_guardrail"
    assert result.guardrail_status == "blocked"
    text = result.model_dump_json().lower()
    assert "generate exploit" not in text


def test_invalid_json_or_provider_failure_returns_fallback() -> None:
    invalid = run_full_ai_assisted(
        FullAiAssistedRequest(bundle=bundle()),
        provider=FakeLLMProvider("not-json"),
    )
    failure = run_full_ai_assisted(
        FullAiAssistedRequest(bundle=bundle()),
        provider=FakeLLMProvider(status="unavailable"),
    )

    assert invalid.llm_status == "invalid_json_fallback"
    assert invalid.guardrail_status == "fallback"
    assert failure.llm_status == "unavailable_fallback"
    assert failure.provider_status == "unavailable"


def test_result_includes_context_lists_and_serializes() -> None:
    result = run_full_ai_assisted(
        FullAiAssistedRequest(bundle=bundle()),
        provider=FakeLLMProvider(valid_payload()),
    )

    assert result.evidence_gaps == ["Process execution telemetry is missing."]
    assert result.unsafe_assumptions == ["Do not claim command execution from payload alone."]
    assert result.rag_sources and result.rag_sources[0]["citation_id"] == "rag-001"
    assert result.similar_case_context and "not_proof=true" in result.similar_case_context[0]
    assert result.graph_context and "not_detection_source=true" in result.graph_context[0]
    assert FullAiAssistedResult.model_validate_json(result.model_dump_json()) == result
