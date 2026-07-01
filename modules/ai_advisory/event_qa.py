"""Event-aware advisory Q&A backend for v3.1.

This module answers questions about an already-built EvidenceGroundingBundle.
It is read-only and advisory-only: it does not route tools, retrieve knowledge,
build graph facts, write case memory, or alter official Risk Level / Decision.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from modules.ai_advisory.evidence_bundle import EvidenceGroundingBundle, GroundingCitation
from modules.ai_advisory.grounded_brief import GroundedBriefOfficialVerdict, LLMStatus
from modules.ai_advisory.llm_provider import (
    BaseLLMProvider,
    LLMProviderRequest,
    ProviderMode,
    ProviderStatus,
    build_default_provider,
)
from modules.ai_advisory.prompt_contract import PromptLanguage, build_soc_copilot_system_prompt

EVENT_AWARE_QA_SCHEMA_VERSION = "v3.1-event-aware-qa-result1"

_UNSAFE_QUESTION_PATTERNS = (
    re.compile(r"\b(exploit|poc|proof[- ]of[- ]concept|reverse shell)\b", re.I),
    re.compile(r"\b(traffic generation|load test|load testing|dos attack|ddos)\b", re.I),
    re.compile(r"\b(hping3|slowloris|wrk|ab -n|attack script)\b", re.I),
    re.compile(r"\b(update|deploy|configure|block|quarantine|isolate)\b.{0,50}\b(firewall|waf|edr|siem|soar)\b", re.I),
    re.compile(r"\b(reset|disable|lock|revoke|delete|remove|rotate)\b.{0,40}\b(account|password|credential|user|session)\b", re.I),
    re.compile(r"\b(change|override|lower|raise|set)\b.{0,40}\b(risk level|decision|verdict)\b", re.I),
    re.compile(r"(?:\u7522\u751f|\u751f\u6210|\u88fd\u4f5c|\u63d0\u4f9b).{0,20}(?:\u653b\u64ca\u6d41\u91cf|exploit|PoC)", re.I),
    re.compile(r"(?:\u58d3\u529b\u6e2c\u8a66|\u8ca0\u8f09\u6e2c\u8a66|\u653b\u64ca\u6d41\u91cf|\u6d41\u91cf\u6e2c\u8a66)", re.I),
    re.compile(r"(?:\u5c01\u9396|\u4fee\u6539|\u8a2d\u5b9a|\u90e8\u7f72).{0,30}(?:\u9632\u706b\u7246|firewall|WAF|EDR|SIEM|SOAR)", re.I),
    re.compile(r"(?:\u505c\u7528|\u91cd\u8a2d|\u64a4\u92b7|\u522a\u9664).{0,30}(?:\u5e33\u865f|\u5bc6\u78bc|\u6191\u8b49|session|\u4f7f\u7528\u8005|token)", re.I),
    re.compile(r"(?:\u6539\u5224\u5b9a|\u8986\u84cb\u98a8\u96aa|\u8986\u84cb\u5224\u5b9a|\u8b8a\u66f4\u5224\u5b9a|\u4fee\u6539\u5224\u5b9a|\u628a\s*Risk Level\s*\u6539\u6210\s*LOW)", re.I),
)
_ANSWER_UNSAFE_PATTERNS = _UNSAFE_QUESTION_PATTERNS + (
    re.compile(r"\bsimilar cases?\b.{0,80}\b(proves?|confirms?|are proof|is proof)\b", re.I),
    re.compile(r"\bgraph\b.{0,80}\b(detected|confirmed|is the detection source|was the detection source)\b", re.I),
    re.compile(r"(?:\u76f8\u4f3c\u6848\u4f8b|Similar Cases).{0,40}(?:\u8b49\u660e|\u78ba\u8a8d).{0,20}(?:\u5df2\u5165\u4fb5|\u5165\u4fb5|compromise)", re.I),
    re.compile(r"(?:Graph|\u5716\u8b5c).{0,30}(?:\u662f|\u4f5c\u70ba).{0,15}(?:\u5075\u6e2c\u4f86\u6e90|detection source)", re.I),
)



def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value.strip()


class EventAwareQARequest(BaseModel):
    """Question over an existing EvidenceGroundingBundle."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    question: str
    language: PromptLanguage = "en"
    bundle: EvidenceGroundingBundle
    provider: Any | None = Field(default=None, exclude=True)

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "question")


