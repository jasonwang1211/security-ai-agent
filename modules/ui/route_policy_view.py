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

DEFAULT_ROUTE_POLICY_LANGUAGE = "en"
_SUPPORTED_ROUTE_POLICY_LANGUAGES = ("en", "zh-TW", "bilingual")

# Language-aware fixed safety notes. English wording is byte-identical to the
# prior output; bilingual is compact "<zh> / <en>". The deterministic ToolPolicy
# reason and the route reason are dynamic backend values and are not translated.
_ROUTE_POLICY_NOTES: dict[str, dict[str, str]] = {
    "clarification_no_route": {
        "en": "No deterministic route selected a skill for execution.",
        "zh-TW": "未選擇任何確定性路由來執行技能。",
    },
    "clarification_no_write": {
        "en": "No write, ingest, promotion, or real enforcement action was executed.",
        "zh-TW": "未執行任何寫入、匯入、提升或真實防護動作。",
    },
    "detection_deterministic": {
        "en": "Detection, Risk Level, and Decision are deterministic project outputs.",
        "zh-TW": "偵測、Risk Level 與 Decision 為確定性的專案輸出。",
    },
    "simulated_no_enforcement": {
        "en": "BLOCK / MONITOR / ALLOW are simulated decisions; no real enforcement was executed.",
        "zh-TW": "BLOCK / MONITOR / ALLOW 是模擬決策；未執行任何真實防護動作。",
    },
    "historical_advisory": {
        "en": "Historical approved cases are advisory references only.",
        "zh-TW": "歷史核准案例僅供參考。",
    },
    "similar_no_override": {
        "en": "Similar cases do not override the current Risk Level or Decision.",
        "zh-TW": "相似案例不會覆蓋目前的 Risk Level 或 Decision。",
    },
    "draft_no_live": {
        "en": "No live KB write, ingest, promotion, or real enforcement is performed.",
        "zh-TW": "不會寫入即時知識庫、不會匯入、不會提升，也不會執行真實防護動作。",
    },
    "draft_isolated": {
        "en": "Draft capture writes only an isolated workbench draft after explicit approval.",
        "zh-TW": "草稿擷取只會在明確核准後寫入隔離的 workbench 草稿。",
    },
    "knowledge_advisory": {
        "en": "Knowledge answers are advisory and do not override current Risk Level or Decision.",
        "zh-TW": "知識回答僅供參考，不會覆蓋目前的 Risk Level 或 Decision。",
    },
    "no_real_devices": {
        "en": "No firewall, WAF, EDR, account, password reset, or monitoring deployment was executed.",
        "zh-TW": "未執行任何防火牆、WAF、EDR、帳號、密碼重設或監控部署。",
    },
}


def _localized_note(key: str, language: str) -> str:
    entry = _ROUTE_POLICY_NOTES[key]
    text = str(language or "").strip()
    if text not in _SUPPORTED_ROUTE_POLICY_LANGUAGES or text == "en":
        return entry["en"]
    if text == "zh-TW":
        return entry["zh-TW"]
    return f"{entry['zh-TW']} / {entry['en']}"


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
    language: str = DEFAULT_ROUTE_POLICY_LANGUAGE,
) -> RoutePolicyDisplay:
    """Build UI display data for an already-selected skill name.

    ``language`` localizes only the fixed safety notes. Permission, execution
    mode, route reason, and the deterministic ToolPolicy reason are unchanged
    backend-derived values. The default ("en") preserves existing output.
    """

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
                _localized_note("clarification_no_route", language),
                _localized_note("clarification_no_write", language),
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
        safety_notes=_safety_notes(normalized_skill, decision.reason, language),
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


def _safety_notes(
    selected_skill: str,
    policy_reason: str,
    language: str = DEFAULT_ROUTE_POLICY_LANGUAGE,
) -> tuple[str, ...]:
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
                _localized_note("detection_deterministic", language),
                _localized_note("simulated_no_enforcement", language),
            ]
        )
    elif selected_skill == RETRIEVE_APPROVED_SIMILAR_CASE_SKILL:
        notes.extend(
            [
                _localized_note("historical_advisory", language),
                _localized_note("similar_no_override", language),
            ]
        )
    elif selected_skill == DRAFT_CASE_CAPTURE_SKILL:
        notes.extend(
            [
                _localized_note("draft_no_live", language),
                _localized_note("draft_isolated", language),
            ]
        )
    elif selected_skill == KNOWLEDGE_QA_SKILL:
        notes.append(_localized_note("knowledge_advisory", language))

    notes.append(_localized_note("no_real_devices", language))
    return tuple(dict.fromkeys(notes))
