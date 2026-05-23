from typing import Any

from modules.controller.types import (
    IncidentJsonExportInput,
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    RawLogInput,
    ReportFollowupInput,
    ToolExecutionResult,
)
from modules.log_pipeline import try_translate_raw_log_input


def _ok(output: dict[str, Any], warnings: list[str] | None = None) -> ToolExecutionResult:
    return ToolExecutionResult(status="ok", output=output, warnings=warnings or [])


def _error(exc: Exception, skill_name: str) -> ToolExecutionResult:
    return ToolExecutionResult(
        status="error",
        warnings=[f"{skill_name} failed"],
        error_message=str(exc),
    )


def _clarification(message: str) -> ToolExecutionResult:
    return ToolExecutionResult(
        status="clarification_required",
        warnings=[message],
        error_message=message,
    )


def _get_agent_state(agent: Any) -> dict[str, Any]:
    if not hasattr(agent, "cli_state"):
        agent.cli_state = {
            "last_question": "",
            "last_answer": "",
            "last_points": [],
            "last_focus": "",
        }
    return agent.cli_state


def run_payload_triage_skill(
    input_data: PayloadTriageInput,
    agent: Any,
) -> ToolExecutionResult:
    try:
        if agent is None or not hasattr(agent, "handle_query"):
            return _clarification("payload_triage requires an agent with handle_query")

        result = agent.handle_query(input_data.raw_text, _get_agent_state(agent))
        return _ok({"text": result})
    except Exception as exc:
        return _error(exc, "payload_triage")


def run_raw_log_translate_skill(input_data: RawLogInput) -> ToolExecutionResult:
    try:
        translation = try_translate_raw_log_input(input_data.raw_log)
        if translation is None:
            return _clarification("raw log line could not be translated")

        return _ok(
            {
                "detected_input_type": translation.detected_input_type,
                "normalized_event_type": translation.normalized_event_type,
                "agent_input": translation.agent_input,
                "normalized_event": translation.normalized_event,
            }
        )
    except Exception as exc:
        return _error(exc, "raw_log_translate")


def run_log_file_ingest_skill(input_data: LogFileInput) -> ToolExecutionResult:
    try:
        from modules.mode_handlers import run_log_ingestion

        result = run_log_ingestion(input_data.path)
        if "No such file or directory" in result or "霈??log 瑼?憭望?" in result:
            return ToolExecutionResult(
                status="error",
                output={"text": result},
                warnings=["log_file_ingest could not read the requested file"],
                error_message=result.strip(),
            )
        return _ok({"text": result})
    except Exception as exc:
        return _error(exc, "log_file_ingest")


def run_rag_security_qa_skill(
    input_data: KnowledgeQuestionInput,
    agent: Any,
) -> ToolExecutionResult:
    try:
        if agent is None:
            return _clarification(
                "rag_security_qa requires an agent with handle_knowledge_query or build_rag_answer"
            )

        if hasattr(agent, "handle_knowledge_query"):
            result = agent.handle_knowledge_query(input_data.question, _get_agent_state(agent))
        elif hasattr(agent, "build_rag_answer"):
            result = agent.build_rag_answer(input_data.question)
        else:
            return _clarification(
                "rag_security_qa requires an agent with handle_knowledge_query or build_rag_answer"
            )
        return _ok({"text": result})
    except Exception as exc:
        return _error(exc, "rag_security_qa")


def run_report_followup_skill(
    input_data: ReportFollowupInput,
    agent: Any,
) -> ToolExecutionResult:
    try:
        if agent is None or not hasattr(agent, "handle_query"):
            return _clarification("report_followup requires an agent with handle_query")

        has_context = bool(input_data.last_incident_id) or bool(
            getattr(agent, "last_incident", None)
        ) or bool(getattr(agent, "cli_state", None))
        if not has_context:
            return _clarification("report_followup requires existing report or incident context")

        result = agent.handle_query(input_data.question, _get_agent_state(agent))
        return _ok({"text": result})
    except Exception as exc:
        return _error(exc, "report_followup")


def run_incident_json_export_skill(input_data: IncidentJsonExportInput) -> ToolExecutionResult:
    try:
        if input_data.incident:
            return _ok({"incident": input_data.incident})

        return _clarification(
            "incident archive lookup is not implemented in v1.5; provide incident data directly"
        )
    except Exception as exc:
        return _error(exc, "incident_json_export")
