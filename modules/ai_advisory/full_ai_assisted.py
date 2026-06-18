"""Full AI-assisted advisory result contract for v3.1.

The API wraps optional provider output with the existing evidence-grounded
brief schema and guardrails. Provider output is never allowed to own the
official Risk Level / Decision.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from modules.ai_advisory.evidence_bundle import (
    EvidenceGroundingBundle,
    GraphGroundingItem,
    GroundingCitation,
    RetrievalGroundingItem,
    SimilarCaseGroundingItem,
)
from modules.ai_advisory.grounded_brief import (
    GroundedAnalystBrief,
    GroundedBriefItem,
    GroundedBriefOfficialVerdict,
    LLMStatus,
    build_deterministic_grounded_brief,
    generate_grounded_analyst_brief,
)
from modules.ai_advisory.llm_provider import (
    BaseLLMProvider,
    LLMProviderRequest,
    ProviderMode,
    ProviderStatus,
    build_default_provider,
)
from modules.ai_advisory.prompt_contract import (
    PromptLanguage,
    build_grounded_brief_user_prompt,
    build_soc_copilot_system_prompt,
)

FULL_AI_ASSISTED_SCHEMA_VERSION = "v3.1-full-ai-assisted-result1"
GuardrailStatus = Literal["passed", "fallback", "blocked", "not_run"]


class FullAiAssistedRequest(BaseModel):
    """Request for guarded full AI-assisted advisory generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    bundle: EvidenceGroundingBundle
    language: PromptLanguage = "en"
    provider: Any | None = Field(default=None, exclude=True)


class FullAiAssistedResult(BaseModel):
    """Validated result safe for backend callers, UI rendering, and export."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = FULL_AI_ASSISTED_SCHEMA_VERSION
    official_verdict: GroundedBriefOfficialVerdict
    provider_mode: ProviderMode
    provider_status: ProviderStatus
    llm_status: LLMStatus
    guardrail_status: GuardrailStatus
    generated_summary: list[GroundedBriefItem] = Field(default_factory=list)
    generated_investigation_plan: list[GroundedBriefItem] = Field(default_factory=list)
    grounded_citations: list[GroundingCitation] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    unsafe_assumptions: list[str] = Field(default_factory=list)
    rag_sources: list[dict[str, Any]] = Field(default_factory=list)
    similar_case_context: list[str] = Field(default_factory=list)
    graph_context: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    no_enforcement: bool = True
    advisory_boundary: list[str] = Field(default_factory=list)


def run_full_ai_assisted(
    request: FullAiAssistedRequest,
    provider: BaseLLMProvider | None = None,
) -> FullAiAssistedResult:
    """Run optional AI generation and always return a guarded advisory result."""

    selected_provider = provider or request.provider or build_default_provider()
    generate = selected_provider.generate
    try:
        provider_response = generate(
            LLMProviderRequest(
                system_prompt=build_soc_copilot_system_prompt(request.language),
                user_prompt=build_grounded_brief_user_prompt(request.bundle, request.language),
                temperature=0.0,
            )
        )
    except Exception:
        return _result_from_brief(
            build_deterministic_grounded_brief(request.bundle, "unavailable_fallback"),
            request.bundle,
            provider_mode=getattr(selected_provider, "mode", "disabled"),
            provider_status="unavailable",
            guardrail_status="not_run",
        )
    if not provider_response.ok:
        status: LLMStatus = (
            "not_used_deterministic_fallback"
            if provider_response.status == "disabled"
            else "unavailable_fallback"
        )
        return _result_from_brief(
            build_deterministic_grounded_brief(request.bundle, status),
            request.bundle,
            provider_mode=provider_response.mode,
            provider_status=provider_response.status,
            guardrail_status="not_run",
        )

    brief = generate_grounded_analyst_brief(
        request.bundle,
        llm_client=lambda _prompt: provider_response.content,
    )
    return _result_from_brief(
        brief,
        request.bundle,
        provider_mode=provider_response.mode,
        provider_status=provider_response.status,
        guardrail_status=_guardrail_status_from_llm_status(brief.llm_status),
    )


def _guardrail_status_from_llm_status(llm_status: LLMStatus) -> GuardrailStatus:
    if llm_status == "used":
        return "passed"
    if llm_status == "blocked_by_guardrail":
        return "blocked"
    return "fallback"


def _result_from_brief(
    brief: GroundedAnalystBrief,
    bundle: EvidenceGroundingBundle,
    *,
    provider_mode: ProviderMode,
    provider_status: ProviderStatus,
    guardrail_status: GuardrailStatus,
) -> FullAiAssistedResult:
    return FullAiAssistedResult(
        official_verdict=brief.official_verdict,
        provider_mode=provider_mode,
        provider_status=provider_status,
        llm_status=brief.llm_status,
        guardrail_status=guardrail_status,
        generated_summary=list(brief.executive_summary),
        generated_investigation_plan=list(brief.recommended_next_steps),
        grounded_citations=list(brief.citations),
        evidence_gaps=list(bundle.evidence_gaps.missing_evidence),
        unsafe_assumptions=list(bundle.evidence_gaps.unsafe_assumptions),
        rag_sources=_rag_sources(bundle.rag_context),
        similar_case_context=_similar_case_context(bundle.similar_cases),
        graph_context=_graph_context(bundle.graph_context),
        human_review_required=True,
        no_enforcement=True,
        advisory_boundary=list(brief.safety_boundary),
    )


def _rag_sources(items: list[RetrievalGroundingItem]) -> list[dict[str, Any]]:
    return [
        {
            "citation_id": item.citation_id,
            "confidence": item.confidence,
            "sources": list(item.sources),
            "advisory_only": item.advisory_only,
        }
        for item in items
    ]


def _similar_case_context(items: list[SimilarCaseGroundingItem]) -> list[str]:
    return [
        f"{item.case_id}: {item.title}; not_proof={str(item.not_proof).lower()}"
        for item in items
    ]


def _graph_context(items: list[GraphGroundingItem]) -> list[str]:
    return [
        (
            f"{item.relationship}; edge_kind={item.edge_kind or 'N/A'}; "
            f"not_detection_source={str(item.not_detection_source).lower()}"
        )
        for item in items
    ]


__all__ = [
    "FULL_AI_ASSISTED_SCHEMA_VERSION",
    "FullAiAssistedRequest",
    "FullAiAssistedResult",
    "GuardrailStatus",
    "run_full_ai_assisted",
]
