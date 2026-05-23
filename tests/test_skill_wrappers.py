import sys

from modules.controller.types import (
    IncidentJsonExportInput,
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    RawLogInput,
    ReportFollowupInput,
    ToolExecutionResult,
)
from modules.controller.skill_wrappers import (
    run_incident_json_export_skill,
    run_log_file_ingest_skill,
    run_payload_triage_skill,
    run_rag_security_qa_skill,
    run_raw_log_translate_skill,
    run_report_followup_skill,
)


class FakeAgent:
    def __init__(self) -> None:
        self.cli_state = {"last_answer": "existing report"}

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
