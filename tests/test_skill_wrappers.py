import sys
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import modules.controller.skill_wrappers as skill_wrappers_module
from modules.controller.case_capture import PENDING_CASE_DRAFT_KEY, write_case_draft
from modules.event_followup import ActiveEventContext
from modules.incident_followup import build_active_auth_incident_context
from modules.types import EvidenceBundle, EvidenceItem, Finding, Incident

from modules.controller.types import (
    CaseDraftInput,
    IncidentJsonExportInput,
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    RawLogInput,
    ReportFollowupInput,
    ToolExecutionResult,
)
from modules.controller.skill_wrappers import (
    run_analyze_payload_skill,
    run_explain_active_event_skill,
    run_explain_active_incident_skill,
    run_draft_case_capture_skill,
    run_incident_json_export_skill,
    run_knowledge_qa_skill,
    run_log_file_ingest_skill,
    run_payload_triage_skill,
    run_rag_security_qa_skill,
    run_raw_log_translate_skill,
    run_report_followup_skill,
)


class FakeAgent:
    def __init__(self) -> None:
        self.cli_state: dict[str, Any] = {
            "last_answer": "existing report",
            "last_question": "",
            "last_points": [],
            "last_focus": "",
            "active_event_context": None,
            "active_incident_context": None,
            "active_context_kind": "",
            PENDING_CASE_DRAFT_KEY: None,
        }

    def handle_query(self, query, state):
        state["last_question"] = query
        return f"answer: {query}"

    def handle_knowledge_query(self, query, state):
        state["last_question"] = query
        return f"knowledge: {query}"


class FakeBuildRagAnswerAgent:
    def build_rag_answer(self, query):
        return f"rag: {query}"


class RaisingAgent:
    def handle_query(self, query, state):
        raise RuntimeError("boom")


def test_payload_wrapper_returns_tool_execution_result() -> None:
    result = run_payload_triage_skill(PayloadTriageInput(raw_text="<script>"), FakeAgent())

    assert isinstance(result, ToolExecutionResult)
    assert result.status == "ok"


def test_payload_wrapper_wraps_successful_text_output() -> None:
    result = run_payload_triage_skill(PayloadTriageInput(raw_text="test"), FakeAgent())

    assert result.output == {"text": "answer: test"}


def test_raw_log_translate_parses_simple_auth_log_line() -> None:
    result = run_raw_log_translate_skill(
        RawLogInput(
            raw_log="2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401"
        )
    )

    assert result.status == "ok"
    assert result.output["normalized_event_type"] == "auth_failure"


def test_raw_log_translate_returns_structured_output() -> None:
    result = run_raw_log_translate_skill(
        RawLogInput(
            raw_log="2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401"
        )
    )

    assert set(result.output) == {
        "detected_input_type",
        "normalized_event_type",
        "agent_input",
        "normalized_event",
    }
    assert result.output["normalized_event"]["source_ip"] == "10.0.0.5"


def test_log_file_ingest_handles_missing_path_gracefully() -> None:
    result = run_log_file_ingest_skill(LogFileInput(path="missing-file.log"))

    assert result.status == "error"
    assert result.error_message


def test_rag_security_qa_uses_fake_agent_handle_knowledge_query() -> None:
    result = run_rag_security_qa_skill(
        KnowledgeQuestionInput(question="SQL Injection 要怎麼防？"),
        FakeAgent(),
    )

    assert result.status == "ok"
    assert result.output["text"] == "knowledge: SQL Injection 要怎麼防？"


def test_rag_security_qa_falls_back_to_build_rag_answer() -> None:
    result = run_rag_security_qa_skill(
        KnowledgeQuestionInput(question="brute force 是什麼？"),
        FakeBuildRagAnswerAgent(),
    )

    assert result.status == "ok"
    assert result.output["text"] == "rag: brute force 是什麼？"


def test_rag_security_qa_missing_methods_returns_clarification() -> None:
    result = run_rag_security_qa_skill(
        KnowledgeQuestionInput(question="brute force 是什麼？"),
        object(),
    )

    assert result.status == "clarification_required"


def test_rag_security_qa_missing_agent_returns_error() -> None:
    result = run_rag_security_qa_skill(
        KnowledgeQuestionInput(question="brute force 是什麼？"),
        None,
    )

    assert result.status == "clarification_required"


def test_report_followup_uses_fake_agent_and_returns_answer() -> None:
    result = run_report_followup_skill(
        ReportFollowupInput(question="EV-003 是什麼意思？", last_incident_id="INC-001"),
        FakeAgent(),
    )

    assert result.status == "ok"
    assert result.output["text"] == "answer: EV-003 是什麼意思？"


