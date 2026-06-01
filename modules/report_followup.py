"""Report-aware follow-up helpers for existing incident/report data.

This module explains EV/F-ID references and report outcomes without re-running
detection, re-judging events, overriding Risk Level / Decision, claiming real
enforcement, or treating RAG/LLM output as detection authority.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from modules.answer_guardrails import AnswerSafetyReport, check_answer_safety
from modules.graph.explainers import explain_graph_reference
from modules.graph.types import GraphNodeKind, GraphSnapshot
from modules.rag_explainers import explain_report_question, explain_rule_question
from modules.rag_metadata import KnowledgeDocMetadata
from modules.rag_types import AnswerWithSources, SourceCitation
from modules.types import EvidenceItem, Finding, Incident

Intent = str

DOC_READING_REPORT = "knowledge/blue_team/report_explainer/reading_the_report.md"
DOC_RISK_DECISION = "knowledge/blue_team/report_explainer/risk_level_decision.md"
DOC_INVESTIGATION = "knowledge/blue_team/report_explainer/investigation_checklist.md"

DOCS_BY_INTENT = {
    "explain_evidence": [DOC_READING_REPORT],
    "explain_finding": [DOC_READING_REPORT],
    "why_risk": [DOC_RISK_DECISION],
    "why_decision": [DOC_RISK_DECISION],
    "next_steps": [DOC_INVESTIGATION],
    "ai_assist_disagreement": [DOC_RISK_DECISION],
    "read_report": [DOC_READING_REPORT],
    "unknown": [],
}

SAFETY_FALLBACK_SOURCE = SourceCitation(
    source="internal/answer_guardrails",
    kind="knowledge_doc",
    heading="Protected fallback",
    identifier="answer_guardrails",
)

SUGGESTIONS_BY_INTENT = {
    "explain_evidence": [
        "為什麼這個 evidence 會影響風險？",
        "我接下來要查什麼？",
    ],
    "explain_finding": [
        "這個 finding 參考了哪些 evidence？",
        "這個 finding 對應哪些調查步驟？",
    ],
    "why_risk": [
        "哪些 evidence 支持這個 Risk Level？",
        "這可能是誤報嗎？",
    ],
    "why_decision": [
        "HIGH 為什麼不一定等於 BLOCK？",
        "什麼情況下會升級成 BLOCK？",
    ],
    "next_steps": [
        "我要查哪些 log source？",
        "這可能是誤報嗎？",
        "是否需要保留 evidence？",
    ],
    "ai_assist_disagreement": [
        "Final Decision 和 AI Assist 誰優先？",
        "我該怎麼處理 AI 建議不同的情況？",
    ],
    "read_report": [
        "Evidence 區塊怎麼看？",
        "Risk Level 和 Decision 有什麼差別？",
    ],
    "unknown": [
        "這份報告怎麼看？",
        "我接下來要查什麼？",
    ],
}


class ProtectedExplanationResult(BaseModel):
    """Guardrail-reviewed explanation with fallback and safety details."""

    answer: AnswerWithSources
    safety_report: AnswerSafetyReport
    was_fallback: bool = False


def protect_answer_with_guardrails(
    answer: AnswerWithSources,
    known_evidence_ids: set[str] | None = None,
    known_finding_ids: set[str] | None = None,
    known_rule_ids: set[str] | None = None,
) -> ProtectedExplanationResult:
    """Return the answer if safe, otherwise a conservative protected fallback."""

    safety_report = check_answer_safety(
        answer,
        known_evidence_ids=known_evidence_ids,
        known_finding_ids=known_finding_ids,
        known_rule_ids=known_rule_ids,
    )
    if not safety_report.has_errors():
        return ProtectedExplanationResult(answer=answer, safety_report=safety_report)

    # Guardrail failures use conservative wording and never change report facts.
    fallback = AnswerWithSources(
        answer=(
            "此回答未通過安全檢查，因此改以保守說明回覆。請以原始報告證據、"
            "命中規則與人工複核為準；本系統不會執行真實封鎖，也不會讓 AI "
            "覆蓋最終判定。"
        ),
        sources=_fallback_sources(answer.sources),
        confidence="LOW",
        limitations=[
            "Original helper output failed deterministic AnswerGuardrails.",
            "Fallback does not change Risk Level, Decision, evidence, findings, or rules.",
        ],
    )
    return ProtectedExplanationResult(
        answer=fallback,
        safety_report=safety_report,
        was_fallback=True,
    )


def _fallback_sources(sources: list[SourceCitation]) -> list[SourceCitation]:
    """Preserve original citations and add deterministic safety provenance."""

    fallback_sources = list(sources)
    if not fallback_sources:
        return [SAFETY_FALLBACK_SOURCE]

    has_safety_source = any(
        citation.source == SAFETY_FALLBACK_SOURCE.source
        and citation.identifier == SAFETY_FALLBACK_SOURCE.identifier
        for citation in fallback_sources
    )
    if not has_safety_source:
        # Rewritten answers carry deterministic provenance for the safety boundary.
        fallback_sources.append(SAFETY_FALLBACK_SOURCE)

    return fallback_sources


def explain_report_followup_protected(
    question: str,
    metadata_items: list[KnowledgeDocMetadata],
    context: dict[str, object] | None = None,
    known_evidence_ids: set[str] | None = None,
    known_finding_ids: set[str] | None = None,
    known_rule_ids: set[str] | None = None,
) -> ProtectedExplanationResult:
    """Explain report questions with deterministic guardrail protection."""

    answer = explain_report_question(question, metadata_items, context=context)
    return protect_answer_with_guardrails(
        answer,
        known_evidence_ids=known_evidence_ids,
        known_finding_ids=known_finding_ids,
        known_rule_ids=known_rule_ids,
    )


def explain_rule_followup_protected(
    question: str,
    metadata_items: list[KnowledgeDocMetadata],
    rule_metadata: dict[str, dict[str, object]] | None = None,
    known_rule_ids: set[str] | None = None,
) -> ProtectedExplanationResult:
    """Explain rule questions without inventing rule authority or IDs."""

    answer = explain_rule_question(
        question,
        metadata_items,
        rule_metadata=rule_metadata,
    )
    return protect_answer_with_guardrails(answer, known_rule_ids=known_rule_ids)


def explain_graph_followup_protected(
    snapshot: GraphSnapshot,
    reference_id: str,
) -> ProtectedExplanationResult:
    """Explain graph references and protect the answer with guardrails."""

    answer = explain_graph_reference(snapshot, reference_id)
    return protect_answer_with_guardrails(
        answer,
        known_evidence_ids=_known_graph_ids(snapshot, GraphNodeKind.EVIDENCE),
        known_finding_ids=_known_graph_ids(snapshot, GraphNodeKind.FINDING),
        known_rule_ids=_known_rule_ids(snapshot),
    )


def classify_followup_intent(question: str) -> Intent:
    """Classify a follow-up question into deterministic report routes."""

    text = str(question or "").strip().lower()
    evidence_ids = extract_evidence_ids(text)
    finding_ids = extract_finding_ids(text)

    if evidence_ids:
        return "explain_evidence"

    if finding_ids:
        return "explain_finding"

    if any(term in text for term in ("ai assist", "llm", "ai 建議", "final decision")):
        if any(term in text for term in ("不一樣", "不同", "disagree", "disagreement")):
            return "ai_assist_disagreement"

    if any(term in text for term in ("接下來", "next", "next step", "查什麼", "checklist")):
        return "next_steps"

    if any(term in text for term in ("monitor", "block", "allow", "decision", "決策", "為什麼是")):
        return "why_decision"

    if any(term in text for term in ("risk", "high", "medium", "low", "風險", "risk level")):
        return "why_risk"

    if any(term in text for term in ("怎麼看", "報告", "report", "triage report")):
        return "read_report"

    return "unknown"


def extract_evidence_ids(text: str) -> list[str]:
    """Extract stable EV-ID references in first-seen order."""

    return _extract_stable_ids(r"EV-\d+", text)


def extract_finding_ids(text: str) -> list[str]:
    """Extract stable F-ID references in first-seen order."""

    return _extract_stable_ids(r"F-\d+", text)


def lookup_evidence(incident: Incident, evidence_id: str) -> EvidenceItem | None:
    """Look up an evidence item by exact normalized ID in an incident."""

    return incident.evidence_bundle.get(str(evidence_id or "").upper())


def lookup_finding(incident: Incident, finding_id: str) -> Finding | None:
    """Look up a finding by exact normalized ID in an incident."""

    normalized_id = str(finding_id or "").upper()
    return next((finding for finding in incident.findings if finding.id == normalized_id), None)


def suggest_followups(intent: str, incident: Incident | None = None) -> list[str]:
    """Return static follow-up suggestions for the classified intent."""

    suggestions = SUGGESTIONS_BY_INTENT.get(intent, SUGGESTIONS_BY_INTENT["unknown"])
    if incident is None:
        return list(suggestions)

    if intent in ("why_decision", "why_risk"):
        return [*suggestions, f"這個 {incident.risk_level}/{incident.decision} 組合代表什麼？"]

    return list(suggestions)


def answer_report_followup(question: str, incident: Incident) -> dict[str, object]:
    """Assemble a deterministic follow-up answer from existing incident data."""

    intent = classify_followup_intent(question)
    evidence_ids = extract_evidence_ids(question)
    finding_ids = extract_finding_ids(question)
    referenced_evidence: list[str] = []
    referenced_findings: list[str] = []
    confidence = "medium"

    if intent == "explain_evidence":
        answer, referenced_evidence, confidence = _answer_evidence_lookup(
            incident, evidence_ids
        )
    elif intent == "explain_finding":
        answer, referenced_findings, referenced_evidence, confidence = _answer_finding_lookup(
            incident, finding_ids
        )
    elif intent == "why_risk":
        answer = _answer_why_risk(incident)
        referenced_findings = [finding.id for finding in incident.findings]
        confidence = "high"
    elif intent == "why_decision":
        answer = _answer_why_decision(incident)
        referenced_findings = [finding.id for finding in incident.findings]
        confidence = "high"
    elif intent == "next_steps":
        answer = _answer_next_steps(incident)
        referenced_findings = [finding.id for finding in incident.findings]
        confidence = "high"
    elif intent == "ai_assist_disagreement":
        answer = _answer_ai_assist_disagreement(incident)
        confidence = "medium"
    elif intent == "read_report":
        answer = _answer_read_report(incident)
        confidence = "high"
    else:
        answer = (
            "我可以根據目前 Incident、Finding、Evidence 說明這份報告，但不會重新判定風險或改變決策。"
            "請指定 EV-ID、F-ID，或詢問 Risk Level、Decision、下一步調查。"
        )
        confidence = "low"

    return {
        "intent": intent,
        "answer": answer,
        "referenced_evidence": referenced_evidence,
        "referenced_findings": referenced_findings,
        "referenced_docs": DOCS_BY_INTENT.get(intent, []),
        "suggested_followups": suggest_followups(intent, incident),
        "confidence": confidence,
    }


def _extract_stable_ids(pattern: str, text: str) -> list[str]:
    """Normalize matched stable IDs while preserving first-seen order."""

    seen = set()
    extracted = []
    for match in re.findall(pattern, str(text or ""), flags=re.IGNORECASE):
        normalized = match.upper()
        if normalized not in seen:
            extracted.append(normalized)
            seen.add(normalized)
    return extracted


def _known_graph_ids(snapshot: GraphSnapshot, kind: GraphNodeKind) -> set[str]:
    return {node.id for node in snapshot.nodes if node.kind == kind}


def _known_rule_ids(snapshot: GraphSnapshot) -> set[str]:
    return {
        node.id.removeprefix("DETECTION_RULE:")
        for node in snapshot.nodes
        if node.kind == GraphNodeKind.DETECTION_RULE
    }


def _answer_evidence_lookup(
    incident: Incident,
    evidence_ids: list[str],
) -> tuple[str, list[str], str]:
    """Explain explicitly requested evidence IDs without guessing missing items."""

    if not evidence_ids:
        return (
            "請提供 EV-ID，例如 EV-003。我會只解釋目前報告中已存在的 evidence。",
            [],
            "insufficient",
        )

    answer_parts = []
    referenced = []
    missing = []
    for evidence_id in evidence_ids:
        item = lookup_evidence(incident, evidence_id)
        if item is None:
            missing.append(evidence_id)
            continue

        referenced.append(item.id)
        value_text = f" value={item.value!r}" if item.value is not None else ""
        answer_parts.append(
            f"{item.id} 是目前 Incident 的 evidence，type={item.type}。"
            f"{item.description}{value_text}。"
        )

    if missing:
        answer_parts.append(
            f"找不到 {', '.join(missing)}；我不會替不存在的 evidence 補內容。"
        )

    confidence = "high" if referenced and not missing else "insufficient"
    return " ".join(answer_parts), referenced, confidence


def _answer_finding_lookup(
    incident: Incident,
    finding_ids: list[str],
) -> tuple[str, list[str], list[str], str]:
    """Explain explicitly requested finding IDs and their linked evidence."""

    if not finding_ids:
        return (
            "請提供 F-ID，例如 F-001。我會只解釋目前報告中已存在的 finding。",
            [],
            [],
            "insufficient",
        )

    answer_parts = []
    referenced_findings = []
    referenced_evidence = []
    missing = []
    for finding_id in finding_ids:
        finding = lookup_finding(incident, finding_id)
        if finding is None:
            missing.append(finding_id)
            continue

        referenced_findings.append(finding.id)
        referenced_evidence.extend(finding.evidence_ids)
        answer_parts.append(
            f"{finding.id} 是 {finding.finding_type}，status={finding.status}，"
            f"risk={finding.risk_level}，decision={finding.decision}。"
            f"它引用 evidence: {', '.join(finding.evidence_ids) or 'none'}。"
        )

    if missing:
        answer_parts.append(f"找不到 {', '.join(missing)}。")

    return (
        " ".join(answer_parts),
        referenced_findings,
        _dedupe(referenced_evidence),
        "high" if referenced_findings and not missing else "insufficient",
    )


def _answer_why_risk(incident: Incident) -> str:
    """Explain the existing deterministic Risk Level without recalculating it."""

    evidence_count = len(incident.evidence_bundle.items)
    return (
        f"目前報告的 Risk Level 是 {incident.risk_level}。"
        f"這是根據既有 Incident / Finding / Evidence 的 deterministic verdict 說明，"
        f"包含 {len(incident.findings)} 個 finding 和 {evidence_count} 個 evidence。"
        "這個回答只解釋報告內容，不重新評分。"
    )


def _answer_why_decision(incident: Incident) -> str:
    """Explain the existing simulated Decision without changing it."""

    return (
        f"目前 Final Decision 是 {incident.decision}。"
        "possible_account_compromise 代表可疑但尚未確認的 compromise；"
        "v1.3 以 MONITOR 表示需要 analyst review，而不是直接執行 BLOCK。"
        f"{incident.simulation_notice}"
    )


def _answer_next_steps(incident: Incident) -> str:
    """Suggest analyst review steps without claiming real enforcement."""

    source_ips = _evidence_values_by_type(incident, "same_source_ip")
    users = _evidence_values_by_type(incident, "same_user")
    targets = _evidence_values_by_type(incident, "same_target")
    focus = ", ".join([*source_ips, *users, *targets]) or incident.id
    return (
        "建議先 review successful login session、檢查同一 source_ip 是否嘗試其他 user、"
        "比對 authentication log 與 session activity，並保留相關 evidence。"
        f"本次調查焦點: {focus}。"
    )


def _answer_ai_assist_disagreement(incident: Incident) -> str:
    """Explain that AI assist is advisory and cannot override final decisions."""

    return (
        f"若 AI Assist 與 Final Decision 不一致，仍以 deterministic Final Decision "
        f"{incident.decision} 為準。AI Assist 是 advisory，不會覆蓋 Risk Level 或 Decision。"
    )


def _answer_read_report(incident: Incident) -> str:
    return (
        "這份 Security Triage Report 可以先看 Quick Verdict，再看 Summary、Evidence、"
        "Risk Level、Decision、Recommended Response 和 Simulation Notice。"
        f"目前 Incident 是 {incident.id}，decision={incident.decision}。"
    )


def _evidence_values_by_type(incident: Incident, evidence_type: str) -> list[str]:
    values = []
    for item in incident.evidence_bundle.items:
        if item.type == evidence_type and item.value is not None:
            values.append(str(item.value))
    return values


def _dedupe(values: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return deduped
