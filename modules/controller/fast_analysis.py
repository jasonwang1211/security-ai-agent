"""Fast deterministic payload analysis for UI demo responsiveness.

This module is intentionally narrow: it reuses the existing deterministic
RuleBasedDetector and TriagePolicy, stores the same ActiveEventContext shape as
Mode 1, and does not call RAG or LLM assist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


def run_fast_payload_analysis(agent: Any, user_input: str) -> FastPayloadAnalysisResult:
    """Run deterministic payload analysis without RAG or LLM explanation layers."""

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
) -> str:
    """Render a concise deterministic report with the existing report marker."""

    del responder  # Kept as an explicit seam for future shared response formatting.
    attack_types = _dedupe_text(detector_result.get("attack_types") or [])
    matched_signatures = detector_result.get("matched_signatures") or {}
    metadata = detector_result.get("metadata") or {}
    risk_level = str(risk_result.get("risk_level") or "LOW")
    decision = str(decision_result.get("decision") or "ALLOW")
    attack_text = ", ".join(attack_types) if attack_types else "None"
    detector_meta = detector_result.get("detector") or {}
    detection_source = _format_detection_source(detector_meta)
    rule_ids = _dedupe_text(metadata.get("rule_ids") or [])
    rule_sources = _dedupe_text(metadata.get("rule_sources") or [])

    lines = [
        "[Security Triage Report]",
        "Mode: Fast Deterministic Mode",
        "",
        "0. Quick Verdict",
        f"Verdict: {_verdict_text(attack_types)}",
        f"Risk Level: {risk_level}",
        f"Decision: {decision}",
        f"Reason: {_quick_reason(matched_signatures)}",
        "",
        "1. Summary",
        f"Status: {detector_result.get('status', 'UNKNOWN')}",
        f"Attack Type: {attack_text}",
        f"Risk Level: {risk_level}",
        f"Decision: {decision}",
        f"Detection Source: {detection_source}",
        f"Rule IDs: {_join_or_none(rule_ids)}",
        f"Rule Sources: {_join_or_none(rule_sources)}",
        "",
        "2. Evidence",
        "Input / Payload:",
        str(detector_result.get("original_input") or ""),
        "",
        "Matched Signatures:",
        *_format_matched_signatures(matched_signatures),
        "",
        "3. Deterministic Explanation",
        "Fast mode used rule-based detection and deterministic policy only.",
        "LLM Assist and expensive RAG explanation were skipped.",
        "The final Risk Level and Decision remain deterministic.",
        "",
        "4. Recommended Response",
        "Immediate Actions:",
        "1. Preserve request, endpoint, source, timestamp, and application logs.",
        "2. Check process logs and audit logs for execution evidence.",
        "3. Verify whether the payload reached command execution sinks.",
        "",
        "Mitigation:",
        "1. Avoid passing user input into shell commands.",
        "2. Use safe APIs instead of shell execution.",
        "3. Apply allowlist validation for command parameters.",
        "",
        "5. Simulation Notice",
        SIMULATION_BOUNDARY,
        "",
        "6. AI Assist",
        "Skipped in Fast Deterministic Mode.",
        "LLM Assist is not used in fast mode.",
        "Fast mode is for demo responsiveness, not production benchmarking.",
    ]
    if defense_result.get("summary"):
        lines.extend(["", f"Simulated Decision Note: {defense_result.get('summary')}"])
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


def _verdict_text(attack_types: list[str]) -> str:
    if not attack_types:
        return "No known attack signature was confirmed."
    return f"This event is likely {', '.join(attack_types)}."


def _quick_reason(matched_signatures: dict[str, Any]) -> str:
    parts = []
    for attack_type, signatures in matched_signatures.items():
        cleaned = _dedupe_text(signatures or [])
        if cleaned:
            parts.append(f"Matched {attack_type} indicators: {', '.join(cleaned)}")
    return "; ".join(parts) if parts else "No matched signature evidence was available."


def _format_matched_signatures(matched_signatures: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for attack_type, signatures in matched_signatures.items():
        cleaned = _dedupe_text(signatures or [])
        lines.append(f"- {attack_type}: {_join_or_none(cleaned)}")
    return lines or ["- None"]


def _dedupe_text(values: Any) -> list[str]:
    output: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text not in output:
            output.append(text)
    return output


def _join_or_none(values: list[str]) -> str:
    return ", ".join(values) if values else "None"