class EventAwareQAResult(BaseModel):
    """Guarded event-aware Q&A answer."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = EVENT_AWARE_QA_SCHEMA_VERSION
    answer: str
    citations: list[GroundingCitation] = Field(default_factory=list)
    provider_mode: ProviderMode
    provider_status: ProviderStatus
    llm_status: LLMStatus
    safety_findings: list[str] = Field(default_factory=list)
    official_verdict: GroundedBriefOfficialVerdict
    advisory_boundary: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    no_enforcement: bool = True

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "answer")


class _ProviderQAPayload(BaseModel):
    answer: str
    citation_ids: list[str] = Field(default_factory=list)

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "answer")


def answer_event_aware_question(
    request: EventAwareQARequest,
    provider: BaseLLMProvider | None = None,
) -> EventAwareQAResult:
    """Answer an active-context question with guarded advisory context."""

    unsafe_reason = _unsafe_question_reason(request.question)
    if unsafe_reason is not None:
        return _deterministic_result(
            request,
            provider_mode="disabled",
            provider_status="disabled",
            llm_status="not_used_deterministic_fallback",
            safety_findings=[unsafe_reason],
            refusal=True,
        )

    selected_provider = provider or request.provider or build_default_provider()
    generate = selected_provider.generate
    try:
        provider_response = generate(
            LLMProviderRequest(
                system_prompt=build_soc_copilot_system_prompt(request.language),
                user_prompt=_event_qa_user_prompt(request),
                temperature=0.0,
            )
        )
    except Exception:
        return _deterministic_result(
            request,
            provider_mode=getattr(selected_provider, "mode", "disabled"),
            provider_status="unavailable",
            llm_status="unavailable_fallback",
            safety_findings=[],
        )
    if not provider_response.ok:
        status: LLMStatus = (
            "not_used_deterministic_fallback"
            if provider_response.status == "disabled"
            else "unavailable_fallback"
        )
        return _deterministic_result(
            request,
            provider_mode=provider_response.mode,
            provider_status=provider_response.status,
            llm_status=status,
            safety_findings=[],
        )

    provider_result = _provider_payload_result(request, provider_response.content)
    if provider_result is None:
        return _deterministic_result(
            request,
            provider_mode=provider_response.mode,
            provider_status=provider_response.status,
            llm_status="invalid_json_fallback",
            safety_findings=["Provider output was invalid or missing known citations."],
        )
    payload, citations = provider_result
    unsafe_answer = _unsafe_answer_reason(payload.answer)
    if unsafe_answer is not None:
        return _deterministic_result(
            request,
            provider_mode=provider_response.mode,
            provider_status=provider_response.status,
            llm_status="blocked_by_guardrail",
            safety_findings=[unsafe_answer],
        )
    return EventAwareQAResult(
        answer=payload.answer,
        citations=citations,
        provider_mode=provider_response.mode,
        provider_status=provider_response.status,
        llm_status="used",
        safety_findings=[],
        official_verdict=_official_verdict(request.bundle),
        advisory_boundary=list(request.bundle.safety_boundary),
        human_review_required=True,
        no_enforcement=True,
    )


def _deterministic_result(
    request: EventAwareQARequest,
    *,
    provider_mode: ProviderMode,
    provider_status: ProviderStatus,
    llm_status: LLMStatus,
    safety_findings: list[str],
    refusal: bool = False,
) -> EventAwareQAResult:
    answer = (
        _refusal_answer(request.language)
        if refusal
        else _deterministic_answer(request.bundle, request.language)
    )
    return EventAwareQAResult(
        answer=answer,
        citations=_fallback_citations(request.bundle),
        provider_mode=provider_mode,
        provider_status=provider_status,
        llm_status=llm_status,
        safety_findings=safety_findings,
        official_verdict=_official_verdict(request.bundle),
        advisory_boundary=list(request.bundle.safety_boundary),
        human_review_required=True,
        no_enforcement=True,
    )


def _event_qa_user_prompt(request: EventAwareQARequest) -> str:
    return "\n".join(
        [
            "Answer the analyst question using only the EvidenceGroundingBundle.",
            "Return JSON with keys: answer, citation_ids.",
            "The answer must cite provided citation IDs and preserve all IDs exactly.",
            "Question:",
            request.question,
            "EvidenceGroundingBundle JSON:",
            request.bundle.model_dump_json(),
        ]
    )


def _provider_payload_result(
    request: EventAwareQARequest,
    content: str,
) -> tuple[_ProviderQAPayload, list[GroundingCitation]] | None:
    try:
        payload = _ProviderQAPayload.model_validate(json.loads(str(content or "")))
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None
    known = {citation.citation_id: citation for citation in request.bundle.citations}
    if not payload.citation_ids:
        return None
    if any(citation_id not in known for citation_id in payload.citation_ids):
        return None
    return payload, [known[citation_id] for citation_id in payload.citation_ids]


def _deterministic_answer(bundle: EvidenceGroundingBundle, language: PromptLanguage) -> str:
    if language == "zh-TW":
        return _deterministic_answer_zh(bundle)
    return _deterministic_answer_en(bundle)


def _deterministic_answer_en(bundle: EvidenceGroundingBundle) -> str:
    rule_ids = _join_or_none(bundle.official_detection.matched_rule_ids)
    evidence_ids = _join_or_none([item.source_id or item.citation_id for item in bundle.evidence_items])
    lines = [
        (
            "Official verdict is copied from deterministic policy: "
            f"Risk Level={bundle.official_verdict.risk_level or 'N/A'}, "
            f"Decision={bundle.official_verdict.decision or 'N/A'}."
        ),
        f"Rule IDs: {rule_ids}. Evidence IDs: {evidence_ids}.",
    ]
    if rule_ids == "None" and evidence_ids == "None":
        lines.append("No rule IDs or evidence IDs are available in the current bundle.")
    if bundle.evidence_gaps.missing_evidence:
        lines.append("Evidence gaps: " + "; ".join(bundle.evidence_gaps.missing_evidence) + ".")
    if bundle.rag_context:
        lines.append("RAG context is available as advisory knowledge only.")
    if bundle.similar_cases:
        cases = ", ".join(item.case_id for item in bundle.similar_cases)
        lines.append(f"Similar Cases are advisory comparisons, not proof: {cases}.")
    if bundle.graph_context:
        lines.append("Graph context is advisory and not a detection source.")
    lines.append("No real enforcement is performed. Human review is required.")
    return "\n".join(lines)


def _deterministic_answer_zh(bundle: EvidenceGroundingBundle) -> str:
    rule_ids = _join_or_none(bundle.official_detection.matched_rule_ids)
    evidence_ids = _join_or_none([item.source_id or item.citation_id for item in bundle.evidence_items])
    lines = [
        (
            "\u5b98\u65b9\u5224\u5b9a\u662f\u5f9e deterministic policy \u8907\u88fd\u800c\u4f86\uff1a"
            f"Risk Level={bundle.official_verdict.risk_level or 'N/A'}\uff0c"
            f"Decision={bundle.official_verdict.decision or 'N/A'}\u3002"
        ),
        f"Rule IDs\uff1a{rule_ids}\u3002Evidence IDs\uff1a{evidence_ids}\u3002",
    ]
    if rule_ids == "None" and evidence_ids == "None":
        lines.append("\u76ee\u524d bundle \u6c92\u6709\u53ef\u7528\u7684 rule IDs \u6216 evidence IDs\u3002")
    if bundle.evidence_gaps.missing_evidence:
        lines.append("\u8b49\u64da\u7f3a\u53e3\uff1a" + "\uff1b".join(bundle.evidence_gaps.missing_evidence) + "\u3002")
    if bundle.rag_context:
        lines.append("RAG context \u53ea\u80fd\u4f5c\u70ba advisory knowledge\u3002")
    if bundle.similar_cases:
        cases = "\uff0c".join(item.case_id for item in bundle.similar_cases)
        lines.append(f"Similar Cases \u662f advisory comparisons\uff0c\u4e0d\u662f compromise \u8b49\u660e\uff1a{cases}\u3002")
    if bundle.graph_context:
        lines.append("Graph context \u53ea\u80fd\u4f5c\u70ba advisory context\uff0c\u4e0d\u662f detection source\u3002")
    lines.append("\u4e0d\u6703\u57f7\u884c\u771f\u5be6 enforcement\uff1b\u9700\u8981 Human review\u3002")
    return "\n".join(lines)


def _refusal_answer(language: PromptLanguage) -> str:
    if language == "zh-TW":
        return (
            "\u6211\u4e0d\u80fd\u5354\u52a9 exploit\u3001PoC\u3001traffic generation\u3001load testing\u3001\u771f\u5be6 enforcement\uff0c"
            "\u4e5f\u4e0d\u80fd\u8986\u84cb deterministic Risk Level / Decision\u3002"
            "\u6211\u53ef\u4ee5\u63d0\u4f9b\u9632\u79a6\u6027\u7684\u8abf\u67e5\u8207\u8b49\u64da\u8907\u6838\u5efa\u8b70\u3002"
        )
    return (
        "I cannot assist with exploit, PoC, traffic generation, load testing, "
        "real enforcement, or overriding deterministic Risk Level / Decision. "
        "I can provide defensive investigation and evidence-review guidance."
    )


def _fallback_citations(bundle: EvidenceGroundingBundle) -> list[GroundingCitation]:
    ids = set(bundle.official_verdict.citation_ids or bundle.official_detection.citation_ids)
    ids.update(bundle.evidence_gaps.citation_ids)
    selected = [citation for citation in bundle.citations if citation.citation_id in ids]
    return selected or list(bundle.citations[:1])


def _official_verdict(bundle: EvidenceGroundingBundle) -> GroundedBriefOfficialVerdict:
    return GroundedBriefOfficialVerdict(
        risk_level=bundle.official_verdict.risk_level,
        decision=bundle.official_verdict.decision,
        simulated_decision=bundle.official_verdict.simulated_decision,
        authority=bundle.official_verdict.authority,
    )


def _unsafe_question_reason(question: str) -> str | None:
    for pattern in _UNSAFE_QUESTION_PATTERNS:
        if pattern.search(question):
            return "Unsafe question refused before provider call."
    return None


def _unsafe_answer_reason(answer: str) -> str | None:
    for pattern in _ANSWER_UNSAFE_PATTERNS:
        if pattern.search(answer):
            return "Provider answer blocked by advisory safety guardrail."
    return None


def _join_or_none(values: list[str]) -> str:
    clean = [str(value or "").strip() for value in values if str(value or "").strip()]
    return ", ".join(clean) if clean else "None"


__all__ = [
    "EVENT_AWARE_QA_SCHEMA_VERSION",
    "EventAwareQARequest",
    "EventAwareQAResult",
    "answer_event_aware_question",
]
