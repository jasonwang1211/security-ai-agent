from typing import Any

from pydantic import BaseModel

import modules.controller.orchestrator as orchestrator_module
from modules.controller.orchestrator import AgentSkillOrchestrator
from modules.controller.skill_catalog import (
    ANALYZE_AUTHENTICATION_LOG_SKILL,
    ANALYZE_PAYLOAD_SKILL,
    EXPLAIN_ACTIVE_EVENT_SKILL,
    EXPLAIN_ACTIVE_INCIDENT_SKILL,
    KNOWLEDGE_QA_SKILL,
)
from modules.controller.types import (
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    ReportFollowupInput,
    ToolExecutionResult,
)


class FakeFollowupHandler:
    def __init__(self, *, natural: bool = False, contextual: bool = False) -> None:
        self.natural = natural
        self.contextual = contextual

    def is_natural_followup(self, _query: str) -> bool:
        return self.natural

    def is_contextual_followup(self, _query: str, _state: dict[str, Any]) -> bool:
        return self.contextual


class FakeAgent:
    def __init__(self) -> None:
        self.cli_state: dict[str, Any] = {
            "last_question": "",
            "last_answer": "",
            "last_points": [],
            "last_focus": "",
            "active_event_context": None,
            "active_incident_context": None,
            "active_context_kind": "",
        }
        self.followup_handler = FakeFollowupHandler()


def _ok(text: str) -> ToolExecutionResult:
    return ToolExecutionResult(status="ok", output={"text": text})


def test_active_incident_followup_takes_precedence_over_event_and_knowledge(monkeypatch) -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "incident"
    agent.cli_state["active_incident_context"] = object()
    agent.cli_state["active_event_context"] = object()

    monkeypatch.setattr(orchestrator_module, "answer_incident_followup", lambda *_args: "incident")
    monkeypatch.setattr(orchestrator_module, "answer_event_followup", lambda *_args: "event")

    def incident_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, ReportFollowupInput)
        return _ok("incident follow-up")

    monkeypatch.setattr(orchestrator_module, "run_explain_active_incident_skill", incident_handler)

    output = AgentSkillOrchestrator(agent).handle_input("EV-003 和 F-001 有什麼關係？")

    assert output.status == "ok"
    assert output.selected_tool == EXPLAIN_ACTIVE_INCIDENT_SKILL
    assert output.response_text == "incident follow-up"


def test_active_event_followup_takes_precedence_over_knowledge(monkeypatch) -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "event"
    agent.cli_state["active_event_context"] = object()

    monkeypatch.setattr(orchestrator_module, "answer_event_followup", lambda *_args: "event")

    def event_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, ReportFollowupInput)
        return _ok("event follow-up")

    monkeypatch.setattr(orchestrator_module, "run_explain_active_event_skill", event_handler)

    output = AgentSkillOrchestrator(agent).handle_input("Why is the Decision BLOCK?")

    assert output.status == "ok"
    assert output.selected_tool == EXPLAIN_ACTIVE_EVENT_SKILL
    assert output.response_text == "event follow-up"


def test_log_file_path_routes_to_authentication_log_skill(monkeypatch) -> None:
    agent = FakeAgent()

    def log_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, LogFileInput)
        assert input_data.path == "demo_logs/scenario_a_mixed_auth.log"
        return _ok("log analyzed")

    monkeypatch.setattr(orchestrator_module, "run_analyze_authentication_log_skill", log_handler)

    output = AgentSkillOrchestrator(agent).handle_input("demo_logs/scenario_a_mixed_auth.log")

    assert output.status == "ok"
    assert output.selected_tool == ANALYZE_AUTHENTICATION_LOG_SKILL
    assert output.response_text == "log analyzed"


def test_windows_log_file_path_routes_to_authentication_log_skill(monkeypatch) -> None:
    agent = FakeAgent()

    def log_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, LogFileInput)
        assert input_data.path == r"demo_logs\scenario_a_mixed_auth.log"
        return _ok("windows log analyzed")

    monkeypatch.setattr(orchestrator_module, "run_analyze_authentication_log_skill", log_handler)

    output = AgentSkillOrchestrator(agent).handle_input(r"demo_logs\scenario_a_mixed_auth.log")

    assert output.status == "ok"
    assert output.selected_tool == ANALYZE_AUTHENTICATION_LOG_SKILL
    assert output.response_text == "windows log analyzed"


