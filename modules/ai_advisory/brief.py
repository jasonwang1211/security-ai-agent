"""Deterministic AI Analyst Brief backend for v2.7-G.

Builds a structured advisory brief from already-computed deterministic facts.
This module is pure backend logic: it does not call LLMs, RAG, Ollama, network
clients, Streamlit, graph builders, draft writers, databases, or enforcement
systems. It never changes Risk Level or Decision and never emits authoritative
fields named ``risk_level`` or ``decision``.
"""

from __future__ import annotations

from modules.output_language import (
    OUTPUT_LANGUAGE_BILINGUAL,
    OUTPUT_LANGUAGE_EN,
    OUTPUT_LANGUAGE_ZH_TW,
    normalize_output_language,
)

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
    "no real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is executed; "
    "no exploit, PoC, or traffic generation is provided; human review is required "
    "before operational action or promotion."
)

AI_ANALYST_BRIEF_BOUNDARY_ZH_TW = (
    "AI Analyst Brief 是確定性建議脈絡，不是最終判決。偵測是 rule-based；"
    "Risk Level 與 Decision 是 deterministic；BLOCK / MONITOR / ALLOW 是 simulated；"
    "AI advisory 不會覆蓋最終判定；不執行真實 firewall、WAF、EDR、account、cloud、"
    "SIEM 或 SOAR action；不提供 exploit、PoC 或 traffic generation；任何操作、案例提升或"
    "知識提升前都需要 human review。"
)

AI_ANALYST_BRIEF_BOUNDARY_BILINGUAL = (
    f"{AI_ANALYST_BRIEF_BOUNDARY_ZH_TW} / AI Analyst Brief is deterministic advisory "
    "context only; no real enforcement, exploit, PoC, or traffic generation; it does not "
    "override the final verdict."
)


def build_ai_analyst_brief(
    brief_input: AIAnalystBriefInput, language: str | None = OUTPUT_LANGUAGE_EN
) -> AIAnalystBrief:
    """Build a deterministic, side-effect-free AI Analyst Brief.

    ``brief_input`` is read but never mutated. If an ``EvidenceGapAnalysis`` is
    supplied, its sections are reused; otherwise the existing deterministic gap
    analyzer is called with the nested advisory input. No LLM/RAG/network/file
    access or writes are performed.
    """

    output_language = normalize_output_language(language)
    advisory_input = brief_input.advisory_input
    evidence_gap = brief_input.evidence_gap or analyze_evidence_gap(
        advisory_input, language=output_language
    )
    scenario = _classify_scenario(advisory_input)

    return AIAnalystBrief(
        what_happened=_what_happened(advisory_input, scenario, output_language),
        why_it_matters=_why_it_matters(scenario, output_language),
        deterministic_verdict=_deterministic_verdict(advisory_input, output_language),
        advisory_summary=_advisory_summary(brief_input, evidence_gap, output_language),
        evidence_gap_summary=_evidence_gap_summary(evidence_gap),
        recommended_next_steps=_recommended_next_steps(evidence_gap, output_language),
        unsafe_assumptions=list(evidence_gap.unsafe_assumptions),
        safety_boundary=_brief_boundary(output_language),
        llm_status="not_used",
        source="deterministic_ai_analyst_brief",
    )


def _line(zh: str, en: str, language: str) -> str:
    if language == OUTPUT_LANGUAGE_ZH_TW:
        return zh
    if language == OUTPUT_LANGUAGE_BILINGUAL:
        return f"{zh} / {en}"
    return en


def _brief_boundary(language: str) -> str:
    if language == OUTPUT_LANGUAGE_ZH_TW:
        return AI_ANALYST_BRIEF_BOUNDARY_ZH_TW
    if language == OUTPUT_LANGUAGE_BILINGUAL:
        return AI_ANALYST_BRIEF_BOUNDARY_BILINGUAL
    return AI_ANALYST_BRIEF_BOUNDARY


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