def test_report_followup_missing_context_returns_clarification() -> None:
    class ContextlessAgent:
        def handle_query(self, query, state):
            return "answer"

    result = run_report_followup_skill(
        ReportFollowupInput(question="EV-003 是什麼意思？"),
        ContextlessAgent(),
    )

    assert result.status == "clarification_required"


def test_incident_json_export_accepts_incident_dict_and_returns_it() -> None:
    incident = {"id": "INC-001", "risk_level": "HIGH"}

    result = run_incident_json_export_skill(IncidentJsonExportInput(incident=incident))

    assert result.status == "ok"
    assert result.output == {"incident": incident}


def test_incident_json_export_with_only_incident_id_returns_not_implemented() -> None:
    result = run_incident_json_export_skill(IncidentJsonExportInput(incident_id="INC-001"))

    assert result.status == "clarification_required"
    assert "not implemented" in str(result.error_message)


def test_wrappers_do_not_initialize_heavy_rag_or_llm_modules() -> None:
    forbidden_modules = {
        "app",
        "chromadb",
        "langchain_chroma",
        "langchain_ollama",
        "ollama",
    }

    run_raw_log_translate_skill(
        RawLogInput(
            raw_log="2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401"
        )
    )
    run_rag_security_qa_skill(KnowledgeQuestionInput(question="test?"), FakeAgent())

    assert forbidden_modules.isdisjoint(sys.modules)


def test_wrappers_return_tool_execution_result_on_exceptions() -> None:
    result = run_payload_triage_skill(PayloadTriageInput(raw_text="test"), RaisingAgent())

    assert isinstance(result, ToolExecutionResult)
    assert result.status == "error"
    assert result.error_message == "boom"


def test_analyze_payload_skill_uses_existing_mode1_wrapper() -> None:
    result = run_analyze_payload_skill(PayloadTriageInput(raw_text="<script>"), FakeAgent())

    assert result.status == "ok"
    assert "answer: <script>" in result.output["text"]


def test_explain_active_event_skill_requires_active_event_context() -> None:
    result = run_explain_active_event_skill(
        ReportFollowupInput(question="Why BLOCK?"),
        FakeAgent(),
    )

    assert result.status == "clarification_required"


def test_explain_active_event_skill_uses_existing_agent_followup_path() -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "event"
    agent.cli_state["active_event_context"] = object()

    result = run_explain_active_event_skill(ReportFollowupInput(question="Why BLOCK?"), agent)

    assert result.status == "ok"
    assert result.output["text"] == "answer: Why BLOCK?"


def test_explain_active_incident_skill_requires_active_incident_context() -> None:
    result = run_explain_active_incident_skill(
        ReportFollowupInput(question="EV-003 是什麼？"),
        FakeAgent(),
    )

    assert result.status == "clarification_required"


def test_explain_active_incident_skill_uses_existing_agent_followup_path() -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "incident"
    agent.cli_state["active_incident_context"] = object()

    result = run_explain_active_incident_skill(
        ReportFollowupInput(question="EV-003 是什麼？"),
        agent,
    )

    assert result.status == "ok"
    assert result.output["text"] == "answer: EV-003 是什麼？"


def test_knowledge_qa_skill_uses_existing_protected_knowledge_path() -> None:
    result = run_knowledge_qa_skill(KnowledgeQuestionInput(question="What is XSS?"), FakeAgent())

    assert result.status == "ok"
    assert result.output["text"] == "knowledge: What is XSS?"


def _active_event_context(
    payload: str = "cmd=whoami; password=supersecret src=10.0.0.7",
) -> ActiveEventContext:
    return ActiveEventContext(
        original_input=payload,
        attack_types=("Command Injection",),
        matched_signatures={"Command Injection": (";", "whoami")},
        rule_ids=("CMD-001",),
        rule_sources=("detections/blue_team/command_injection.yml",),
        risk_level="HIGH",
        decision="BLOCK",
        simulation_notice="Simulated BLOCK only.",
        rendered_report="Mode 1 report",
    )


