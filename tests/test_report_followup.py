from pathlib import Path

from modules.evidence_correlator import correlate_auth_sequence
from modules.report_followup import (
    classify_followup_intent,
    extract_evidence_ids,
    extract_finding_ids,
    lookup_evidence,
    lookup_finding,
    suggest_followups,
    answer_report_followup,
)
from modules.types import Incident


def make_auth_event(event_type: str, timestamp: str) -> dict:
    return {
        "event_type": event_type,
        "source_ip": "10.0.0.5",
        "target": "/login",
        "user": "admin",
        "timestamp": timestamp,
        "raw": f"{timestamp} {event_type} src_ip=10.0.0.5 user=admin endpoint=/login",
    }


def make_incident() -> Incident:
    events = [
        make_auth_event("auth_failure", "2026-05-01T10:00:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:01:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:02:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:03:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:04:00Z"),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z"),
    ]
    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)
    assert incident is not None
    return incident


def test_extract_evidence_ids_preserves_order_and_removes_duplicates():
    assert extract_evidence_ids("EV-003 是什麼？EV-001 和 EV-003") == [
        "EV-003",
        "EV-001",
    ]


def test_extract_finding_ids_normalizes_lowercase():
    assert extract_finding_ids("f-001 是什麼？") == ["F-001"]


def test_classify_followup_intent_detects_explain_evidence():
    assert classify_followup_intent("EV-003 是什麼意思？") == "explain_evidence"


def test_classify_followup_intent_detects_why_decision():
    assert classify_followup_intent("為什麼是 MONITOR 不是 BLOCK？") == "why_decision"


def test_classify_followup_intent_detects_next_steps():
    assert classify_followup_intent("我接下來要查什麼？") == "next_steps"


def test_lookup_evidence_returns_item():
    incident = make_incident()

    evidence = lookup_evidence(incident, "EV-003")

    assert evidence is not None
    assert evidence.type == "success_after_failures"


def test_lookup_evidence_returns_none_for_missing_id():
    assert lookup_evidence(make_incident(), "EV-999") is None


def test_lookup_finding_returns_finding():
    finding = lookup_finding(make_incident(), "F-001")

    assert finding is not None
    assert finding.finding_type == "possible_account_compromise"


def test_answer_report_followup_for_evidence_id():
    incident = make_incident()
    original_decision = incident.decision

    response = answer_report_followup("EV-003 是什麼意思？", incident)

    assert "EV-003" in str(response["answer"])
    assert "EV-003" in response["referenced_evidence"]
    assert response["confidence"] in ("high", "medium")
    assert incident.decision == original_decision


def test_answer_report_followup_for_why_monitor():
    response = answer_report_followup("為什麼是 MONITOR 不是 BLOCK？", make_incident())

    assert "MONITOR" in str(response["answer"])
    assert "analyst review" in str(response["answer"]) or "simulated" in str(response["answer"])
    assert any("risk_level_decision.md" in doc for doc in response["referenced_docs"])


def test_answer_report_followup_for_next_steps():
    response = answer_report_followup("我接下來要查什麼？", make_incident())
    answer = str(response["answer"]).lower()

    assert any(term in answer for term in ("check", "review", "log", "source_ip", "user"))
    assert any("investigation_checklist.md" in doc for doc in response["referenced_docs"])


def test_answer_report_followup_for_unknown_evidence_id():
    response = answer_report_followup("EV-999 是什麼？", make_incident())

    assert response["confidence"] in ("insufficient", "low")
    assert "找不到 EV-999" in str(response["answer"])


def test_suggest_followups_returns_static_suggestions():
    suggestions = suggest_followups("why_decision")

    assert suggestions
    assert any("BLOCK" in suggestion for suggestion in suggestions)


def test_minimal_kb_docs_exist_and_contain_key_phrases():
    docs = [
        Path("knowledge/blue_team/report_explainer/reading_the_report.md"),
        Path("knowledge/blue_team/report_explainer/risk_level_decision.md"),
        Path("knowledge/blue_team/report_explainer/investigation_checklist.md"),
        Path("knowledge/blue_team/report_explainer/security_triage_report.md"),
        Path("knowledge/blue_team/report_explainer/evidence_interpretation.md"),
        Path("knowledge/blue_team/report_explainer/detection_source_meaning.md"),
        Path("knowledge/blue_team/report_explainer/behavior_attack_triage.md"),
        Path("knowledge/blue_team/report_explainer/simulation_notice.md"),
        Path("knowledge/blue_team/report_explainer/ai_assist_limitations.md"),
        Path("knowledge/blue_team/report_explainer/disagreement_handling.md"),
        Path("knowledge/blue_team/report_explainer/incident_response_next_steps.md"),
    ]

    for doc in docs:
        assert doc.exists()
        content = doc.read_text(encoding="utf-8")
        assert content.strip()
        assert "---" in content

    combined = "\n".join(doc.read_text(encoding="utf-8") for doc in docs)
    assert "Security Triage Report" in combined
    assert "Risk Level" in combined
    assert "possible_account_compromise" in combined or "Possible Account Compromise" in combined
