"""Session-state helpers for the Streamlit analyst console.

The helpers are deliberately framework-light: Streamlit passes a dict-like
session object, while the backend keeps its existing CLI state on the agent.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any

SIMILAR_CASE_COMMAND = "find similar cases"

STATE_AGENT = "sentinel_agent"
STATE_ORCHESTRATOR = "sentinel_orchestrator"
STATE_CLI_STATE = "sentinel_cli_state"
STATE_LAST_INPUT = "sentinel_last_input"
STATE_LAST_OUTPUT = "sentinel_last_output"
STATE_LAST_SELECTED_ACTION = "sentinel_last_selected_action"
STATE_ANALYSIS_OUTPUT = "sentinel_analysis_output"
STATE_SIMILAR_CASE_OUTPUT = "sentinel_similar_case_output"
# Already-computed structured advisory context (v2.9-M3/M4). These hold the
# structured SimilarCaseResult and GraphSnapshot objects produced by the
# Find Similar Cases action so the Evidence-Grounded AI Brief can consume them
# directly, instead of re-parsing the display text. Both are advisory-only and
# never override the official Risk Level or Decision.
STATE_SIMILAR_CASE_RESULT = "sentinel_similar_case_result"
STATE_GRAPH_SNAPSHOT = "sentinel_graph_snapshot"
STATE_FOLLOWUP_QUESTION = "sentinel_followup_question"
STATE_FOLLOWUP_OUTPUT = "sentinel_followup_output"
STATE_FOLLOWUP_SKILL = "sentinel_followup_skill"
STATE_KNOWLEDGE_QUESTION = "sentinel_knowledge_question"
STATE_KNOWLEDGE_OUTPUT = "sentinel_knowledge_output"
STATE_KNOWLEDGE_SKILL = "sentinel_knowledge_skill"

ACTIVE_EVENT_CONTEXT_KEY = "active_event_context"
ACTIVE_INCIDENT_CONTEXT_KEY = "active_incident_context"
ACTIVE_CONTEXT_KIND_KEY = "active_context_kind"


@dataclass(frozen=True)
class ActiveContextSummary:
    """Small display summary for the currently retained active context."""

    kind: str
    title: str
    risk_level: str
    decision: str
    details: tuple[str, ...]

    @property
    def has_context(self) -> bool:
        return bool(self.kind)


def default_cli_state() -> dict[str, Any]:
    """Return the shared CLI state shape expected by existing mode handlers."""

    return {
        "last_question": "",
        "last_answer": "",
        "last_points": [],
        "last_focus": "",
        ACTIVE_EVENT_CONTEXT_KEY: None,
        ACTIVE_INCIDENT_CONTEXT_KEY: None,
        ACTIVE_CONTEXT_KIND_KEY: "",
        "pending_case_draft_request": None,
    }


def ensure_agent_cli_state(agent: Any) -> dict[str, Any]:
    """Create or normalize the existing direct-input CLI state on an agent."""

    if not hasattr(agent, "cli_state") or not isinstance(agent.cli_state, dict):
        agent.cli_state = default_cli_state()

    for key, value in default_cli_state().items():
        agent.cli_state.setdefault(key, value)
    return agent.cli_state


def bind_runtime(
    session_state: MutableMapping[str, Any],
    *,
    agent: Any,
    orchestrator: Any,
) -> dict[str, Any]:
    """Store runtime objects and lightweight UI state in a session mapping."""

    cli_state = ensure_agent_cli_state(agent)
    session_state[STATE_AGENT] = agent
    session_state[STATE_ORCHESTRATOR] = orchestrator
    session_state[STATE_CLI_STATE] = cli_state
    session_state.setdefault(STATE_LAST_INPUT, "")
    session_state.setdefault(STATE_LAST_OUTPUT, "")
    session_state.setdefault(STATE_LAST_SELECTED_ACTION, "")
    session_state.setdefault(STATE_ANALYSIS_OUTPUT, "")
    session_state.setdefault(STATE_SIMILAR_CASE_OUTPUT, "")
    session_state.setdefault(STATE_FOLLOWUP_QUESTION, "")
    session_state.setdefault(STATE_FOLLOWUP_OUTPUT, "")
    session_state.setdefault(STATE_FOLLOWUP_SKILL, "")
    session_state.setdefault(STATE_KNOWLEDGE_QUESTION, "")
    session_state.setdefault(STATE_KNOWLEDGE_OUTPUT, "")
    session_state.setdefault(STATE_KNOWLEDGE_SKILL, "")
    session_state.setdefault(STATE_SIMILAR_CASE_RESULT, None)
    session_state.setdefault(STATE_GRAPH_SNAPSHOT, None)
    return cli_state


def record_output(
    session_state: MutableMapping[str, Any],
    *,
    user_input: str,
    response_text: str,
    selected_action: str | None,
) -> None:
    """Remember the latest direct-input execution result for display."""

    session_state[STATE_LAST_INPUT] = user_input
    session_state[STATE_LAST_OUTPUT] = response_text
    session_state[STATE_LAST_SELECTED_ACTION] = selected_action or "clarification_required"


def record_analysis_output(session_state: MutableMapping[str, Any], response_text: str) -> None:
    """Store a new analysis output and clear stale similar-case / follow-up state."""

    session_state[STATE_ANALYSIS_OUTPUT] = response_text
    session_state[STATE_SIMILAR_CASE_OUTPUT] = ""
    # A new analysis means the previous context-specific AI follow-up is stale.
    session_state[STATE_FOLLOWUP_QUESTION] = ""
    session_state[STATE_FOLLOWUP_OUTPUT] = ""
    session_state[STATE_FOLLOWUP_SKILL] = ""
    # Structured similar-case / graph advisory context is tied to the previous
    # active context, so it is stale after a new analysis.
    session_state[STATE_SIMILAR_CASE_RESULT] = None
    session_state[STATE_GRAPH_SNAPSHOT] = None


def record_similar_case_output(
    session_state: MutableMapping[str, Any],
    response_text: str,
) -> None:
    """Store similar-case output for the current active context."""

    session_state[STATE_SIMILAR_CASE_OUTPUT] = response_text


def record_structured_similar_case_context(
    session_state: MutableMapping[str, Any],
    *,
    similar_case_result: Any | None,
    graph_snapshot: Any | None,
) -> None:
    """Store the already-computed structured similar-case / graph advisory context.

    These are opaque structured objects (a ``SimilarCaseResult`` and a
    ``GraphSnapshot``) captured at the Find Similar Cases action so the
    Evidence-Grounded AI Brief can consume them without re-running retrieval or
    re-parsing display text. Both are advisory-only and never override the
    official Risk Level or Decision.
    """

    session_state[STATE_SIMILAR_CASE_RESULT] = similar_case_result
    session_state[STATE_GRAPH_SNAPSHOT] = graph_snapshot


def record_draft_action_output(
    session_state: MutableMapping[str, Any],
    *,
    command: str,
    response_text: str,
    selected_action: str | None,
) -> None:
    """Record a draft-action result without clearing preserved report sections.

    Draft actions (request / approve / cancel) must update the latest command,
    latest output, and latest selected action so the Case Draft panel and Raw
    Output reflect the newest draft command. They must NOT overwrite or clear
    the preserved analysis report or similar-case output, which the Export
    Report and report-section views still need to display.
    """

    record_output(
        session_state,
        user_input=command,
        response_text=response_text,
        selected_action=selected_action,
    )


def _record_advisory_output(
    session_state: MutableMapping[str, Any],
    *,
    question: str,
    response_text: str,
    selected_action: str | None,
    question_key: str,
    output_key: str,
    skill_key: str,
) -> None:
    """Record an advisory AI answer while preserving report sections.

    Updates the latest command / output / action (so Raw Output, Performance,
    and Route / Policy reflect the AI follow-up) and stores the question, answer,
    and the per-panel selected skill under the given keys. It must NOT touch the
    preserved analysis report or similar-case output that the report sections
    and Export Report still need.
    """

    session_state[question_key] = question
    session_state[output_key] = response_text
    session_state[skill_key] = selected_action or ""
    record_output(
        session_state,
        user_input=question,
        response_text=response_text,
        selected_action=selected_action,
    )


def record_followup_output(
    session_state: MutableMapping[str, Any],
    *,
    question: str,
    response_text: str,
    selected_action: str | None,
) -> None:
    """Record an AI follow-up answer without clearing preserved report sections."""

    _record_advisory_output(
        session_state,
        question=question,
        response_text=response_text,
        selected_action=selected_action,
        question_key=STATE_FOLLOWUP_QUESTION,
        output_key=STATE_FOLLOWUP_OUTPUT,
        skill_key=STATE_FOLLOWUP_SKILL,
    )


def record_knowledge_output(
    session_state: MutableMapping[str, Any],
    *,
    question: str,
    response_text: str,
    selected_action: str | None,
) -> None:
    """Record a Knowledge Q&A answer without clearing preserved report sections."""

    _record_advisory_output(
        session_state,
        question=question,
        response_text=response_text,
        selected_action=selected_action,
        question_key=STATE_KNOWLEDGE_QUESTION,
        output_key=STATE_KNOWLEDGE_OUTPUT,
        skill_key=STATE_KNOWLEDGE_SKILL,
    )


def clear_active_context(session_state: MutableMapping[str, Any]) -> None:
    """Clear retained active context and displayed output without touching files."""

    state = session_state.get(STATE_CLI_STATE)
    if not isinstance(state, dict):
        agent = session_state.get(STATE_AGENT)
        state = ensure_agent_cli_state(agent) if agent is not None else default_cli_state()
        session_state[STATE_CLI_STATE] = state

    state[ACTIVE_EVENT_CONTEXT_KEY] = None
    state[ACTIVE_INCIDENT_CONTEXT_KEY] = None
    state[ACTIVE_CONTEXT_KIND_KEY] = ""
    session_state[STATE_LAST_OUTPUT] = ""
    session_state[STATE_ANALYSIS_OUTPUT] = ""
    session_state[STATE_SIMILAR_CASE_OUTPUT] = ""
    session_state[STATE_FOLLOWUP_QUESTION] = ""
    session_state[STATE_FOLLOWUP_OUTPUT] = ""
    session_state[STATE_FOLLOWUP_SKILL] = ""
    session_state[STATE_KNOWLEDGE_QUESTION] = ""
    session_state[STATE_KNOWLEDGE_OUTPUT] = ""
    session_state[STATE_SIMILAR_CASE_RESULT] = None
    session_state[STATE_GRAPH_SNAPSHOT] = None
    session_state[STATE_KNOWLEDGE_SKILL] = ""
    session_state[STATE_LAST_SELECTED_ACTION] = "Clear Context"


def combined_display_output(session_state: MutableMapping[str, Any]) -> str:
    """Return analysis plus similar-case output in stable display order."""

    outputs = [
        str(session_state.get(STATE_ANALYSIS_OUTPUT) or "").strip(),
        str(session_state.get(STATE_SIMILAR_CASE_OUTPUT) or "").strip(),
    ]
    return "\n\n".join(output for output in outputs if output)


def summarize_active_context(cli_state: dict[str, Any] | None) -> ActiveContextSummary:
    """Build a compact display summary from existing active context objects."""

    state = cli_state or {}
    context_kind = str(state.get(ACTIVE_CONTEXT_KIND_KEY) or "")
    if context_kind == "event" and state.get(ACTIVE_EVENT_CONTEXT_KEY) is not None:
        return _summarize_event_context(state[ACTIVE_EVENT_CONTEXT_KEY])
    if context_kind == "incident" and state.get(ACTIVE_INCIDENT_CONTEXT_KEY) is not None:
        return _summarize_incident_context(state[ACTIVE_INCIDENT_CONTEXT_KEY])
    return ActiveContextSummary(kind="", title="No active context", risk_level="", decision="", details=())


def _summarize_event_context(context: Any) -> ActiveContextSummary:
    attack_types = tuple(str(value) for value in getattr(context, "attack_types", ()) if value)
    rule_ids = tuple(str(value) for value in getattr(context, "rule_ids", ()) if value)
    details = (
        f"Attack Type: {_join_or_none(attack_types)}",
        f"Rule IDs: {_join_or_none(rule_ids)}",
    )
    return ActiveContextSummary(
        kind="event",
        title="Payload/Event",
        risk_level=str(getattr(context, "risk_level", "")),
        decision=str(getattr(context, "decision", "")),
        details=details,
    )


def _summarize_incident_context(context: Any) -> ActiveContextSummary:
    incident = getattr(context, "incident", None)
    evidence_bundle = getattr(incident, "evidence_bundle", None)
    available_ids = sorted(getattr(evidence_bundle, "available_ids", []) or [])
    details = (
        f"Incident ID: {getattr(incident, 'id', 'N/A')}",
        f"Attack Type: {getattr(incident, 'attack_type', '') or getattr(incident, 'title', 'N/A')}",
        f"Evidence IDs: {_join_or_none(tuple(available_ids))}",
    )
    return ActiveContextSummary(
        kind="incident",
        title="Authentication Incident",
        risk_level=str(getattr(incident, "risk_level", "")),
        decision=str(getattr(incident, "decision", "")),
        details=details,
    )


def _join_or_none(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "None"