def test_case_draft_input_rejects_public_output_dir(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        CaseDraftInput.model_validate(
            {
                "action": "approve",
                "user_text": "approve draft case",
                "output_dir": str(tmp_path),
            }
        )


def test_draft_case_capture_request_without_active_context_writes_nothing(tmp_path: Path) -> None:
    agent = FakeAgent()

    result = run_draft_case_capture_skill(
        CaseDraftInput(action="request", user_text="draft this case"),
        agent,
    )

    assert result.status == "clarification_required"
    assert "No active" in str(result.error_message)
    assert list(tmp_path.iterdir()) == []
    assert agent.cli_state[PENDING_CASE_DRAFT_KEY] is None


def test_draft_case_capture_request_stores_pending_without_writing(tmp_path: Path) -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "event"
    agent.cli_state["active_event_context"] = _active_event_context()

    result = run_draft_case_capture_skill(
        CaseDraftInput(action="request", user_text="draft this case"),
        agent,
    )

    assert result.status == "clarification_required"
    assert "Explicit approval is required" in result.output["text"]
    assert agent.cli_state[PENDING_CASE_DRAFT_KEY] is not None
    assert list(tmp_path.iterdir()) == []


def test_draft_case_capture_approval_writes_pending_snapshot_and_clears_state(
    tmp_path: Path, monkeypatch
) -> None:
    agent = FakeAgent()
    monkeypatch.setattr(
        skill_wrappers_module,
        "write_case_draft",
        lambda pending: write_case_draft(pending, output_dir=tmp_path),
    )
    agent.cli_state["active_context_kind"] = "event"
    agent.cli_state["active_event_context"] = _active_event_context()
    request = run_draft_case_capture_skill(
        CaseDraftInput(action="request", user_text="draft this case"),
        agent,
    )
    pending_fingerprint = request.output["fingerprint"]
    agent.cli_state["active_event_context"] = _active_event_context("<script>alert(1)</script>")

    result = run_draft_case_capture_skill(
        CaseDraftInput(action="approve", user_text="approve draft case"),
        agent,
    )

    assert result.status == "ok"
    assert result.output["fingerprint"] == pending_fingerprint
    assert agent.cli_state[PENDING_CASE_DRAFT_KEY] is None
    draft_path = Path(result.output["draft_path"])
    assert draft_path.parent == tmp_path
    markdown = draft_path.read_text(encoding="utf-8")
    assert "supersecret" not in markdown
    assert "<script>alert" not in markdown
    assert "No real firewall" in markdown


def test_draft_case_capture_approval_without_pending_writes_nothing(tmp_path: Path) -> None:
    result = run_draft_case_capture_skill(
        CaseDraftInput(action="approve", user_text="approve draft case"),
        FakeAgent(),
    )

    assert result.status == "clarification_required"
    assert "No pending" in str(result.error_message)
    assert list(tmp_path.iterdir()) == []


def test_draft_case_capture_cancel_clears_pending_and_later_approval_writes_nothing(tmp_path: Path) -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "event"
    agent.cli_state["active_event_context"] = _active_event_context()
    run_draft_case_capture_skill(
        CaseDraftInput(action="request", user_text="draft this case"),
        agent,
    )

    cancel = run_draft_case_capture_skill(
        CaseDraftInput(action="cancel", user_text="cancel draft case"),
        agent,
    )
    approve = run_draft_case_capture_skill(
        CaseDraftInput(action="approve", user_text="approve draft case"),
        agent,
    )

    assert cancel.status == "ok"
    assert agent.cli_state[PENDING_CASE_DRAFT_KEY] is None
    assert approve.status == "clarification_required"
    assert list(tmp_path.iterdir()) == []


def _active_incident_context():
    incident = Incident(
        id="INC-20260605-001",
        title="Possible Account Compromise",
        status="ALERT",
        risk_level="HIGH",
        decision="MONITOR",
        attack_type="Possible Account Compromise",
        findings=[
            Finding(
                id="F-001",
                finding_type="possible_account_compromise",
                title="Successful login after failures",
                status="ALERT",
                risk_level="HIGH",
                decision="MONITOR",
                evidence_ids=["EV-001", "EV-003"],
            )
        ],
        evidence_bundle=EvidenceBundle(
            incident_id="INC-20260605-001",
            items=[
                EvidenceItem(
                    id="EV-001",
                    type="auth_failure_sequence",
                    description="Repeated failed login attempts",
                    value={"source_ip": "10.0.0.5", "user": "admin"},
                ),
                EvidenceItem(
                    id="EV-003",
                    type="success_after_failures",
                    description="Successful login after failures",
                    value={"source_ip": "10.0.0.5", "user": "admin"},
                ),
            ],
        ),
    )
    return build_active_auth_incident_context(
        incident,
        rendered_summary="[Log Ingestion Summary]\n\nFile: demo_logs/scenario_a_mixed_auth.log\n",
    )


def test_draft_case_capture_auth_incident_request_stores_pending_without_writing(tmp_path: Path) -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "incident"
    agent.cli_state["active_incident_context"] = _active_incident_context()

    result = run_draft_case_capture_skill(
        CaseDraftInput(action="request", user_text="draft this incident case"),
        agent,
    )

    assert result.status == "clarification_required"
    assert result.output["source_context_type"] == "active_auth_incident"
    assert agent.cli_state[PENDING_CASE_DRAFT_KEY] is not None
    assert list(tmp_path.iterdir()) == []
