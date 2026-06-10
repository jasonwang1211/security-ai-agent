"""Deterministic AI Analyst Brief backend for v2.7-G.

Builds a structured advisory brief from already-computed deterministic facts.
This module is pure backend logic: it does not call LLMs, RAG, Ollama, network
clients, Streamlit, graph builders, draft writers, databases, or enforcement
systems. It never changes Risk Level or Decision and never emits authoritative
fields named ``risk_level`` or ``decision``.
"""

from __future__ import annotations

from .evidence_gap import analyze_evidence_gap
from .types import (
    AIAdvisoryInput,
    AIAnalystBrief,
    AIAnalystBriefInput,
    EvidenceGapAnalysis,
)

AI_ANALYST_BRIEF_BOUNDARY = (
    "AI Analyst Brief is deterministic advisory context only. Detection is "
    "rule-based; Risk Level and Decision are deterministic; BLOCK / MONITOR / "
    "ALLOW are simulated; AI advisory does not override the final verdict; "
    "human review is required before operational action or promotion."
)


def build_ai_analyst_brief(brief_input: AIAnalystBriefInput) -> AIAnalystBrief:
    """Build a deterministic, side-effect-free AI Analyst Brief.

    ``brief_input`` is read but never mutated. If an ``EvidenceGapAnalysis`` is
    supplied, its sections are reused; otherwise the existing deterministic gap
    analyzer is called with the nested advisory input. No LLM/RAG/network/file
    access or writes are performed.
    """

    advisory_input = brief_input.advisory_input
    evidence_gap = brief_input.evidence_gap or analyze_evidence_gap(advisory_input)
    scenario = _classify_scenario(advisory_input)

    return AIAnalystBrief(
        what_happened=_what_happened(advisory_input, scenario),
        why_it_matters=_why_it_matters(scenario),
        deterministic_verdict=_deterministic_verdict(advisory_input),
        advisory_summary=_advisory_summary(brief_input, evidence_gap),
        evidence_gap_summary=_evidence_gap_summary(evidence_gap),
        recommended_next_steps=_recommended_next_steps(evidence_gap),
        unsafe_assumptions=list(evidence_gap.unsafe_assumptions),
        safety_boundary=AI_ANALYST_BRIEF_BOUNDARY,
        llm_status="not_used",
        source="deterministic_ai_analyst_brief",
    )


def _classify_scenario(advisory_input: AIAdvisoryInput) -> str:
    haystack = " ".join(
        value
        for value in (
            advisory_input.event_kind,
            advisory_input.attack_type,
            advisory_input.finding_type,
        )
        if value
    ).casefold()
    rule_ids = [rule_id.strip().upper() for rule_id in advisory_input.matched_rule_ids]

    if "command injection" in haystack or any(rule_id.startswith("CMD-") for rule_id in rule_ids):
        return "command_injection"
    if "sql injection" in haystack or any(rule_id.startswith("SQLI-") for rule_id in rule_ids):
        return "sql_injection"
    if (
        "account compromise" in haystack
        or "authentication" in haystack
        or "auth_" in haystack
        or any(rule_id.startswith("AUTH-") for rule_id in rule_ids)
    ):
        return "authentication_incident"
    return "generic"


def _what_happened(advisory_input: AIAdvisoryInput, scenario: str) -> list[str]:
    lines: list[str] = []
    rule_text = _joined(advisory_input.matched_rule_ids)

    if scenario == "command_injection":
        lines.append(
            f"Rule-based detection matched Command Injection pattern(s){_with_rule_suffix(rule_text)}."
        )
    elif scenario == "sql_injection":
        lines.append(
            f"Rule-based detection matched SQL Injection pattern(s){_with_rule_suffix(rule_text)}."
        )
    elif scenario == "authentication_incident":
        if advisory_input.finding_type:
            lines.append(
                f"Rule-based analysis identified authentication finding: {advisory_input.finding_type}."
            )
        else:
            lines.append(
                "Rule-based analysis identified failed login attempts followed by a successful login."
            )
    else:
        label = advisory_input.attack_type or advisory_input.finding_type or advisory_input.event_kind
        lines.append(f"Rule-based analysis produced an advisory brief for: {label}.")

    if advisory_input.matched_signatures:
        lines.append(f"Matched signature(s): {_joined(advisory_input.matched_signatures)}.")
    if advisory_input.evidence_labels:
        lines.append(f"Structured evidence label(s): {_joined(advisory_input.evidence_labels)}.")
    if advisory_input.incident_id:
        lines.append(f"Current incident context: {advisory_input.incident_id}.")
    return lines


