"""Fast deterministic payload analysis for UI demo responsiveness.

This module is intentionally narrow: it reuses the existing deterministic
RuleBasedDetector and TriagePolicy, stores the same ActiveEventContext shape as
Mode 1, and does not call RAG or LLM assist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.controller.report_language import (
    DEFAULT_REPORT_LANGUAGE,
    labeled_line,
    normalize_report_language,
    report_text,
)
from modules.controller.skill_catalog import ANALYZE_PAYLOAD_SKILL
from modules.detector import RuleBasedDetector
from modules.event_followup import ActiveEventContext, build_active_event_context
from modules.mode_handlers import get_agent_state
from modules.responder import Responder
from modules.triage_policy import TriagePolicy

FAST_ANALYSIS_MODE_NAME = "Fast Deterministic Mode"
FAST_ANALYSIS_STATUS = "ok"

SIMULATION_BOUNDARY = (
    "BLOCK / MONITOR / ALLOW are simulated project decisions. No real firewall, "
    "WAF, EDR, account, password reset, monitoring deployment, or enforcement "
    "action was executed."
)


@dataclass(frozen=True)
class FastPayloadAnalysisResult:
    """Fast analysis output shaped like the UI needs from controller output."""

    status: str
    selected_tool: str
    response_text: str
    active_context: ActiveEventContext
    detector_result: dict[str, Any]
    risk_result: dict[str, Any]
    decision_result: dict[str, Any]


def run_fast_payload_analysis(
    agent: Any,
    user_input: str,
    language: str = DEFAULT_REPORT_LANGUAGE,
) -> FastPayloadAnalysisResult:
    """Run deterministic payload analysis without RAG or LLM explanation layers.

    Only the fixed report headings/labels/template text follow ``language``;
    detection, risk, and decision logic are unchanged and deterministic.
    """

    detector = getattr(agent, "detector", None) or RuleBasedDetector()
    triage_policy = getattr(agent, "triage_policy", None) or TriagePolicy()
    responder = getattr(agent, "responder", None) or Responder()

    detector_result = detector.inspect_text(user_input)
    risk_result = triage_policy.score_risk(detector_result)
    decision_result = triage_policy.decide(risk_result)
    defense_result = triage_policy.simulate_defense(
        decision_result,
        detector_result,
        risk_result,
    )
    report = build_fast_deterministic_report(
        detector_result=detector_result,
        risk_result=risk_result,
        decision_result=decision_result,
        defense_result=defense_result,
        responder=responder,
        language=language,
    )

    state = get_agent_state(agent)
    context = build_active_event_context(
        detector_result=detector_result,
        risk_result=risk_result,
        decision_result=decision_result,
        defense_result=defense_result,
        rendered_report=report,
    )
    state["active_event_context"] = context
    state["active_context_kind"] = "event"
    _update_state(agent, state, user_input, report)

    return FastPayloadAnalysisResult(
        status=FAST_ANALYSIS_STATUS,
        selected_tool=ANALYZE_PAYLOAD_SKILL,
        response_text=f"\nAI: {report}\n",
        active_context=context,
        detector_result=detector_result,
        risk_result=risk_result,
        decision_result=decision_result,
    )


def build_fast_deterministic_report(
    *,
    detector_result: dict[str, Any],
    risk_result: dict[str, Any],
    decision_result: dict[str, Any],
    defense_result: dict[str, Any],
    responder: Responder | None = None,
    language: str = DEFAULT_REPORT_LANGUAGE,
) -> str:
    """Render a concise deterministic report with the existing report marker.

    Fixed headings/labels/explanatory text follow ``language``; dynamic values
    (attack type, risk, decision, rule IDs, sources, indicators, payload) are
    inserted unchanged.
    """

    del responder  # Kept as an explicit seam for future shared response formatting.
    lang = normalize_report_language(language)
    attack_types = _dedupe_text(detector_result.get("attack_types") or [])
    matched_signatures = detector_result.get("matched_signatures") or {}
    metadata = detector_result.get("metadata") or {}
    risk_level = str(risk_result.get("risk_level") or "LOW")
    decision = str(decision_result.get("decision") or "ALLOW")
    none_value = report_text("none_value", lang)
    attack_text = ", ".join(attack_types) if attack_types else none_value
    detector_meta = detector_result.get("detector") or {}
    detection_source = _format_detection_source(detector_meta)
    rule_ids = _dedupe_text(metadata.get("rule_ids") or [])
    rule_sources = _dedupe_text(metadata.get("rule_sources") or [])

    lines = [
        report_text("report_title", lang),
        labeled_line("mode_label", report_text("mode_value", lang), lang),
        "",
        report_text("section_quick_verdict", lang),
        labeled_line("verdict_label", _verdict_text(attack_types, lang), lang),
        labeled_line("risk_level_label", risk_level, lang),
        labeled_line("decision_label", decision, lang),
        labeled_line("reason_label", _quick_reason(matched_signatures, lang), lang),
        "",
        report_text("section_summary", lang),
        labeled_line("status_label", str(detector_result.get("status", "UNKNOWN")), lang),
        labeled_line("attack_type_label", attack_text, lang),
        labeled_line("risk_level_label", risk_level, lang),
        labeled_line("decision_label", decision, lang),
        labeled_line("detection_source_label", detection_source, lang),
        labeled_line("rule_ids_label", _join_or_none(rule_ids, lang), lang),
        labeled_line("rule_sources_label", _join_or_none(rule_sources, lang), lang),
        "",
        report_text("section_evidence", lang),
        report_text("input_payload_heading", lang),
        str(detector_result.get("original_input") or ""),
        "",
        report_text("matched_signatures_heading", lang),
        *_format_matched_signatures(matched_signatures, lang),
        "",
        report_text("section_explanation", lang),
        report_text("explanation_line_1", lang),
        report_text("explanation_line_2", lang),
        report_text("explanation_line_3", lang),
        "",
        report_text("section_recommended", lang),
        report_text("immediate_actions_heading", lang),
        report_text("immediate_action_1", lang),
        report_text("immediate_action_2", lang),
        report_text("immediate_action_3", lang),
        "",
        report_text("mitigation_heading", lang),
        report_text("mitigation_1", lang),
        report_text("mitigation_2", lang),
        report_text("mitigation_3", lang),
        "",
        report_text("section_simulation_notice", lang),
        report_text("simulation_boundary", lang),
        "",
        report_text("section_ai_assist", lang),
        report_text("ai_assist_line_1", lang),
        report_text("ai_assist_line_2", lang),
        report_text("ai_assist_line_3", lang),
    ]
    if defense_result.get("summary"):
        lines.extend(
            [
                "",
                labeled_line(
                    "simulated_decision_note_label",
                    str(defense_result.get("summary")),
                    lang,
                ),
            ]
        )
    return "\n".join(lines).strip()


def _update_state(agent: Any, state: dict[str, Any], user_input: str, report: str) -> None:
    state["last_question"] = user_input
    state["last_answer"] = report
    followup_handler = getattr(agent, "followup_handler", None)
    if followup_handler is not None and hasattr(followup_handler, "extract_points"):
        try:
            state["last_points"] = followup_handler.extract_points(report)
        except Exception:
            state["last_points"] = []
    else:
        state["last_points"] = []
    state["last_focus"] = ""


def _format_detection_source(detector_meta: dict[str, Any]) -> str:
    name = detector_meta.get("name") or "rule_based_detector"
    detector_type = detector_meta.get("type") or "rule_based"
    return f"{name} ({detector_type})"


def _verdict_text(attack_types: list[str], language: str) -> str:
    if not attack_types:
        return report_text("verdict_unknown", language)
    return report_text("verdict_known", language).format(attack=", ".join(attack_types))


def _quick_reason(matched_signatures: dict[str, Any], language: str) -> str:
    template = report_text("reason_item", language)
    parts = []
    for attack_type, signatures in matched_signatures.items():
        cleaned = _dedupe_text(signatures or [])
        if cleaned:
            parts.append(template.format(attack=attack_type, indicators=", ".join(cleaned)))
    if not parts:
        return report_text("reason_empty", language)
    return report_text("reason_separator", language).join(parts)


def _format_matched_signatures(matched_signatures: dict[str, Any], language: str) -> list[str]:
    lines: list[str] = []
    for attack_type, signatures in matched_signatures.items():
        cleaned = _dedupe_text(signatures or [])
        lines.append(f"- {attack_type}: {_join_or_none(cleaned, language)}")
    return lines or [f"- {report_text('none_value', language)}"]


def _dedupe_text(values: Any) -> list[str]:
    output: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text not in output:
            output.append(text)
    return output


def _join_or_none(values: list[str], language: str) -> str:
    return ", ".join(values) if values else report_text("none_value", language)
