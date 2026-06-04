"""Deterministic Agent Skill Orchestration for direct user input.

The orchestrator is explicit routing glue over existing local capabilities. It
does not use LLM route selection, run similar-case retrieval, write knowledge,
or execute real enforcement actions.
"""

from __future__ import annotations

from collections.abc import Callable
import re
from typing import Any

from pydantic import BaseModel

from modules.controller.agent import ControllerAgent
from modules.controller.skill_catalog import (
    ANALYZE_AUTHENTICATION_LOG_SKILL,
    ANALYZE_PAYLOAD_SKILL,
    DRAFT_CASE_CAPTURE_SKILL,
    EXPLAIN_ACTIVE_EVENT_SKILL,
    EXPLAIN_ACTIVE_INCIDENT_SKILL,
    KNOWLEDGE_QA_SKILL,
    build_v2_5_registry,
)
from modules.controller.skill_wrappers import (
    run_analyze_authentication_log_skill,
    run_analyze_payload_skill,
    run_draft_case_capture_skill,
    run_explain_active_event_skill,
    run_explain_active_incident_skill,
    run_knowledge_qa_skill,
)
from modules.controller.tool_policy import is_tool_allowed_without_human_approval
from modules.controller.types import (
    CaseDraftAction,
    ControllerOutput,
    RouterDecision,
    ToolExecutionResult,
)
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
            registry=build_v2_5_registry(),
            handlers=self._build_handlers(agent),
            route_map={},
        )

    def handle_input(self, user_input: str) -> ControllerOutput:
        text = str(user_input or "").strip()
        if not text:
            return self._clarification("Input is blank.")

        case_draft_action = _case_draft_action(text)
        if case_draft_action is not None:
            return self.controller.dispatch_tool(
                DRAFT_CASE_CAPTURE_SKILL,
                {"action": case_draft_action, "user_text": text},
            )

        selected_skill = self._select_skill(text)
        if selected_skill is None:
            return self._clarification("No deterministic v2.5 route matched the input.")

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

        def draft_case_capture(input_data: BaseModel) -> ToolExecutionResult:
            return run_draft_case_capture_skill(input_data, agent)  # type: ignore[arg-type]

        return {
            ANALYZE_PAYLOAD_SKILL: analyze_payload,
            ANALYZE_AUTHENTICATION_LOG_SKILL: analyze_auth_log,
            EXPLAIN_ACTIVE_EVENT_SKILL: explain_event,
            EXPLAIN_ACTIVE_INCIDENT_SKILL: explain_incident,
            KNOWLEDGE_QA_SKILL: knowledge_qa,
            DRAFT_CASE_CAPTURE_SKILL: draft_case_capture,
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


def build_default_v2_5_orchestrator(agent: Any) -> AgentSkillOrchestrator:
    """Build the default v2.5 direct-input orchestrator for the CLI runtime."""

    return AgentSkillOrchestrator(agent)


def build_default_v2_4_orchestrator(agent: Any) -> AgentSkillOrchestrator:
    """Backward-compatible builder name for tests and older imports."""

    return build_default_v2_5_orchestrator(agent)


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


def _case_draft_action(text: str) -> CaseDraftAction | None:
    normalized = " ".join(str(text or "").strip().casefold().split())
    if not normalized:
        return None

    if any(command.fullmatch(normalized) for command in _CANCEL_DRAFT_PATTERNS):
        return "cancel"
    if any(command.fullmatch(normalized) for command in _APPROVE_DRAFT_PATTERNS):
        return "approve"
    if any(command.fullmatch(normalized) for command in _REQUEST_DRAFT_PATTERNS):
        return "request"
    return None


_TITLE_SUFFIX = r"(?:\s+(?:title\s*[:=]|標題\s*[：:])\s*.+)?"
_REQUEST_DRAFT_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        rf"save this case as a draft{_TITLE_SUFFIX}",
        rf"draft this incident case{_TITLE_SUFFIX}",
        rf"draft this case{_TITLE_SUFFIX}",
        rf"請幫我把這個案例儲存成草稿{_TITLE_SUFFIX}",
        rf"請將這個案例儲存為草稿{_TITLE_SUFFIX}",
        rf"儲存這個案例為草稿{_TITLE_SUFFIX}",
        rf"儲存目前案例為草稿{_TITLE_SUFFIX}",
        rf"建立這個案例草稿{_TITLE_SUFFIX}",
        rf"撰寫這個案例草稿{_TITLE_SUFFIX}",
        rf"把這個案例存成草稿{_TITLE_SUFFIX}",
        rf"把這筆事件存成草稿{_TITLE_SUFFIX}",
        rf"建立這筆事件的案例草稿{_TITLE_SUFFIX}",
        rf"建立目前事件的案例草稿{_TITLE_SUFFIX}",
    )
)
_APPROVE_DRAFT_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"approve draft case",
        r"approve case draft",
        r"confirm draft case",
        r"confirm case draft",
        r"核准草稿案例",
        r"核准案例草稿",
        r"核可草稿案例",
        r"核可案例草稿",
        r"同意草稿案例",
        r"同意案例草稿",
        r"確認草稿案例",
        r"確認案例草稿",
        r"確認建立案例草稿",
        r"批准建立草稿",
        r"批准建立案例草稿",
    )
)
_CANCEL_DRAFT_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"cancel draft case",
        r"cancel case draft",
        r"discard draft case",
        r"discard case draft",
        r"取消草稿案例",
        r"取消案例草稿",
        r"放棄草稿案例",
        r"放棄案例草稿",
        r"取消建立草稿",
        r"取消這個案例草稿",
    )
)
