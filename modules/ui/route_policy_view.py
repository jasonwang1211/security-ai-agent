"""Pure route/policy display helpers for the Streamlit console.

This is UI-only observability over the latest selected skill. It does not route,
execute tools, or change backend policy decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.controller.skill_catalog import (
    ANALYZE_AUTHENTICATION_LOG_SKILL,
    ANALYZE_PAYLOAD_SKILL,
    DRAFT_CASE_CAPTURE_SKILL,
    EXPLAIN_ACTIVE_EVENT_SKILL,
    EXPLAIN_ACTIVE_INCIDENT_SKILL,
    KNOWLEDGE_QA_SKILL,
    RETRIEVE_APPROVED_SIMILAR_CASE_SKILL,
)
from modules.controller.tool_policy import evaluate_tool_policy

CLARIFICATION_SELECTED_SKILL = "clarification_required"
NO_PERMISSION = "none"
NO_EXECUTION = "not executed"
NO_WRITE_BEHAVIOR = "none"


@dataclass(frozen=True)
class RoutePolicyDisplay:
    """Small immutable display model for the latest route and policy boundary."""

    selected_skill: str
    route_reason: str
    permission: str
    execution_mode: str
    human_approval_required: bool
    write_behavior: str
    safety_notes: tuple[str, ...]


def build_route_policy_display(
    selected_skill: str | None,
    latest_input: str = "",
) -> RoutePolicyDisplay:
    """Build UI display data for an already-selected skill name."""

    normalized_skill = _normalize_selected_skill(selected_skill)
    if normalized_skill == CLARIFICATION_SELECTED_SKILL:
        return RoutePolicyDisplay(
            selected_skill=CLARIFICATION_SELECTED_SKILL,
            route_reason=_clarification_reason(latest_input),
            permission=NO_PERMISSION,
            execution_mode=NO_EXECUTION,
            human_approval_required=False,
            write_behavior=NO_WRITE_BEHAVIOR,
            safety_notes=(
                "No deterministic route selected a skill for execution.",
                "No write, ingest, promotion, or real enforcement action was executed.",
            ),
        )

    decision = evaluate_tool_policy(normalized_skill)
    return RoutePolicyDisplay(
        selected_skill=normalized_skill,
        route_reason=_route_reason(normalized_skill, latest_input),
        permission=decision.permission,
        execution_mode=decision.execution_mode,
        human_approval_required=decision.requires_human_approval,
        write_behavior=_write_behavior(normalized_skill),
        safety_notes=_safety_notes(normalized_skill, decision.reason),
    )


def _normalize_selected_skill(selected_skill: str | None) -> str:
    value = str(selected_skill or "").strip()
    if not value or value.casefold() in {
        "none",
        "clarification_required",
        "input is blank",
    }:
        return CLARIFICATION_SELECTED_SKILL
    if value == "Clear Context":
        return CLARIFICATION_SELECTED_SKILL
    return value


def _route_reason(selected_skill: str, latest_input: str) -> str:
    normalized_input = " ".join(str(latest_input or "").strip().casefold().split())
    if selected_skill == ANALYZE_PAYLOAD_SKILL:
        return "payload-style input matched deterministic payload analysis route"
    if selected_skill == ANALYZE_AUTHENTICATION_LOG_SKILL:
        return "log-path input matched deterministic authentication log analysis route"
    if selected_skill == RETRIEVE_APPROVED_SIMILAR_CASE_SKILL:
        if normalized_input:
            return f'exact command matched "{latest_input}"'
        return "exact similar-case command matched deterministic retrieval route"
    if selected_skill == DRAFT_CASE_CAPTURE_SKILL:
        return "explicit case-draft command matched approval-gated draft capture route"
    if selected_skill == EXPLAIN_ACTIVE_EVENT_SKILL:
        return "active event follow-up matched deterministic event explanation route"
    if selected_skill == EXPLAIN_ACTIVE_INCIDENT_SKILL:
        return "active incident follow-up matched deterministic incident explanation route"
    if selected_skill == KNOWLEDGE_QA_SKILL:
        return "security knowledge question matched protected knowledge Q&A route"
    return "selected tool policy displayed from deterministic tool policy registry"


def _clarification_reason(latest_input: str) -> str:
    if str(latest_input or "").strip():
        return "no deterministic route matched the latest input"
    return "no deterministic route has executed yet"


def _write_behavior(selected_skill: str) -> str:
    if selected_skill == DRAFT_CASE_CAPTURE_SKILL:
        return "isolated workbench draft only after explicit approval"
    return NO_WRITE_BEHAVIOR


def _safety_notes(selected_skill: str, policy_reason: str) -> tuple[str, ...]:
    notes: list[str] = []
    if policy_reason:
        notes.append(policy_reason)

    if selected_skill in {
        ANALYZE_PAYLOAD_SKILL,
        ANALYZE_AUTHENTICATION_LOG_SKILL,
        EXPLAIN_ACTIVE_EVENT_SKILL,
        EXPLAIN_ACTIVE_INCIDENT_SKILL,
    }:
        notes.extend(
            [
                "Detection, Risk Level, and Decision are deterministic project outputs.",
                "BLOCK / MONITOR / ALLOW are simulated decisions; no real enforcement was executed.",
            ]
        )
    elif selected_skill == RETRIEVE_APPROVED_SIMILAR_CASE_SKILL:
        notes.extend(
            [
                "Historical approved cases are advisory references only.",
                "Similar cases do not override the current Risk Level or Decision.",
            ]
        )
    elif selected_skill == DRAFT_CASE_CAPTURE_SKILL:
        notes.extend(
            [
                "No live KB write, ingest, promotion, or real enforcement is performed.",
                "Draft capture writes only an isolated workbench draft after explicit approval.",
            ]
        )
    elif selected_skill == KNOWLEDGE_QA_SKILL:
        notes.append("Knowledge answers are advisory and do not override current Risk Level or Decision.")

    notes.append("No firewall, WAF, EDR, account, password reset, or monitoring deployment was executed.")
    return tuple(dict.fromkeys(notes))
