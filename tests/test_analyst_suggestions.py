import subprocess
import sys

import pytest
from pydantic import ValidationError

from modules.analyst_suggestions import (
    AnalystSuggestion,
    AnalystSuggestionSet,
    extract_evidence_ids_from_text,
    extract_finding_ids_from_text,
    extract_rule_ids_from_text,
    suggest_followup_questions,
)


def test_analyst_suggestion_rejects_blank_question():
    with pytest.raises(ValidationError):
        AnalystSuggestion(kind="next_steps", question=" ", reason="Useful next step.")


def test_analyst_suggestion_rejects_blank_reason():
    with pytest.raises(ValidationError):
        AnalystSuggestion(kind="next_steps", question="下一步要查什麼？", reason=" ")


def test_suggestion_set_questions_returns_questions():
    suggestion_set = AnalystSuggestionSet(
        suggestions=[
            AnalystSuggestion(
                kind="next_steps",
                question="下一步要查什麼？",
                reason="Report looks suspicious.",
            )
        ]
    )

    assert suggestion_set.questions() == ["下一步要查什麼？"]


def test_suggestion_set_by_kind_filters_suggestions():
    suggestion_set = AnalystSuggestionSet(
        suggestions=[
            AnalystSuggestion(kind="next_steps", question="下一步要查什麼？", reason="A."),
            AnalystSuggestion(kind="decision_reason", question="為什麼是 MONITOR？", reason="B."),
        ]
    )

    assert [suggestion.question for suggestion in suggestion_set.by_kind("decision_reason")] == [
        "為什麼是 MONITOR？"
    ]


def test_monitor_decision_includes_monitor_question():
    suggestions = suggest_followup_questions(decision="MONITOR")

    assert "為什麼是 MONITOR？" in suggestions.questions()


def test_block_decision_includes_block_question():
    suggestions = suggest_followup_questions(decision="BLOCK")

    assert "為什麼是 BLOCK？" in suggestions.questions()


def test_risk_level_and_decision_include_difference_question():
    suggestions = suggest_followup_questions(risk_level="HIGH", decision="MONITOR")

    assert "Risk Level 跟 Decision 差在哪？" in suggestions.questions()


def test_evidence_id_ev_003_creates_ev_specific_question():
    suggestions = suggest_followup_questions(evidence_ids=["EV-003"])

    assert "EV-003 是什麼意思？" in suggestions.questions()


def test_finding_id_f_001_creates_finding_specific_question():
    suggestions = suggest_followup_questions(finding_ids=["F-001"])

    assert "F-001 代表什麼？" in suggestions.questions()


def test_rule_id_sqli_001_creates_rule_explanation_question():
    suggestions = suggest_followup_questions(rule_ids=["SQLI-001"])

    assert "SQLI-001 這條規則為什麼命中？" in suggestions.questions()


def test_suspicious_report_includes_next_step_question():
    suggestions = suggest_followup_questions(report_text="Suspicious brute force activity detected.")

    assert "下一步要查什麼？" in suggestions.questions()


def test_simulated_report_includes_safety_boundary_question():
    suggestions = suggest_followup_questions(report_text="Decision is simulated for demo.")

    assert "這個 BLOCK / MONITOR / ALLOW 是真的執行嗎？" in suggestions.questions()


def test_duplicate_suggestions_are_removed():
    suggestions = suggest_followup_questions(
        report_text="EV-003 appears again as EV 003.",
        evidence_ids=["EV-003"],
        limit=10,
    )

    assert suggestions.questions().count("EV-003 是什麼意思？") == 1


def test_limit_is_respected():
    suggestions = suggest_followup_questions(
        report_text="EV-003 F-001 SQLI-001 simulated suspicious activity.",
        decision="MONITOR",
        risk_level="HIGH",
        limit=3,
    )

    assert len(suggestions.suggestions) == 3


def test_default_suggestions_returned_when_no_signals():
    suggestions = suggest_followup_questions(limit=5)

    assert suggestions.questions() == [
        "這份報告的重點是什麼？",
        "我下一步應該先查什麼？",
    ]


def test_text_extraction_helpers_normalize_ev_f_and_rule_ids():
    text = "See EV 003, EV-003, F 001, SQLI 001, XSS-001, CMD 002, and PATH-003."

    assert extract_evidence_ids_from_text(text) == ["EV-003"]
    assert extract_finding_ids_from_text(text) == ["F-001"]
    assert extract_rule_ids_from_text(text) == ["SQLI-001", "XSS-001", "CMD-002", "PATH-003"]


def test_analyst_suggestions_module_does_not_import_runtime_heavy_modules():
    code = (
        "import sys; "
        "import modules.analyst_suggestions; "
        "forbidden={'app','modules.rag_qa','modules.detector','chromadb','ollama','langchain','torch'}; "
        "present=forbidden.intersection(sys.modules); "
        "raise SystemExit(1 if present else 0)"
    )

    result = subprocess.run([sys.executable, "-c", code], check=False)

    assert result.returncode == 0
