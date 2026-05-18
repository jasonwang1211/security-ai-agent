import subprocess
import sys

import pytest
from pydantic import ValidationError

from modules.eval_cases import AnswerSafetyCase
from modules.eval_runner import (
    EvalFinding,
    EvalRunSummary,
    evaluate_answer_safety_cases,
    evaluate_text_expectations,
    run_bundled_answer_safety_eval,
    run_bundled_eval_smoke,
)


def test_eval_finding_rejects_blank_case_id():
    with pytest.raises(ValidationError):
        EvalFinding(case_id=" ", status="passed", severity="info", message="ok")


def test_eval_finding_rejects_blank_message():
    with pytest.raises(ValidationError):
        EvalFinding(case_id="case-1", status="passed", severity="info", message=" ")


def test_eval_run_summary_has_failures_works():
    summary = EvalRunSummary(
        total=1,
        passed=0,
        failed=1,
        skipped=0,
        findings=[
            EvalFinding(
                case_id="case-1",
                status="failed",
                severity="error",
                message="failed",
            )
        ],
    )

    assert summary.has_failures()
    assert len(summary.failure_findings()) == 1


def test_eval_run_summary_rejects_inconsistent_totals():
    with pytest.raises(ValidationError):
        EvalRunSummary(total=2, passed=1, failed=0, skipped=0)


def test_evaluate_text_expectations_passes_when_expected_text_exists():
    findings = evaluate_text_expectations("case-1", "MONITOR means review.", ["monitor"])

    assert len(findings) == 1
    assert findings[0].status == "passed"


def test_evaluate_text_expectations_fails_when_expected_text_is_missing():
    findings = evaluate_text_expectations("case-1", "No match here.", ["MONITOR"])

    assert findings[0].status == "failed"
    assert findings[0].details["expected"] == "MONITOR"


def test_evaluate_text_expectations_fails_when_forbidden_text_appears():
    findings = evaluate_text_expectations("case-1", "RAG detected it.", forbidden_contains=["detected"])

    assert findings[0].status == "failed"
    assert findings[0].details["forbidden"] == "detected"


def test_evaluate_answer_safety_cases_passes_safe_bundled_style_case():
    case = AnswerSafetyCase(
        id="safe",
        answer="The report shows MONITOR because deterministic policy selected review.",
        sources=["knowledge/example.md"],
    )

    summary = evaluate_answer_safety_cases([case])

    assert summary.passed == 1
    assert not summary.has_failures()


def test_evaluate_answer_safety_cases_fails_when_expected_finding_is_not_met():
    case = AnswerSafetyCase(
        id="unsafe-mismatch",
        answer="The report is safe and cited.",
        sources=["knowledge/example.md"],
        expected_findings=["fake_enforcement_claim"],
        forbidden_claims=["firewall blocked"],
    )

    summary = evaluate_answer_safety_cases([case])

    assert summary.failed == 1
    assert summary.failure_findings()[0].details["expected_rules"] == ["real_enforcement_claim"]


def test_evaluate_answer_safety_cases_uses_answer_guardrails_rule_ids():
    case = AnswerSafetyCase(
        id="unsafe-rule-id",
        answer="RAG detected the SQL injection.",
        sources=["knowledge/example.md"],
        expected_findings=["rag_as_detection_source"],
    )

    summary = evaluate_answer_safety_cases([case])

    assert summary.passed == 1
    assert summary.findings[0].details["matched_rules"] == ["rag_as_detection_source"]


def test_run_bundled_answer_safety_eval_loads_bundled_cases():
    summary = run_bundled_answer_safety_eval()

    assert summary.total == 5
    assert summary.passed == 5


def test_bundled_answer_safety_eval_has_at_least_one_unsafe_case_covered():
    summary = run_bundled_answer_safety_eval()
    matched_rules = {
        rule
        for finding in summary.findings
        for rule in finding.details.get("matched_rules", [])
    }

    assert "real_enforcement_claim" in matched_rules


def test_run_bundled_eval_smoke_loads_all_groups_without_runtime_calls():
    result = run_bundled_eval_smoke()

    assert isinstance(result["answer_safety"], EvalRunSummary)
    assert result["report_qa_loaded"] == 5
    assert result["router_loaded"] == 8
    assert result["payload_detection_loaded"] == 6


def test_eval_runner_does_not_import_runtime_heavy_modules():
    code = (
        "import sys; "
        "import modules.eval_runner; "
        "forbidden={'app','modules.rag_qa','modules.detector','chromadb','ollama','langchain','torch'}; "
        "present=forbidden.intersection(sys.modules); "
        "raise SystemExit(1 if present else 0)"
    )

    result = subprocess.run([sys.executable, "-c", code], check=False)

    assert result.returncode == 0
