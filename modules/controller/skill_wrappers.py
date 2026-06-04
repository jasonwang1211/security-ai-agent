"""Typed wrappers around existing local controller capabilities.

Wrappers adapt existing behavior to ToolExecutionResult objects. They do not add
autonomous tool selection, runtime policy enforcement, or real enforcement.
"""

from typing import Any

from modules.controller.case_capture import (
    PENDING_CASE_DRAFT_KEY,
    PendingCaseDraftRequest,
    build_pending_case_draft_request,
    write_case_draft,
)

from modules.controller.types import (
    IncidentJsonExportInput,
    CaseDraftInput,
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
            "active_event_context": None,
            "active_incident_context": None,
            "active_context_kind": "",
            PENDING_CASE_DRAFT_KEY: None,
        }
    agent.cli_state.setdefault(PENDING_CASE_DRAFT_KEY, None)
    return agent.cli_state


def run_payload_triage_skill(
    input_data: PayloadTriageInput,
    agent: Any,
) -> ToolExecutionResult:
    """Run existing payload triage behavior through a typed wrapper."""

    try:
        if agent is None or not hasattr(agent, "handle_query"):
            return _clarification("payload_triage requires an agent with handle_query")

        result = agent.handle_query(input_data.raw_text, _get_agent_state(agent))
        return _ok({"text": result})
    except Exception as exc:
        return _error(exc, "payload_triage")


def run_raw_log_translate_skill(input_data: RawLogInput) -> ToolExecutionResult:
    """Translate one raw log line through the local log pipeline."""

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
    """Run existing local log file ingestion for an explicit path."""

    try:
        # Lazy import keeps wrapper import lightweight and avoids CLI wiring at import time.
        from modules.mode_handlers import run_log_ingestion

        result = run_log_ingestion(input_data.path)
        if "No such file or directory" in result or "讀取 log 檔案失敗" in result:
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
    """Call existing advisory RAG Q&A behavior through an explicit agent method."""

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
    """Run report-aware follow-up only when prior context is available."""

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
    """Return provided incident JSON data without archive lookup or side effects."""

    try:
        if input_data.incident:
            return _ok({"incident": input_data.incident})

        return _clarification(
            "incident archive lookup is not implemented in v1.5; provide incident data directly"
        )
    except Exception as exc:
        return _error(exc, "incident_json_export")


def run_analyze_payload_skill(
    input_data: PayloadTriageInput,
    agent: Any,
) -> ToolExecutionResult:
    """Run existing Mode 1 payload/event analysis for direct-input orchestration."""

    try:
        if agent is None:
            return _clarification("AnalyzePayloadSkill requires an agent")

        from modules.mode_handlers import run_payload_analysis

        return _ok({"text": run_payload_analysis(agent, input_data.raw_text)})
    except Exception as exc:
        return _error(exc, "AnalyzePayloadSkill")


def run_analyze_authentication_log_skill(
    input_data: LogFileInput,
    agent: Any,
) -> ToolExecutionResult:
    """Run existing Mode 2 log ingestion while retaining active incident context."""

    try:
        if agent is None:
            return _clarification("AnalyzeAuthenticationLogSkill requires an agent")

        from modules.mode_handlers import run_log_ingestion

        return _ok({"text": run_log_ingestion(input_data.path, agent=agent)})
    except Exception as exc:
        return _error(exc, "AnalyzeAuthenticationLogSkill")


def run_explain_active_event_skill(
    input_data: ReportFollowupInput,
    agent: Any,
) -> ToolExecutionResult:
    """Answer follow-up questions against the current active Mode 1 event."""

    try:
        if agent is None or not hasattr(agent, "handle_query"):
            return _clarification("ExplainActiveEventSkill requires an agent with handle_query")

        state = _get_agent_state(agent)
        if state.get("active_context_kind") != "event" or state.get("active_event_context") is None:
            return _clarification("ExplainActiveEventSkill requires an active payload/event context")

        return _ok({"text": agent.handle_query(input_data.question, state)})
    except Exception as exc:
        return _error(exc, "ExplainActiveEventSkill")


def run_explain_active_incident_skill(
    input_data: ReportFollowupInput,
    agent: Any,
) -> ToolExecutionResult:
    """Answer follow-up questions against the current active Mode 2 incident."""

    try:
        if agent is None or not hasattr(agent, "handle_query"):
            return _clarification("ExplainActiveIncidentSkill requires an agent with handle_query")

        state = _get_agent_state(agent)
        if state.get("active_context_kind") != "incident" or state.get("active_incident_context") is None:
            return _clarification("ExplainActiveIncidentSkill requires an active incident context")

        return _ok({"text": agent.handle_query(input_data.question, state)})
    except Exception as exc:
        return _error(exc, "ExplainActiveIncidentSkill")


def run_knowledge_qa_skill(
    input_data: KnowledgeQuestionInput,
    agent: Any,
) -> ToolExecutionResult:
    """Run existing protected Mode 3 knowledge Q&A for direct-input orchestration."""

    return run_rag_security_qa_skill(input_data, agent)


def run_draft_case_capture_skill(
    input_data: CaseDraftInput,
    agent: Any,
) -> ToolExecutionResult:
    """Prepare, approve, or cancel an approval-gated local case draft."""

    try:
        if agent is None:
            return _clarification("DraftCaseCaptureSkill requires an agent with active context state")

        state = _get_agent_state(agent)
        if input_data.action == "cancel":
            state[PENDING_CASE_DRAFT_KEY] = None
            return _ok({"text": "Pending case draft request cancelled. No file was written."})

        if input_data.action == "request":
            pending = build_pending_case_draft_request(state, input_data.user_text)
            if pending is None:
                return _clarification(
                    "No active payload event or authentication incident is available to draft. "
                    "Analyze a payload or authentication log first; no file was written."
                )
            state[PENDING_CASE_DRAFT_KEY] = pending
            return ToolExecutionResult(
                status="clarification_required",
                output={
                    "text": (
                        "Case draft request prepared from the current active context. "
                        "Explicit approval is required before any markdown file is written. "
                        "Type 'approve draft case' to create the isolated workbench draft, "
                        "or 'cancel draft case' to clear this pending request."
                    ),
                    "fingerprint": pending.fingerprint,
                    "source_context_type": pending.source_context_type,
                },
                warnings=[
                    "DraftCaseCaptureSkill is WRITE_DRAFT and HUMAN_APPROVAL_REQUIRED; no file was written."
                ],
            )

        pending_value = state.get(PENDING_CASE_DRAFT_KEY)
        if pending_value is None:
            return _clarification("No pending case draft request exists; no file was written.")
        pending = (
            pending_value
            if isinstance(pending_value, PendingCaseDraftRequest)
            else PendingCaseDraftRequest.model_validate(pending_value)
        )
        result = write_case_draft(pending)
        if result.created or result.duplicate:
            state[PENDING_CASE_DRAFT_KEY] = None
        if result.created:
            return _ok(
                {
                    "text": f"Case draft created for human review: {result.draft_path}",
                    "draft_path": result.draft_path,
                    "fingerprint": result.fingerprint,
                },
                warnings=result.warnings,
            )
        return ToolExecutionResult(
            status="clarification_required",
            output={
                "text": f"Duplicate case draft detected; no file was overwritten: {result.draft_path}",
                "draft_path": result.draft_path,
                "fingerprint": result.fingerprint,
            },
            warnings=result.warnings,
        )
    except Exception as exc:
        return _error(exc, "DraftCaseCaptureSkill")
