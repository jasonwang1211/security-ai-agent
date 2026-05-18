import subprocess
import sys

import pytest
from pydantic import ValidationError

from modules.answer_guardrails import (
    AnswerSafetyFinding,
    AnswerSafetyReport,
    check_answer_safety,
    check_answer_safety_case,
    check_raw_answer_text,
)
from modules.eval_cases import load_answer_safety_cases
from modules.rag_types import AnswerWithSources, RAGConfidence, SourceCitation


def _answer(
    text: str,
    *,
    confidence: RAGConfidence = "MEDIUM",
    limitations: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    finding_ids: list[str] | None = None,
    rule_ids: list[str] | None = None,
) -> AnswerWithSources:
    return AnswerWithSources(
        answer=text,
        sources=[SourceCitation(source="knowledge/example.md", kind="knowledge_doc")],
        evidence_ids=evidence_ids or [],
        finding_ids=finding_ids or [],
        rule_ids=rule_ids or [],
        confidence=confidence,
        limitations=limitations or [],
    )


def test_answer_safety_finding_rejects_blank_message():
    with pytest.raises(ValidationError):
        AnswerSafetyFinding(rule="missing_sources", severity="ERROR", message=" ")


def test_answer_safety_report_has_errors_works():
    report = AnswerSafetyReport(
        is_safe=True,
        findings=[
            AnswerSafetyFinding(
                rule="real_enforcement_claim",
                severity="ERROR",
                message="Unsafe claim.",
            )
        ],
    )

    assert report.has_errors()
    assert not report.is_safe
    assert len(report.findings_by_rule("real_enforcement_claim")) == 1


def test_safe_source_cited_answer_has_no_error_findings():
    report = check_answer_safety(
        _answer("The report shows MONITOR because deterministic policy selected review.")
    )

    assert report.is_safe
    assert not report.has_errors()


def test_real_firewall_block_claim_is_error():
    report = check_answer_safety(_answer("The firewall blocked the attacker in production."))

    assert report.has_errors()
    assert report.findings_by_rule("real_enforcement_claim")


def test_simulated_block_wording_is_allowed():
    report = check_answer_safety(_answer("This is a simulated BLOCK decision for training."))

    assert not report.has_errors()


def test_rag_as_detection_source_claim_is_error():
    report = check_answer_safety(_answer("RAG detected the SQL injection."))

    assert report.findings_by_rule("rag_as_detection_source")
    assert report.has_errors()


def test_llm_final_verdict_override_claim_is_error():
    report = check_answer_safety(_answer("The LLM changed the decision from MONITOR to BLOCK."))

    assert report.findings_by_rule("llm_final_verdict_override")
    assert report.has_errors()


def test_monitor_as_confirmed_compromise_claim_is_error():
    report = check_answer_safety(_answer("MONITOR means confirmed compromise."))

    assert report.findings_by_rule("monitor_as_confirmed_compromise")
    assert report.has_errors()


def test_monitor_as_possible_compromise_wording_is_allowed():
    report = check_answer_safety(_answer("MONITOR means suspicious activity and possible compromise."))

    assert not report.has_errors()


def test_invented_evidence_id_is_error_when_known_evidence_ids_provided():
    report = check_answer_safety(_answer("See EV-999.", evidence_ids=["EV-999"]), {"EV-001"})

    assert report.findings_by_rule("invented_evidence_id")
    assert report.has_errors()


def test_invented_finding_id_is_error_when_known_finding_ids_provided():
    report = check_answer_safety(
        _answer("See F-999.", finding_ids=["F-999"]),
        known_finding_ids={"F-001"},
    )

    assert report.findings_by_rule("invented_finding_id")
    assert report.has_errors()


def test_invented_rule_id_is_error_when_known_rule_ids_provided():
    report = check_answer_safety(_answer("See CMD-999.", rule_ids=["CMD-999"]), known_rule_ids={"CMD-001"})

    assert report.findings_by_rule("invented_rule_id")
    assert report.has_errors()


def test_missing_known_id_set_skips_invented_id_check():
    report = check_answer_safety(_answer("See EV-999 and F-999.", evidence_ids=["EV-999"], finding_ids=["F-999"]))

    assert not report.has_errors()


def test_low_confidence_without_limitations_creates_warning_only():
    report = check_answer_safety(_answer("Available evidence is limited.", confidence="LOW"))

    assert not report.has_errors()
    assert report.findings_by_rule("missing_limitations")
    assert report.findings_by_rule("missing_limitations")[0].severity == "WARNING"


def test_raw_answer_with_empty_sources_can_report_missing_sources():
    report = check_raw_answer_text("This answer claims a fact.", sources=[])

    assert report.findings_by_rule("missing_sources")
    assert report.has_errors()


def test_bundled_answer_safety_eval_cases_load_and_can_be_checked():
    cases = load_answer_safety_cases("eval_cases/answer_safety_cases.jsonl")
    reports = [check_answer_safety_case(case) for case in cases]

    assert len(reports) == 5
    assert any(report.has_errors() for report in reports)


def test_bundled_forbidden_real_enforcement_case_produces_error():
    cases = load_answer_safety_cases("eval_cases/answer_safety_cases.jsonl")
    case = next(case for case in cases if case.id == "answer-safety-forbid-real-firewall-block")

    report = check_answer_safety_case(case)

    assert report.findings_by_rule("real_enforcement_claim")
    assert report.has_errors()


def test_answer_guardrails_module_does_not_import_runtime_heavy_modules():
    code = (
        "import sys; "
        "import modules.answer_guardrails; "
        "forbidden={'app','modules.rag_qa','modules.detector','chromadb','ollama','langchain','torch'}; "
        "present=forbidden.intersection(sys.modules); "
        "raise SystemExit(1 if present else 0)"
    )

    result = subprocess.run([sys.executable, "-c", code], check=False)

    assert result.returncode == 0