def _what_happened(
    advisory_input: AIAdvisoryInput, scenario: str, language: str
) -> list[str]:
    lines: list[str] = []
    rule_text = _joined(advisory_input.matched_rule_ids)

    if scenario == "command_injection":
        lines.append(
            _line(
                f"規則式偵測命中 Command Injection 模式{_with_rule_suffix(rule_text)}。",
                f"Rule-based detection matched Command Injection pattern(s){_with_rule_suffix(rule_text)}.",
                language,
            )
        )
    elif scenario == "sql_injection":
        lines.append(
            _line(
                f"規則式偵測命中 SQL Injection 模式{_with_rule_suffix(rule_text)}。",
                f"Rule-based detection matched SQL Injection pattern(s){_with_rule_suffix(rule_text)}.",
                language,
            )
        )
    elif scenario == "authentication_incident":
        if advisory_input.finding_type:
            lines.append(
                _line(
                    f"規則式分析辨識 authentication finding：{advisory_input.finding_type}。",
                    f"Rule-based analysis identified authentication finding: {advisory_input.finding_type}.",
                    language,
                )
            )
        else:
            lines.append(
                _line(
                    "規則式分析辨識多次 failed login attempts 後出現 successful login。",
                    "Rule-based analysis identified failed login attempts followed by a successful login.",
                    language,
                )
            )
    else:
        label = advisory_input.attack_type or advisory_input.finding_type or advisory_input.event_kind
        lines.append(
            _line(
                f"規則式分析針對此脈絡產生建議摘要：{label}。",
                f"Rule-based analysis produced an advisory brief for: {label}.",
                language,
            )
        )

    if advisory_input.matched_signatures:
        signatures = _joined(advisory_input.matched_signatures)
        lines.append(
            _line(
                f"命中的特徵：{signatures}。",
                f"Matched signature(s): {signatures}.",
                language,
            )
        )
    if advisory_input.evidence_labels:
        labels = _joined(advisory_input.evidence_labels)
        lines.append(
            _line(
                f"結構化證據標籤：{labels}。",
                f"Structured evidence label(s): {labels}.",
                language,
            )
        )
    if advisory_input.incident_id:
        lines.append(
            _line(
                f"目前 incident context：{advisory_input.incident_id}。",
                f"Current incident context: {advisory_input.incident_id}.",
                language,
            )
        )
    return lines


def _why_it_matters(scenario: str, language: str) -> list[str]:
    if scenario == "command_injection":
        return [
            _line(
                "Command Injection 模式可能代表嘗試讓伺服器執行 operating-system commands。",
                "Command Injection patterns may indicate an attempt to make the server execute operating-system commands.",
                language,
            ),
            _line(
                "此命中對調查很重要，但不代表命令已成功執行。",
                "The match is important for investigation, but successful command execution is not proven by the match alone.",
                language,
            ),
        ]
    if scenario == "sql_injection":
        return [
            _line(
                "SQL Injection 模式可能代表嘗試操控後端 database queries。",
                "SQL Injection patterns may indicate an attempt to manipulate backend database queries.",
                language,
            ),
            _line(
                "此命中對調查很重要，但 data access、exfiltration 或 database compromise 不會只因 payload 成立。",
                "The match is important for investigation, but data access, exfiltration, or database compromise is not proven by the payload alone.",
                language,
            ),
        ]
    if scenario == "authentication_incident":
        return [
            _line(
                "failure-then-success authentication sequence 具可疑性，因為可能符合 account-takeover behavior。",
                "A failure-then-success authentication sequence is suspicious because it can match account-takeover behavior.",
                language,
            ),
            _line(
                "宣稱 confirmed account compromise 前，需要 identity 與 session corroboration。",
                "The sequence needs identity and session corroboration before claiming confirmed account compromise.",
                language,
            ),
        ]
    return [
        _line(
            "確定性 finding 提供 analyst 可複核的結構化起點。",
            "The deterministic finding gives analysts a structured starting point for review.",
            language,
        ),
        _line(
            "宣稱 real impact 或 compromise 前，rule 或 pattern match 仍需佐證。",
            "A rule or pattern match should be corroborated before claiming real impact or compromise.",
            language,
        ),
    ]


