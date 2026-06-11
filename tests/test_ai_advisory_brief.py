"""Focused tests for the deterministic AI Analyst Brief backend (v2.7-G)."""

import subprocess
import sys
from pathlib import Path

from modules.ai_advisory import (
    AIAdvisoryInput,
    AIAnalystBrief,
    AIAnalystBriefInput,
    EvidenceGapAnalysis,
    build_ai_analyst_brief,
)

AI_ADVISORY_DIR = Path(__file__).resolve().parents[1] / "modules" / "ai_advisory"
FORBIDDEN_RUNTIME_MODULES = [
    "app",
    "modules.rag",
    "modules.rag_qa",
    "modules.detector",
    "modules.controller.agent",
    "modules.controller_agent",
    "ollama",
    "chromadb",
    "langchain",
    "torch",
    "sentence_transformers",
    "requests",
    "httpx",
    "openai",
    "streamlit",
]


def command_injection_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        attack_type="Command Injection",
        risk_label="HIGH",
        decision_label="BLOCK",
        matched_rule_ids=["CMD-001"],
        matched_signatures=["; rm", "; rm -rf"],
        evidence_labels=["shell_metacharacter_payload"],
        detection_source="rule_based_detection",
    )


def sql_injection_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        attack_type="SQL Injection",
        risk_label="HIGH",
        decision_label="BLOCK",
        matched_rule_ids=["SQLI-001"],
        matched_signatures=["' OR '1'='1"],
        evidence_labels=["sql_injection_payload"],
    )


def auth_incident_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="authentication_incident",
        finding_type="Possible Account Compromise",
        risk_label="HIGH",
        decision_label="MONITOR",
        evidence_labels=["failed_then_success_auth_sequence"],
        incident_id="INC-20260605-001",
    )


def generic_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        finding_type="Unknown Anomaly",
        matched_rule_ids=["GEN-001"],
    )


def custom_gap() -> EvidenceGapAnalysis:
    return EvidenceGapAnalysis(
        confirmed_facts=["Custom confirmed fact from provided gap."],
        missing_evidence=["Custom missing evidence from provided gap."],
        recommended_checks=["Custom recommended check from provided gap."],
        unsafe_assumptions=["Custom unsafe assumption from provided gap."],
    )


def _brief_text(brief: AIAnalystBrief) -> str:
    return " ".join(
        brief.what_happened
        + brief.why_it_matters
        + brief.deterministic_verdict
        + brief.advisory_summary
        + brief.evidence_gap_summary
        + brief.recommended_next_steps
        + brief.unsafe_assumptions
        + [brief.safety_boundary]
    ).casefold()


def test_command_injection_brief_includes_rule_and_execution_not_proven_language() -> None:
    brief = build_ai_analyst_brief(AIAnalystBriefInput(advisory_input=command_injection_input()))
    text = _brief_text(brief)

    assert "cmd-001" in text
    assert "command injection" in text
    assert "successful command execution is not proven" in text or "does not prove command execution" in text
    assert "process execution" in text
    assert "edr" in text
    assert "file modification" in text
    assert "outbound" in text


def test_command_injection_brief_supports_zh_tw_output() -> None:
    brief = build_ai_analyst_brief(
        AIAnalystBriefInput(advisory_input=command_injection_input()),
        language="zh-TW",
    )
    text = _brief_text(brief)

    assert "規則式偵測命中 command injection" in text
    assert "cmd-001" in text
    assert "不代表命令已成功執行" in text
    assert "deterministic pipeline" in text
    assert "不執行真實 firewall" in text
    assert brief.llm_status == "not_used"


def test_command_injection_brief_supports_bilingual_output() -> None:
    brief = build_ai_analyst_brief(
        AIAnalystBriefInput(advisory_input=command_injection_input()),
        language="bilingual",
    )
    text = _brief_text(brief)

    assert "規則式偵測命中 command injection" in text
    assert "rule-based detection matched command injection" in text
    assert "successful command execution is not proven" in text
    assert "不執行真實 firewall" in text
    assert "no real enforcement" in text


def test_sql_injection_brief_does_not_claim_exfiltration() -> None:
    brief = build_ai_analyst_brief(AIAnalystBriefInput(advisory_input=sql_injection_input()))
    text = _brief_text(brief)

    assert "sqli-001" in text
    assert "sql injection" in text
    assert "exfiltration" in text
    assert "not proven" in text or "do not claim data exfiltration" in text
    for line in brief.what_happened + brief.why_it_matters + brief.advisory_summary:
        if "exfiltration" in line.casefold():
            assert "not proven" in line.casefold() or "does not prove" in line.casefold()
    assert "database compromise" in text