def test_explicit_log_analysis_request_extracts_path(monkeypatch) -> None:
    agent = FakeAgent()

    def log_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, LogFileInput)
        assert input_data.path == "demo_logs/scenario_a_mixed_auth.log"
        return _ok("explicit log analyzed")

    monkeypatch.setattr(orchestrator_module, "run_analyze_authentication_log_skill", log_handler)

    output = AgentSkillOrchestrator(agent).handle_input(
        "analyze log demo_logs/scenario_a_mixed_auth.log"
    )

    assert output.status == "ok"
    assert output.selected_tool == ANALYZE_AUTHENTICATION_LOG_SKILL
    assert output.response_text == "explicit log analyzed"


def test_explicit_windows_log_analysis_request_extracts_path(monkeypatch) -> None:
    agent = FakeAgent()

    def log_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, LogFileInput)
        assert input_data.path == r"demo_logs\scenario_a_mixed_auth.log"
        return _ok("explicit windows log analyzed")

    monkeypatch.setattr(orchestrator_module, "run_analyze_authentication_log_skill", log_handler)

    output = AgentSkillOrchestrator(agent).handle_input(
        r"analyze log demo_logs\scenario_a_mixed_auth.log"
    )

    assert output.status == "ok"
    assert output.selected_tool == ANALYZE_AUTHENTICATION_LOG_SKILL
    assert output.response_text == "explicit windows log analyzed"


def test_payload_like_input_routes_to_payload_skill(monkeypatch) -> None:
    agent = FakeAgent()

    def payload_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, PayloadTriageInput)
        assert "<script>" in input_data.raw_text
        return _ok("payload analyzed")

    monkeypatch.setattr(orchestrator_module, "run_analyze_payload_skill", payload_handler)

    output = AgentSkillOrchestrator(agent).handle_input("<script>alert(1)</script>")

    assert output.status == "ok"
    assert output.selected_tool == ANALYZE_PAYLOAD_SKILL
    assert output.response_text == "payload analyzed"


def test_active_context_natural_followup_uses_safe_existing_followup_fallback(
    monkeypatch,
) -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "event"
    agent.cli_state["active_event_context"] = object()
    agent.followup_handler = FakeFollowupHandler(natural=True)

    monkeypatch.setattr(orchestrator_module, "answer_event_followup", lambda *_args: None)

    def event_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, ReportFollowupInput)
        assert input_data.question == "What should we check next?"
        return _ok("safe existing follow-up fallback")

    monkeypatch.setattr(orchestrator_module, "run_explain_active_event_skill", event_handler)

    output = AgentSkillOrchestrator(agent).handle_input("What should we check next?")

    assert output.status == "ok"
    assert output.selected_tool == EXPLAIN_ACTIVE_EVENT_SKILL
    assert output.response_text == "safe existing follow-up fallback"


def test_general_security_question_routes_to_knowledge_skill(monkeypatch) -> None:
    agent = FakeAgent()

    def knowledge_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, KnowledgeQuestionInput)
        assert "SQL injection" in input_data.question
        return _ok("knowledge answer")

    monkeypatch.setattr(orchestrator_module, "run_knowledge_qa_skill", knowledge_handler)

    output = AgentSkillOrchestrator(agent).handle_input("What is SQL injection?")

    assert output.status == "ok"
    assert output.selected_tool == KNOWLEDGE_QA_SKILL
    assert output.response_text == "knowledge answer"


def test_general_security_question_with_active_context_still_routes_to_knowledge_skill(
    monkeypatch,
) -> None:
    agent = FakeAgent()
    agent.cli_state["active_context_kind"] = "event"
    agent.cli_state["active_event_context"] = object()
    agent.followup_handler = FakeFollowupHandler(natural=True, contextual=True)

    monkeypatch.setattr(orchestrator_module, "answer_event_followup", lambda *_args: None)

    def knowledge_handler(input_data: BaseModel, _agent) -> ToolExecutionResult:
        assert isinstance(input_data, KnowledgeQuestionInput)
        assert input_data.question == "What is SQL injection?"
        return _ok("knowledge answer with active context preserved")

    monkeypatch.setattr(orchestrator_module, "run_knowledge_qa_skill", knowledge_handler)

    output = AgentSkillOrchestrator(agent).handle_input("What is SQL injection?")

    assert output.status == "ok"
    assert output.selected_tool == KNOWLEDGE_QA_SKILL
    assert output.response_text == "knowledge answer with active context preserved"
    assert agent.cli_state["active_event_context"] is not None
    assert agent.cli_state["active_context_kind"] == "event"


def test_unknown_input_requests_clarification() -> None:
    output = AgentSkillOrchestrator(FakeAgent()).handle_input("please handle this somehow")

    assert output.status == "clarification_required"
    assert output.selected_tool is None
    assert output.route.requires_clarification
