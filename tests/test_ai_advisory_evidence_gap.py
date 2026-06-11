"""Focused tests for the deterministic, LLM-free Evidence Gap Analyzer (v2.7-A).

These tests assert advisory usefulness without advisory authority:
- the analyzer never claims execution / exfiltration / confirmed compromise from
  a match alone,
- it always carries an advisory boundary and an explicit ``llm_status``,
- it exposes no authoritative final fields, does not mutate its input, and
- importing the package pulls in no LLM / RAG / Ollama runtime.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from modules.ai_advisory import (
    ADVISORY_BOUNDARY,
    AIAdvisoryInput,
    EvidenceGapAnalysis,
    analyze_evidence_gap,
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
]


# --------------------------------------------------------------------------- #
# Input builders (structured facts only)
# --------------------------------------------------------------------------- #
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
        incident_id="INC-CMD-1",
    )


def sql_injection_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        attack_type="SQL Injection",
        risk_label="HIGH",
        decision_label="BLOCK",
        matched_rule_ids=["SQLI-001"],
        matched_signatures=["' OR '1'='1"],
        evidence_labels=["tautology_sql_payload"],
    )


def auth_incident_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="authentication_incident",
        finding_type="Possible Account Compromise",
        risk_label="HIGH",
        decision_label="MONITOR",
        matched_rule_ids=["AUTH-001"],
        evidence_labels=["failed_then_success_auth_sequence"],
    )


def generic_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        finding_type="Unknown Anomaly",
        matched_rule_ids=["GEN-001"],
    )


def _all_text(analysis: EvidenceGapAnalysis) -> str:
    parts = (
        analysis.confirmed_facts
        + analysis.missing_evidence
        + analysis.recommended_checks
        + analysis.unsafe_assumptions
        + [analysis.advisory_boundary]
    )
    return " ".join(parts).lower()


ALL_BUILDERS = [
    command_injection_input,
    sql_injection_input,
    auth_incident_input,
    generic_input,
]


# --------------------------------------------------------------------------- #
# Scenario behavior
# --------------------------------------------------------------------------- #
def test_command_injection_match_does_not_prove_execution() -> None:
    analysis = analyze_evidence_gap(command_injection_input())
    text = _all_text(analysis)

    # Match does not prove command execution.
    assert "does not prove" in text
    assert "command execution" in text or "command was executed" in text

    # Confirmed payload / rule / signature facts and the provided deterministic
    # HIGH / BLOCK are echoed.
    confirmed = " ".join(analysis.confirmed_facts)
    assert "CMD-001" in confirmed
    assert "; rm" in confirmed
    assert "HIGH" in confirmed and "BLOCK" in confirmed

    # Missing evidence covers process execution, runtime telemetry, file
    # modification, and outbound connections.
    missing = " ".join(analysis.missing_evidence).lower()
    assert "process execution" in missing
    assert "telemetry" in missing
    assert "file modification" in missing
    assert "outbound" in missing

    # Recommended checks cover web server, process creation, EDR, file
    # integrity, and outbound DNS/HTTP logs.
    checks = " ".join(analysis.recommended_checks).lower()
    assert "web server" in checks
    assert "process creation" in checks
    assert "edr" in checks
    assert "file integrity" in checks
    assert "outbound dns" in checks or "outbound" in checks

    # Unsafe assumptions warn against claiming execution / compromise.
    unsafe = " ".join(analysis.unsafe_assumptions).lower()
    assert "do not claim" in unsafe
    assert "execut" in unsafe


def test_command_injection_gap_supports_zh_tw_output() -> None:
    analysis = analyze_evidence_gap(command_injection_input(), language="zh-TW")
    text = _all_text(analysis)

    assert "確定性規則命中" in text
    assert "輸入命中 command injection" in text
    assert "不代表命令已成功執行" in text
    assert "程序執行證據" in text
    assert "不執行真實 firewall" in text
    assert analysis.llm_status == "not_used"


def test_command_injection_gap_supports_bilingual_output() -> None:
    analysis = analyze_evidence_gap(command_injection_input(), language="bilingual")
    text = _all_text(analysis)

    assert "確定性規則命中" in text
    assert "deterministic rule match" in text
    assert "程序執行證據" in text
    assert "process execution evidence" in text
    assert "no real enforcement" in text


def test_sql_injection_does_not_claim_exfiltration() -> None:
    analysis = analyze_evidence_gap(sql_injection_input())
    text = _all_text(analysis)

    # An explicit warning against claiming exfiltration must be present.
    unsafe = " ".join(analysis.unsafe_assumptions).lower()
    assert "do not claim data exfiltration" in unsafe or (
        "exfiltrat" in unsafe and "do not claim" in unsafe
    )
    assert "exfiltrat" in text

    # No confirmed fact may *assert* exfiltration happened; any mention must be
    # negated (e.g. "does not prove ... exfiltrated").
    for fact in analysis.confirmed_facts:
        if "exfiltrat" in fact.lower():
            assert "not" in fact.lower()

    missing = " ".join(analysis.missing_evidence).lower()
    assert "database error" in missing
    assert "query execution" in missing
    assert "unauthorized data access" in missing
    assert "exfiltration" in missing

    checks = " ".join(analysis.recommended_checks).lower()
    assert "application logs" in checks
    assert "database audit" in checks
    assert "query trace" in checks
    assert "error logs" in checks
    assert "data-access" in checks or "data access" in checks


def test_authentication_does_not_claim_confirmed_compromise() -> None:
    analysis = analyze_evidence_gap(auth_incident_input())
    text = _all_text(analysis)

    # Confirms the observed sequence but not a confirmed compromise.
    confirmed = " ".join(analysis.confirmed_facts).lower()
    assert "failed login" in confirmed and "successful login" in confirmed

    unsafe = " ".join(analysis.unsafe_assumptions).lower()
    assert "do not claim" in unsafe
    assert "confirmed account compromise" in text

    missing = " ".join(analysis.missing_evidence).lower()
    assert "mfa" in missing
    assert "impossible-travel" in missing or "impossible travel" in missing
    assert "device" in missing and "session" in missing
    assert "user confirmation" in missing
    assert "privileged action" in missing

    checks = " ".join(analysis.recommended_checks).lower()
    assert "identity provider" in checks
    assert "mfa" in checks
    assert "session" in checks and "device" in checks
    assert "geo" in checks or "ip history" in checks
    assert "account activity" in checks


def test_generic_fallback_populates_all_sections() -> None:
    analysis = analyze_evidence_gap(generic_input())
    assert analysis.confirmed_facts
    assert analysis.missing_evidence
    assert analysis.recommended_checks
    assert analysis.unsafe_assumptions
    # The generic path still refuses to treat a match as confirmed impact.
    text = _all_text(analysis)
    assert "rule-based" in text
    assert "do not treat" in text


# --------------------------------------------------------------------------- #
# Invariants across all scenarios
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("builder", ALL_BUILDERS)
def test_output_always_contains_advisory_boundary(builder) -> None:
    analysis = analyze_evidence_gap(builder())
    assert analysis.advisory_boundary
    assert analysis.advisory_boundary == ADVISORY_BOUNDARY
    boundary = analysis.advisory_boundary.lower()
    assert "advisory" in boundary
    assert "does not" in boundary and "override" in boundary
    assert "simulated" in boundary


@pytest.mark.parametrize("builder", ALL_BUILDERS)
def test_llm_status_not_used_and_deterministic_source(builder) -> None:
    analysis = analyze_evidence_gap(builder())
    assert analysis.llm_status == "not_used"
    assert analysis.source == "deterministic_ai_advisory"


def test_no_authoritative_final_fields_exposed() -> None:
    fields = set(EvidenceGapAnalysis.model_fields)
    assert "risk_level" not in fields
    assert "decision" not in fields
    # The advisory output also carries no recomputed verdict under any obvious
    # authoritative alias.
    assert "final_risk" not in fields
    assert "final_decision" not in fields


def test_input_forbids_smuggling_authoritative_fields() -> None:
    # Extra fields are forbidden, so a caller cannot inject a field literally
    # named risk_level or decision into the advisory input. The invalid kwargs
    # are intentional (they raise ValidationError at runtime), so the static
    # call-arg complaint is suppressed on purpose.
    with pytest.raises(ValidationError):
        AIAdvisoryInput(event_kind="payload_or_event", risk_level="HIGH")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        AIAdvisoryInput(event_kind="payload_or_event", decision="BLOCK")  # type: ignore[call-arg]


def test_analyze_does_not_mutate_input() -> None:
    advisory_input = command_injection_input()
    snapshot = advisory_input.model_copy(deep=True)

    analyze_evidence_gap(advisory_input)

    assert advisory_input == snapshot
    assert advisory_input.matched_rule_ids == ["CMD-001"]
    assert advisory_input.matched_signatures == ["; rm", "; rm -rf"]
    assert advisory_input.risk_label == "HIGH"
    assert advisory_input.decision_label == "BLOCK"


@pytest.mark.parametrize("builder", ALL_BUILDERS)
def test_analysis_is_deterministic(builder) -> None:
    first = analyze_evidence_gap(builder())
    second = analyze_evidence_gap(builder())
    assert first == second


# --------------------------------------------------------------------------- #
# LLM / RAG / Ollama isolation
# --------------------------------------------------------------------------- #
def test_sources_have_no_llm_rag_ollama_imports_or_calls() -> None:
    forbidden_token = re.compile(
        r"(?i)\b(ollama|rag|ragqa|llm|openai|requests|httpx|chromadb|"
        r"sentence_transformers|langchain|torch)\b"
    )
    forbidden_call = re.compile(
        r"(?i)(ollama\s*\.|ragqa|requests\s*\.|httpx\s*\.|openai\s*\."
        r"|\.generate\s*\(|\.chat\s*\(|\.embed)"
    )

    sources = list(AI_ADVISORY_DIR.glob("*.py"))
    assert sources, "expected python sources in modules/ai_advisory"

    for path in sources:
        src = path.read_text(encoding="utf-8")
        # Only import statements are scanned for forbidden module tokens, so the
        # advisory-boundary text (which mentions "LLM" / "RAG") is not flagged.
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                assert not forbidden_token.search(stripped), (
                    f"forbidden import in {path.name}: {line}"
                )
        assert not forbidden_call.search(src), f"forbidden call pattern in {path.name}"


def _assert_import_stays_lightweight(module_name: str) -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module({module_name!r})

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


def test_package_import_stays_lightweight() -> None:
    _assert_import_stays_lightweight("modules.ai_advisory")


def test_evidence_gap_module_import_stays_lightweight() -> None:
    _assert_import_stays_lightweight("modules.ai_advisory.evidence_gap")
