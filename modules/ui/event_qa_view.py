"""Pure renderer for the v3.2 Event-aware advisory Q&A panel.

This helper answers questions over an already-built EvidenceGroundingBundle. It
imports no Streamlit, performs no retrieval, writes no files, and does not alter
official Risk Level / Decision. Provider behavior remains disabled by default.
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from typing import Any

from modules.ai_advisory.event_qa import (
    EventAwareQARequest,
    EventAwareQAResult,
    answer_event_aware_question,
)
from modules.ai_advisory.prompt_contract import PromptLanguage
from modules.ui.evidence_grounded_brief_view import build_evidence_grounding_bundle_from_cli_state
from modules.ui.i18n import DEFAULT_LANGUAGE


def build_event_aware_qa_result_from_cli_state(
    cli_state: Mapping[str, Any] | None,
    *,
    question: str,
    language: str = DEFAULT_LANGUAGE,
    rag_answer_text: str = "",
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
    provider: Any | None = None,
) -> EventAwareQAResult | None:
    """Answer a current-event question from already-available UI context."""

    clean_question = str(question or "").strip()
    if not clean_question:
        return None
    bundle = build_evidence_grounding_bundle_from_cli_state(
        cli_state,
        language=language,
        rag_answer_text=rag_answer_text,
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
    )
    if bundle is None:
        return None
    return answer_event_aware_question(
        EventAwareQARequest(
            question=clean_question,
            language=_prompt_language(language),
            bundle=bundle,
            provider=provider,
        )
    )


def render_event_aware_qa_panel_html(
    cli_state: Mapping[str, Any] | None,
    *,
    question: str,
    language: str = DEFAULT_LANGUAGE,
    rag_answer_text: str = "",
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
    provider: Any | None = None,
) -> str:
    """Return escaped HTML for a current Event-aware Q&A answer."""

    result = build_event_aware_qa_result_from_cli_state(
        cli_state,
        question=question,
        language=language,
        rag_answer_text=rag_answer_text,
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
        provider=provider,
    )
    if result is None:
        return build_empty_event_qa_html(language)
    return build_event_aware_qa_result_html(result, language=language)


def build_empty_event_qa_html(language: str = DEFAULT_LANGUAGE) -> str:
    message = (
        "\u8acb\u5148\u57f7\u884c\u4e00\u6b21\u5206\u6790\uff0c\u4e26\u8f38\u5165\u76ee\u524d\u4e8b\u4ef6\u7684\u554f\u984c\u3002"
        if language == "zh-TW"
        else "Run an analysis first, then ask a question about the current event."
    )
    return (
        '<div class="sentinel-empty-card">'
        '<span class="sentinel-empty-icon">&#128172;</span>'
        f"{html.escape(message)}"
        "</div>"
    )


def build_event_aware_qa_result_html(
    result: EventAwareQAResult,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Render a guarded EventAwareQAResult as escaped HTML."""

    labels = _labels(language)
    meta = (
        '<div class="sentinel-brief-meta">'
        f'<span class="sentinel-brief-chip det">{html.escape(labels["chip"])}</span>'
        f'<span class="sentinel-brief-chip">provider_mode: {html.escape(result.provider_mode)}</span>'
        f'<span class="sentinel-brief-chip">provider_status: {html.escape(result.provider_status)}</span>'
        f'<span class="sentinel-brief-chip">llm_status: {html.escape(result.llm_status)}</span>'
        f'<span class="sentinel-brief-chip">human_review_required: {str(result.human_review_required).lower()}</span>'
        f'<span class="sentinel-brief-chip">no_enforcement: {str(result.no_enforcement).lower()}</span>'
        "</div>"
    )
    verdict = (
        '<div class="sentinel-brief-section deterministic">'
        f'<div class="sentinel-brief-h">{html.escape(labels["verdict"])}</div>'
        "<ul>"
        f"<li>Risk Level: {html.escape(str(result.official_verdict.risk_level or 'N/A'))}</li>"
        f"<li>Decision: {html.escape(str(result.official_verdict.decision or 'N/A'))}</li>"
        f"<li>simulated_decision: {str(result.official_verdict.simulated_decision).lower()}</li>"
        f"<li>authority: {html.escape(result.official_verdict.authority)}</li>"
        "</ul>"
        "</div>"
    )
    answer = _plain_section(labels["answer"], [result.answer], "advisory")
    safety = _plain_section(labels["safety"], result.safety_findings, "unsafe")
    citations = _citation_section(result, labels["citations"])
    boundary = _plain_section(labels["boundary"], result.advisory_boundary, "unsafe")
    return f'<div class="sentinel-brief">{meta}{verdict}{answer}{safety}{citations}{boundary}</div>'


def _prompt_language(language: str) -> PromptLanguage:
    return "zh-TW" if language == "zh-TW" else "en"


def _labels(language: str) -> dict[str, str]:
    if language == "zh-TW":
        return {
            "chip": "Event-aware advisory Q&A",
            "verdict": "\u5b98\u65b9 deterministic verdict",
            "answer": "\u56de\u7b54",
            "safety": "\u5b89\u5168\u6aa2\u67e5",
            "citations": "\u5f15\u7528\u4f9d\u64da",
            "boundary": "?? / Human Review Boundary",
        }
    return {
        "chip": "Event-aware advisory Q&A",
        "verdict": "Official Deterministic Verdict",
        "answer": "Answer",
        "safety": "Safety Findings",
        "citations": "Citations",
        "boundary": "Safety / Human Review Boundary",
    }


def _plain_section(title: str, items: list[str], variant: str) -> str:
    body = "".join(
        f"<li>{html.escape(str(item).strip())}</li>" for item in items if str(item).strip()
    )
    if not body:
        return ""
    return (
        f'<div class="sentinel-brief-section {html.escape(variant)}">'
        f'<div class="sentinel-brief-h">{html.escape(title)}</div>'
        f"<ul>{body}</ul>"
        "</div>"
    )


def _citation_section(result: EventAwareQAResult, title: str) -> str:
    rows = "".join(
        "<li>"
        f"{html.escape(citation.citation_id)} - {html.escape(citation.kind)} - "
        f"{html.escape(citation.label)}"
        "</li>"
        for citation in result.citations
    )
    if not rows:
        return ""
    return (
        '<div class="sentinel-brief-section neutral">'
        f'<div class="sentinel-brief-h">{html.escape(title)}</div>'
        f"<ul>{rows}</ul>"
        "</div>"
    )


__all__ = [
    "build_empty_event_qa_html",
    "build_event_aware_qa_result_from_cli_state",
    "build_event_aware_qa_result_html",
    "render_event_aware_qa_panel_html",
]