def _why_it_matters(scenario: str) -> list[str]:
    if scenario == "command_injection":
        return [
            "Command Injection patterns may indicate an attempt to make the server execute operating-system commands.",
            "The match is important for investigation, but successful command execution is not proven by the match alone.",
        ]
    if scenario == "sql_injection":
        return [
            "SQL Injection patterns may indicate an attempt to manipulate backend database queries.",
            "The match is important for investigation, but data access, exfiltration, or database compromise is not proven by the payload alone.",
        ]
    if scenario == "authentication_incident":
        return [
            "A failure-then-success authentication sequence is suspicious because it can match account-takeover behavior.",
            "The sequence needs identity and session corroboration before claiming confirmed account compromise.",
        ]
    return [
        "The deterministic finding gives analysts a structured starting point for review.",
        "A rule or pattern match should be corroborated before claiming real impact or compromise.",
    ]


def _deterministic_verdict(advisory_input: AIAdvisoryInput) -> list[str]:
    lines = [
        f"Detection source: {advisory_input.detection_source} (rule-based, not AI).",
        "Risk Level and Decision are produced by the deterministic pipeline, not by this advisory brief.",
    ]
    if advisory_input.risk_label:
        lines.append(f"Deterministic Risk label context: {advisory_input.risk_label}.")
    if advisory_input.decision_label:
        lines.append(
            f"Deterministic simulated Decision label context: {advisory_input.decision_label}."
        )
    lines.append("BLOCK / MONITOR / ALLOW are simulated decisions only.")
    return lines


def _advisory_summary(
    brief_input: AIAnalystBriefInput,
    evidence_gap: EvidenceGapAnalysis,
) -> list[str]:
    lines = [
        "AI advisory summarizes deterministic facts and evidence gaps; it does not override the final verdict.",
        "Human review is required before operational action, case promotion, or knowledge promotion.",
    ]
    if brief_input.run_mode:
        lines.append(f"Analysis run mode context: {brief_input.run_mode}.")
    if brief_input.similar_case_ids:
        lines.append(f"Approved similar-case context: {_joined(brief_input.similar_case_ids)}.")
    if brief_input.graph_relation_summary:
        lines.append(
            f"Graph relationship context available: {_joined(brief_input.graph_relation_summary)}."
        )
    if brief_input.case_draft_status:
        lines.append(f"Case draft context: {brief_input.case_draft_status}.")
    if evidence_gap.confirmed_facts:
        lines.append(f"Evidence-gap source fact: {evidence_gap.confirmed_facts[0]}")
    return lines


def _evidence_gap_summary(evidence_gap: EvidenceGapAnalysis) -> list[str]:
    return list(evidence_gap.missing_evidence)


def _recommended_next_steps(evidence_gap: EvidenceGapAnalysis) -> list[str]:
    checks = list(evidence_gap.recommended_checks)
    checks.append("Review the deterministic report and evidence before taking operational action.")
    checks.append("Keep any case draft or knowledge promotion behind human review.")
    return list(dict.fromkeys(checks))


def _joined(values: list[str]) -> str:
    return ", ".join(str(value) for value in values if str(value).strip()) or "None"


def _with_rule_suffix(rule_text: str) -> str:
    return f" ({rule_text})" if rule_text != "None" else ""


__all__ = ["AI_ANALYST_BRIEF_BOUNDARY", "build_ai_analyst_brief"]
