"""Deterministic Agent Skill Orchestration for direct user input.

The orchestrator is explicit routing glue over existing local capabilities. It
does not use LLM route selection, run similar-case retrieval, write knowledge,
or execute real enforcement actions.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from modules.controller.agent import ControllerAgent
from modules.controller.skill_catalog import (
    ANALYZE_AUTHENTICATION_LOG_SKILL,
    ANALYZE_PAYLOAD_SKILL,
    EXPLAIN_ACTIVE_EVENT_SKILL,
    EXPLAIN_ACTIVE_INCIDENT_SKILL,
    KNOWLEDGE_QA_SKILL,
    build_v2_4_registry,
)
from modules.controller.skill_wrappers import (
    run_analyze_authentication_log_skill,
    run_analyze_payload_skill,
    run_explain_active_event_skill,
    run_explain_active_incident_skill,
    run_knowledge_qa_skill,
)
from modules.controller.tool_policy import is_tool_allowed_without_human_approval
from modules.controller.types import ControllerOutput, RouterDecision, ToolExecutionResult
from modules.event_followup import answer_event_followup
from modules.incident_followup import answer_incident_followup
from modules.mode_handlers import get_agent_state
from modules.smart_router import route_user_input

ToolHandler = Callable[[BaseModel], ToolExecutionResult]

CLARIFICATION_TEXT = (
    "I could not deterministically route that input. Provide a payload, a log "
    "file path, a supported active-context follow-up question, or a security "
    "knowledge question."
)


class AgentSkillOrchestrator:
    """Route direct user input to the first permitted deterministic skill."""

    def __init__(self, agent: Any) -> None:
        self.agent = agent
        self.controller = ControllerAgent(
            registry=build_v2_4_registry(),
            handlers=self._build_handlers(agent),
            route_map={},
        )

    def handle_input(self, user_input: str) -> ControllerOutput:
        text = str(user_input or "").strip()
        if not text:
            return self._clarification("Input is blank.")

        selected_skill = self._select_skill(text)
        if selected_skill is None:
            return self._clarification("No deterministic v2.4 route matched the input.")

        if not is_tool_allowed_without_human_approval(selected_skill):
            return self._blocked(selected_skill)

        return self.controller.dispatch_tool(
            selected_skill,
            self._payload_for_skill(selected_skill, text),
        )

    def _select_skill(self, text: str) -> str | None:
        state = get_agent_state(self.agent)
        active_context_kind = state.get("active_context_kind")

        if active_context_kind == "incident" and _is_active_incident_followup(text, state):
            return EXPLAIN_ACTIVE_INCIDENT_SKILL
        if active_context_kind == "event" and _is_active_event_followup(text, state):
            return EXPLAIN_ACTIVE_EVENT_SKILL

        routed = route_user_input(text)
        if active_context_kind == "incident" and _should_preserve_active_context_followup(
            text,
            state,
            routed.route,
            self.agent,
        ):
            return EXPLAIN_ACTIVE_INCIDENT_SKILL
        if active_context_kind == "event" and _should_preserve_active_context_followup(
            text,
            state,
            routed.route,
            self.agent,
        ):
            return EXPLAIN_ACTIVE_EVENT_SKILL

        if routed.route == "log_file_ingest":
            return ANALYZE_AUTHENTICATION_LOG_SKILL
        if routed.route == "payload_triage":
            return ANALYZE_PAYLOAD_SKILL
        if routed.route == "rag_security_qa":
            return KNOWLEDGE_QA_SKILL

        return None

    @staticmethod
    def _payload_for_skill(skill_name: str, text: str) -> dict[str, str]:
        if skill_name == ANALYZE_AUTHENTICATION_LOG_SKILL:
            return {"path": _extract_log_path(text)}
        if skill_name == KNOWLEDGE_QA_SKILL:
            return {"question": text}
        if skill_name in {EXPLAIN_ACTIVE_EVENT_SKILL, EXPLAIN_ACTIVE_INCIDENT_SKILL}:
            return {"question": text}
        return {"raw_text": text}

    @staticmethod
    def _build_handlers(agent: Any) -> dict[str, ToolHandler]:
        def analyze_payload(input_data: BaseModel) -> ToolExecutionResult:
            return run_analyze_payload_skill(input_data, agent)  # type: ignore[arg-type]

        def analyze_auth_log(input_data: BaseModel) -> ToolExecutionResult:
            return run_analyze_authentication_log_skill(input_data, agent)  # type: ignore[arg-type]

        def explain_event(input_data: BaseModel) -> ToolExecutionResult:
            return run_explain_active_event_skill(input_data, agent)  # type: ignore[arg-type]

        def explain_incident(input_data: BaseModel) -> ToolExecutionResult:
            return run_explain_active_incident_skill(input_data, agent)  # type: ignore[arg-type]

        def knowledge_qa(input_data: BaseModel) -> ToolExecutionResult:
            return run_knowledge_qa_skill(input_data, agent)  # type: ignore[arg-type]

        return {
            ANALYZE_PAYLOAD_SKILL: analyze_payload,
            ANALYZE_AUTHENTICATION_LOG_SKILL: analyze_auth_log,
            EXPLAIN_ACTIVE_EVENT_SKILL: explain_event,
            EXPLAIN_ACTIVE_INCIDENT_SKILL: explain_incident,
            KNOWLEDGE_QA_SKILL: knowledge_qa,
        }

    @staticmethod
    def _clarification(reason: str) -> ControllerOutput:
        return ControllerOutput(
            status="clarification_required",
            selected_tool=None,
            response_text=CLARIFICATION_TEXT,
            structured_result={"error_message": CLARIFICATION_TEXT},
            route=RouterDecision(
                input_kind="unknown",
                selected_tool=None,
                confidence="LOW",
                reason=reason,
                requires_clarification=True,
            ),
            warnings=[reason],
        )

    @staticmethod
    def _blocked(skill_name: str) -> ControllerOutput:
        message = f"Selected skill is not allowed without human approval: {skill_name}"
        return ControllerOutput(
            status="clarification_required",
            selected_tool=None,
            response_text=message,
            structured_result={"error_message": message},
            route=RouterDecision(
                input_kind="unknown",
                selected_tool=None,
                confidence="LOW",
                reason=message,
                requires_clarification=True,
            ),
            warnings=[message],
        )


def build_default_v2_4_orchestrator(agent: Any) -> AgentSkillOrchestrator:
    """Build the default direct-input orchestrator for the CLI runtime."""

    return AgentSkillOrchestrator(agent)


def _is_active_incident_followup(text: str, state: dict[str, Any]) -> bool:
    context = state.get("active_incident_context")
    return context is not None and answer_incident_followup(text, context) is not None


def _is_active_event_followup(text: str, state: dict[str, Any]) -> bool:
    context = state.get("active_event_context")
    return context is not None and answer_event_followup(text, context) is not None


def _should_preserve_active_context_followup(
    text: str,
    state: dict[str, Any],
    routed_route: str,
    agent: Any,
) -> bool:
    if routed_route in {
        "log_file_ingest",
        "payload_triage",
        "rag_security_qa",
        "raw_log_translate",
        "incident_json_export",
    }:
        return False
    if routed_route == "report_followup":
        return True

    followup_handler = getattr(agent, "followup_handler", None)
    if followup_handler is not None:
        try:
            if followup_handler.is_natural_followup(text):
                return True
        except Exception:
            pass
        try:
            if followup_handler.is_contextual_followup(text, state):
                return True
        except Exception:
            pass

    return _looks_like_active_context_followup_text(text)


def _looks_like_active_context_followup_text(text: str) -> bool:
    normalized = str(text or "").strip().casefold()
    if not normalized:
        return False
    return any(
        phrase in normalized
        for phrase in (
            "what should",
            "what do",
            "what next",
            "what's next",
            "next step",
            "next steps",
            "follow up",
            "explain this",
            "does this mean",
            "is this real",
            "should we",
            "can we",
            "why did",
            "why is",
            "how should",
        )
    )


def _extract_log_path(text: str) -> str:
    stripped = text.strip().strip('"')
    lowered = stripped.casefold()
    prefixes = (
        "analyze authentication log ",
        "analyze auth log ",
        "analyze log ",
        "log file ",
        "log: ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return stripped[len(prefix) :].strip().strip('"')

    return stripped
