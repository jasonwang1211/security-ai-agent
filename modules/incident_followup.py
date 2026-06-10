"""Deterministic Mode 2 incident follow-up helpers.

These helpers explain the latest structured authentication incident retained
from Mode 2. They use only existing Incident/Evidence/Finding facts and the
explicit in-memory graph snapshot; they do not call RAG, LLM, tools, or change
Risk Level / Decision.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from modules.controller.report_language import (
    label_separator,
    normalize_report_language,
    report_text,
)
from modules.graph.builder import build_graph_snapshot
from modules.graph.types import GraphSnapshot
from modules.report_followup import explain_graph_followup_protected
from modules.types import EvidenceItem, Finding, Incident


@dataclass(frozen=True)
class ActiveAuthIncidentContext:
    """Structured facts retained from the latest Mode 2 auth correlation."""

    incident: Incident
    graph_snapshot: GraphSnapshot
    rendered_summary: str = ""
    source: str = "mode2_auth_sequence_correlation"


def build_active_auth_incident_context(
    incident: Incident,
    *,
    rendered_summary: str = "",
) -> ActiveAuthIncidentContext:
    """Build a read-only active context from an already-correlated incident."""

    return ActiveAuthIncidentContext(
        incident=incident,
        graph_snapshot=build_graph_snapshot(incident),
        rendered_summary=rendered_summary,
    )


def format_active_auth_incident_summary(
    context: ActiveAuthIncidentContext,
    language: str = "en",
) -> str:
    """Format a visible Mode 2 incident summary for follow-up handoff.

    Only the fixed titles/labels/notice text follow ``language``; the incident
    facts (ID, status, attack type, risk, decision, evidence/finding IDs) are
    inserted unchanged.
    """

    lang = normalize_report_language(language)
    sep = label_separator(lang)
    incident = context.incident
    evidence_ids = sorted(incident.evidence_bundle.available_ids)
    finding_ids = [finding.id for finding in incident.findings]
    decision_value = f"{incident.decision} {report_text('auth_decision_note', lang)}"
    return "\n".join(
        [
            report_text("auth_incident_title", lang),
            f"{report_text('incident_id_label', lang)}{sep}{incident.id}",
            f"{report_text('status_label', lang)}{sep}{incident.status}",
            f"{report_text('attack_type_label', lang)}{sep}{incident.attack_type or incident.title}",
            f"{report_text('risk_level_label', lang)}{sep}{incident.risk_level}",
            f"{report_text('decision_label', lang)}{sep}{decision_value}",
            f"{report_text('evidence_ids_label', lang)}{sep}{_join_or_none(evidence_ids)}",
            f"{report_text('finding_ids_label', lang)}{sep}{_join_or_none(finding_ids)}",
            report_text("auth_failure_then_success_note", lang),
            report_text("auth_suggested_followup_label", lang),
            *_bullet_lines(_followup_examples(evidence_ids, finding_ids, incident.decision)),
        ]
    )


def answer_incident_followup(
    question: str,
    context: ActiveAuthIncidentContext | None,
) -> str | None:
    """Answer supported Mode 4 questions against the latest Mode 2 incident."""

    if context is None:
        return None

    intent = classify_incident_followup_intent(question)
    evidence_ids = _extract_ids(question, "EV")
    finding_ids = _extract_ids(question, "F")
    incident_ids = _extract_ids(question, "INC")

    if intent == "graph_relationship":
        return _graph_relationship_answer(context, evidence_ids, finding_ids)
    if evidence_ids:
        return _evidence_answer(context, evidence_ids[0])
    if finding_ids:
        return _finding_answer(context, finding_ids[0])
    if incident_ids:
        return _incident_reference_answer(context, incident_ids[0])
    if intent == "decision_boundary":
        return _decision_boundary_answer(context)
    if intent == "compromise_uncertainty":
        return _compromise_uncertainty_answer(context)
    if intent == "investigation":
        return _investigation_answer(context)
    if intent == "classification":
        return _classification_answer(context)
    return None


def classify_incident_followup_intent(question: str) -> str | None:
    """Classify a Mode 2 incident follow-up with deterministic keyword rules."""

    text = str(question or "").casefold()
    if not text.strip():
        return None

    evidence_ids = _extract_ids(text, "EV")
    finding_ids = _extract_ids(text, "F")
    if evidence_ids and finding_ids:
        return "graph_relationship"
    if (evidence_ids or finding_ids) and _contains_any(
        text,
        ["relationship", "relation", "support", "supports", "關係", "支援", "支持"],
    ):
        return "graph_relationship"

    if _contains_any(
        text,
        [
            "monitor",
            "block",
            "allow",
            "decision",
            "為什麼是 monitor",
            "真的監控",
            "真的封鎖",
            "已經封鎖",
            "實際處置",
            "模擬",
        ],
    ):
        return "decision_boundary"

    if _contains_any(
        text,
        [
            "compromise",
            "confirmed",
            "account takeover",
            "successful intrusion",
            "已經被入侵",
            "真的被入侵",
            "帳號被盜",
            "攻擊成功",
            "成功登入代表",
        ],
    ):
        return "compromise_uncertainty"

    if _contains_any(
        text,
        [
            "next",
            "investigate",
            "investigation",
            "remediate",
            "mitigate",
            "調查",
            "修補",
            "下一步",
            "先做",
            "怎麼處理",
        ],
    ):
        return "investigation"

    if _contains_any(
        text,
        [
            "why",
            "classified",
            "classification",
            "possible account compromise",
            "為什麼",
            "判定",
            "分類",
        ],
    ):
        return "classification"

    return None


def _classification_answer(context: ActiveAuthIncidentContext) -> str:
    incident = context.incident
    finding = _primary_finding(incident)
    evidence_lines = [_format_evidence_summary(item) for item in incident.evidence_bundle.items]
    return "\n".join(
        [
            f"目前 Mode 2 structured incident 是 {incident.attack_type or incident.title}.",
            (
                f"{finding.id} / {finding.finding_type} 由這些實際 evidence 支撐："
                if finding
                else "此 incident 由這些實際 evidence 支撐："
            ),
            *_bullet_lines(evidence_lines),
            f"目前 Risk Level 為 {incident.risk_level}，Decision 為 {incident.decision}。",
            _simulated_decision_notice(),
            (
                "這是 deterministic auth sequence correlation 的結果；"
                "LLM/RAG 不會覆蓋 final verdict。"
            ),
        ]
    )


def _evidence_answer(context: ActiveAuthIncidentContext, evidence_id: str) -> str:
    incident = context.incident
    evidence = incident.evidence_bundle.get(evidence_id)
    if evidence is None:
        return _missing_reference_answer(evidence_id, context)

    protected = explain_graph_followup_protected(context.graph_snapshot, evidence_id)
    return "\n".join(
        [
            f"{evidence.id} ({evidence.type})：{evidence.description}",
            f"Value: {_format_value(evidence.value)}",
            f"Source events: {_join_or_none(evidence.source_event_ids)}",
            f"Graph fact: {protected.answer.answer}",
            "Graph lookup follows explicit incident edges only; it is not Graph RAG.",
        ]
    )


def _finding_answer(context: ActiveAuthIncidentContext, finding_id: str) -> str:
    finding = _find_finding(context.incident, finding_id)
    if finding is None:
        return _missing_reference_answer(finding_id, context)

    protected = explain_graph_followup_protected(context.graph_snapshot, finding_id)
    return "\n".join(
        [
            f"{finding.id} / {finding.finding_type}: {finding.title}",
            f"Status: {finding.status}; Risk Level: {finding.risk_level}; Decision: {finding.decision}.",
            f"Evidence IDs: {_join_or_none(finding.evidence_ids)}",
            f"Graph fact: {protected.answer.answer}",
            _simulated_decision_notice(),
        ]
    )


def _incident_reference_answer(context: ActiveAuthIncidentContext, incident_id: str) -> str:
    if incident_id != context.incident.id:
        return _missing_reference_answer(incident_id, context)

    protected = explain_graph_followup_protected(context.graph_snapshot, incident_id)
    return "\n".join(
        [
            f"{context.incident.id}: {context.incident.title}",
            f"Status: {context.incident.status}; Risk Level: {context.incident.risk_level}; Decision: {context.incident.decision}.",
            f"Graph fact: {protected.answer.answer}",
            _simulated_decision_notice(),
        ]
    )


def _graph_relationship_answer(
    context: ActiveAuthIncidentContext,
    evidence_ids: list[str],
    finding_ids: list[str],
) -> str | None:
    if not evidence_ids and not finding_ids:
        return None

    incident = context.incident
    evidence_id = evidence_ids[0] if evidence_ids else ""
    finding_id = finding_ids[0] if finding_ids else ""
    evidence = incident.evidence_bundle.get(evidence_id) if evidence_id else None
    finding = _find_finding(incident, finding_id) if finding_id else None

    if evidence_id and evidence is None:
        return _missing_reference_answer(evidence_id, context)
    if finding_id and finding is None:
        return _missing_reference_answer(finding_id, context)

    relationship = "No explicit relationship was found."
    if evidence and finding and evidence.id in finding.evidence_ids:
        relationship = f"{finding.id} is explicitly supported by {evidence.id}."
    elif evidence:
        related_findings = [
            item for item in incident.findings if evidence.id in item.evidence_ids
        ]
        if related_findings:
            relationship = (
                f"{evidence.id} explicitly supports finding(s): "
                f"{', '.join(item.id for item in related_findings)}."
            )
    elif finding:
        relationship = (
            f"{finding.id} is explicitly supported by evidence: "
            f"{_join_or_none(finding.evidence_ids)}."
        )

    reference_id = evidence_id or finding_id
    protected = explain_graph_followup_protected(context.graph_snapshot, reference_id)
    return "\n".join(
        [
            relationship,
            f"Graph fact: {protected.answer.answer}",
            "Only explicit GraphSnapshot edges were followed; no relationship was inferred from free text.",
        ]
    )


def _decision_boundary_answer(context: ActiveAuthIncidentContext) -> str:
    incident = context.incident
    return "\n".join(
        [
            f"目前 Risk Level 為 {incident.risk_level}，Decision 為 {incident.decision}。",
            (
                "這筆事件是 possible_account_compromise candidate："
                "repeated authentication failures were followed by a successful login, "
                "so the system keeps it HIGH risk but MONITOR for analyst review."
            ),
            _simulated_decision_notice(),
            "This explanation does not change the deterministic Risk Level or Decision.",
        ]
    )


def _compromise_uncertainty_answer(context: ActiveAuthIncidentContext) -> str:
    incident = context.incident
    return "\n".join(
        [
            "不能只靠這份 evidence 宣稱帳號已確認被入侵。",
            (
                f"{incident.id} 顯示 repeated failures followed by login_success，"
                "這是 suspicious sequence, not confirmed compromise。"
            ),
            (
                "需要再查 successful login session、source_ip/device 是否可信、MFA 狀態、"
                "登入後是否有異常權限變更、資料存取或橫向移動。"
            ),
            _simulated_decision_notice(),
        ]
    )


def _investigation_answer(context: ActiveAuthIncidentContext) -> str:
    incident = context.incident
    response_lines = (
        incident.recommended_response
        if incident.recommended_response
        else [
            "Review the successful login session after repeated failures.",
            "Check whether the same source attempted other users.",
            "Preserve relevant authentication and session evidence.",
        ]
    )
    return "\n".join(
        [
            f"針對 {incident.id} / {incident.attack_type or incident.title}，建議先做：",
            *_bullet_lines(response_lines),
            (
                "再補查 MFA 狀態、登入後行為、privilege changes、異常資料存取、"
                "同 source_ip 是否攻擊其他 user。"
            ),
            "以上是 defensive investigation guidance；系統沒有宣稱已執行任何處置。",
        ]
    )


def _missing_reference_answer(reference_id: str, context: ActiveAuthIncidentContext) -> str:
    return (
        f"{reference_id} was not found in the active Mode 2 incident context. "
        f"Available evidence IDs: {_join_or_none(sorted(context.incident.evidence_bundle.available_ids))}. "
        f"Available finding IDs: {_join_or_none(finding.id for finding in context.incident.findings)}."
    )


def _primary_finding(incident: Incident) -> Finding | None:
    return incident.findings[0] if incident.findings else None


def _find_finding(incident: Incident, finding_id: str) -> Finding | None:
    return next((finding for finding in incident.findings if finding.id == finding_id), None)


def _format_evidence_summary(item: EvidenceItem) -> str:
    return f"{item.id} / {item.type}: {item.description} Value={_format_value(item.value)}"


def _followup_examples(
    evidence_ids: list[str],
    finding_ids: list[str],
    decision: str,
) -> list[str]:
    evidence_id = "EV-003" if "EV-003" in evidence_ids else (evidence_ids[0] if evidence_ids else "EV-001")
    finding_id = "F-001" if "F-001" in finding_ids else (finding_ids[0] if finding_ids else "F-001")
    return [
        f"{evidence_id} 是什麼意思？",
        f"{evidence_id} 和 {finding_id} 有什麼關係？",
        f"為什麼是 {decision}？",
        "這代表帳號已經被入侵了嗎？",
    ]


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return "None"
    return str(value)


def _extract_ids(text: str, prefix: str) -> list[str]:
    if prefix == "INC":
        pattern = r"\bINC-\d{8}-\d{3}\b"
    else:
        pattern = rf"\b{prefix}-\d{{3}}\b"
    return list(dict.fromkeys(match.upper() for match in re.findall(pattern, str(text or ""), re.IGNORECASE)))


def _contains_any(text: str, candidates: list[str]) -> bool:
    return any(candidate.casefold() in text for candidate in candidates)


def _bullet_lines(lines: list[str]) -> list[str]:
    return [f"- {line}" for line in lines]


def _join_or_none(values: Any) -> str:
    items = [str(value) for value in values if str(value).strip()]
    return ", ".join(items) if items else "None"


def _simulated_decision_notice() -> str:
    return "此 Decision 為模擬決策，不代表已執行真實封鎖、監控部署或其他實際處置。"