def test_authentication_brief_does_not_claim_confirmed_compromise() -> None:
    brief = build_ai_analyst_brief(AIAnalystBriefInput(advisory_input=auth_incident_input()))
    text = _brief_text(brief)

    assert "possible account compromise" in text
    assert "confirmed account compromise" in text
    assert "do not claim" in text or "before claiming" in text
    assert "mfa" in text
    assert "device" in text and "session" in text
    assert "user confirmation" in text
    assert "privileged action" in text


def test_brief_reuses_provided_evidence_gap_analysis() -> None:
    gap = custom_gap()
    brief = build_ai_analyst_brief(
        AIAnalystBriefInput(advisory_input=command_injection_input(), evidence_gap=gap)
    )

    assert brief.evidence_gap_summary == ["Custom missing evidence from provided gap."]
    assert "Custom recommended check from provided gap." in brief.recommended_next_steps
    assert brief.unsafe_assumptions == ["Custom unsafe assumption from provided gap."]
    assert "Custom confirmed fact from provided gap." in " ".join(brief.advisory_summary)


def test_brief_generates_evidence_gap_when_none_is_provided() -> None:
    brief = build_ai_analyst_brief(AIAnalystBriefInput(advisory_input=command_injection_input()))

    assert any("Process execution" in item for item in brief.evidence_gap_summary)
    assert any("EDR" in item for item in brief.recommended_next_steps)


def test_brief_includes_required_safety_boundary() -> None:
    brief = build_ai_analyst_brief(AIAnalystBriefInput(advisory_input=generic_input()))
    boundary = brief.safety_boundary.casefold()

    assert "detection is rule-based" in boundary
    assert "risk level and decision are deterministic" in boundary
    assert "block / monitor / allow are simulated" in boundary
    assert "does not override" in boundary
    assert "human review is required" in boundary


def test_llm_status_not_used() -> None:
    brief = build_ai_analyst_brief(AIAnalystBriefInput(advisory_input=generic_input()))

    assert brief.llm_status == "not_used"
    assert brief.source == "deterministic_ai_analyst_brief"


def test_brief_output_exposes_no_authoritative_final_fields() -> None:
    fields = set(AIAnalystBrief.model_fields)

    assert "risk_level" not in fields
    assert "decision" not in fields


def test_build_ai_analyst_brief_does_not_mutate_input() -> None:
    gap = custom_gap()
    brief_input = AIAnalystBriefInput(
        advisory_input=command_injection_input(),
        evidence_gap=gap,
        similar_case_ids=["CASE-SEED-001"],
        graph_relation_summary=["Current event shares rule ID CMD-001 with CASE-SEED-001."],
        case_draft_status="no pending draft",
        run_mode="fast deterministic",
    )
    snapshot = brief_input.model_copy(deep=True)

    build_ai_analyst_brief(brief_input)

    assert brief_input == snapshot


def test_brief_accepts_optional_context_without_authority_change() -> None:
    brief = build_ai_analyst_brief(
        AIAnalystBriefInput(
            advisory_input=command_injection_input(),
            similar_case_ids=["CASE-SEED-001"],
            graph_relation_summary=["Current event shares rule ID CMD-001 with CASE-SEED-001."],
            case_draft_status="no pending draft",
            run_mode="full ai assisted",
        )
    )
    text = _brief_text(brief)

    assert "case-seed-001" in text
    assert "graph relationship context" in text
    assert "no pending draft" in text
    assert "full ai assisted" in text
    assert "does not override" in text


def test_sources_have_no_runtime_or_ui_imports_or_calls() -> None:
    forbidden_import_terms = (
        "ollama",
        "rag",
        "ragqa",
        "openai",
        "requests",
        "httpx",
        "chromadb",
        "sentence_transformers",
        "langchain",
        "torch",
        "streamlit",
    )
    forbidden_call_terms = (
        "ollama.",
        "requests.",
        "httpx.",
        "openai.",
        ".generate(",
        ".chat(",
        ".embed",
    )

    for path in AI_ADVISORY_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8").casefold()
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                assert not any(term in stripped for term in forbidden_import_terms), (
                    f"forbidden import in {path.name}: {line}"
                )
        assert not any(term in source for term in forbidden_call_terms), path.name


def test_brief_import_stays_lightweight() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}
importlib.import_module("modules.ai_advisory.brief")
loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]
print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