def _deterministic_verdict(advisory_input: AIAdvisoryInput, language: str) -> list[str]:
    lines = [
        _line(
            f"偵測來源：{advisory_input.detection_source}（rule-based，不是 AI）。",
            f"Detection source: {advisory_input.detection_source} (rule-based, not AI).",
            language,
        ),
        _line(
            "Risk Level 與 Decision 由 deterministic pipeline 產生，不是由此 advisory brief 決定。",
            "Risk Level and Decision are produced by the deterministic pipeline, not by this advisory brief.",
            language,
        ),
    ]
    if advisory_input.risk_label:
        lines.append(
            _line(
                f"Deterministic Risk label context：{advisory_input.risk_label}。",
                f"Deterministic Risk label context: {advisory_input.risk_label}.",
                language,
            )
        )
    if advisory_input.decision_label:
        lines.append(
            _line(
                f"Deterministic simulated Decision label context：{advisory_input.decision_label}。",
                f"Deterministic simulated Decision label context: {advisory_input.decision_label}.",
                language,
            )
        )
    lines.append(
        _line(
            "BLOCK / MONITOR / ALLOW 只是 simulated decisions。",
            "BLOCK / MONITOR / ALLOW are simulated decisions only.",
            language,
        )
    )
    return lines


def _advisory_summary(
    brief_input: AIAnalystBriefInput,
    evidence_gap: EvidenceGapAnalysis,
    language: str,
) -> list[str]:
    lines = [
        _line(
            "AI advisory 只彙整 deterministic facts 與 evidence gaps；不覆蓋 final verdict。",
            "AI advisory summarizes deterministic facts and evidence gaps; it does not override the final verdict.",
            language,
        ),
        _line(
            "任何 operational action、case promotion 或 knowledge promotion 前都需要 human review。",
            "Human review is required before operational action, case promotion, or knowledge promotion.",
            language,
        ),
    ]
    if brief_input.run_mode:
        lines.append(
            _line(
                f"分析模式脈絡：{brief_input.run_mode}。",
                f"Analysis run mode context: {brief_input.run_mode}.",
                language,
            )
        )
    if brief_input.similar_case_ids:
        case_ids = _joined(brief_input.similar_case_ids)
        lines.append(
            _line(
                f"核准相似案例脈絡：{case_ids}。",
                f"Approved similar-case context: {case_ids}.",
                language,
            )
        )
    if brief_input.graph_relation_summary:
        lines.append(
            _line(
                f"Graph relationship context available：{_joined(brief_input.graph_relation_summary)}。",
                f"Graph relationship context available: {_joined(brief_input.graph_relation_summary)}.",
                language,
            )
        )
    if brief_input.case_draft_status:
        lines.append(
            _line(
                f"Case draft context：{brief_input.case_draft_status}。",
                f"Case draft context: {brief_input.case_draft_status}.",
                language,
            )
        )
    if evidence_gap.confirmed_facts:
        lines.append(
            _line(
                f"Evidence-gap source fact：{evidence_gap.confirmed_facts[0]}",
                f"Evidence-gap source fact: {evidence_gap.confirmed_facts[0]}",
                language,
            )
        )
    return lines


def _evidence_gap_summary(evidence_gap: EvidenceGapAnalysis) -> list[str]:
    return list(evidence_gap.missing_evidence)


def _recommended_next_steps(evidence_gap: EvidenceGapAnalysis, language: str) -> list[str]:
    checks = list(evidence_gap.recommended_checks)
    checks.append(
        _line(
            "採取 operational action 前，先複核 deterministic report 與 evidence。",
            "Review the deterministic report and evidence before taking operational action.",
            language,
        )
    )
    checks.append(
        _line(
            "任何 case draft 或 knowledge promotion 都要保留 human review gate。",
            "Keep any case draft or knowledge promotion behind human review.",
            language,
        )
    )
    return list(dict.fromkeys(checks))


def _joined(values: list[str]) -> str:
    return ", ".join(str(value) for value in values if str(value).strip()) or "None"


def _with_rule_suffix(rule_text: str) -> str:
    return f" ({rule_text})" if rule_text != "None" else ""


__all__ = ["AI_ANALYST_BRIEF_BOUNDARY", "build_ai_analyst_brief"]
