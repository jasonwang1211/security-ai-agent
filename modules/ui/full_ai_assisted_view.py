"""Pure renderer for the v3.2 Full AI-assisted advisory panel.

The helper maps current UI state to the v3.1 FullAiAssistedResult contract and
renders escaped HTML. It imports no Streamlit and does not trigger retrieval,
graph work, case writes, enforcement, or live provider access by itself. The
runtime provider remains disabled by default unless a caller injects one.
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from typing import Any

from modules.ai_advisory.full_ai_assisted import (
    FullAiAssistedRequest,
    FullAiAssistedResult,
    run_full_ai_assisted,
)
from modules.ai_advisory.grounded_brief import GroundedBriefItem
from modules.ai_advisory.prompt_contract import PromptLanguage
from modules.ui.evidence_grounded_brief_view import build_evidence_grounding_bundle_from_cli_state
from modules.ui.i18n import DEFAULT_LANGUAGE


def build_full_ai_assisted_result_from_cli_state(
    cli_state: Mapping[str, Any] | None,
    *,
    language: str = DEFAULT_LANGUAGE,
    rag_answer_text: str = "",
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
    provider: Any | None = None,
) -> FullAiAssistedResult | None:
    """Build a guarded Full AI-assisted result from already-available UI state."""

    bundle = build_evidence_grounding_bundle_from_cli_state(
        cli_state,
        language=language,
        rag_answer_text=rag_answer_text,
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
    )
    if bundle is None:
        return None
    return run_full_ai_assisted(
        FullAiAssistedRequest(
            bundle=bundle,
            language=_prompt_language(language),
            provider=provider,
        )
    )


def render_full_ai_assisted_panel_html(
    cli_state: Mapping[str, Any] | None,
    *,
    language: str = DEFAULT_LANGUAGE,
    rag_answer_text: str = "",
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
    provider: Any | None = None,
) -> str:
    """Return escaped HTML for the Full AI-assisted advisory result panel."""

    result = build_full_ai_assisted_result_from_cli_state(
        cli_state,
        language=language,
        rag_answer_text=rag_answer_text,
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
        provider=provider,
    )
    if result is None:
        return build_empty_full_ai_assisted_html(language)
    return build_full_ai_assisted_result_html(result, language=language)


def build_empty_full_ai_assisted_html(language: str = DEFAULT_LANGUAGE) -> str:
    message = _labels(language)["empty"]
    return (
        '<div class="sentinel-empty-card">'
        '<span class="sentinel-empty-icon">&#128203;</span>'
        f"{html.escape(message)}"
        "</div>"
    )


def build_full_ai_assisted_result_html(
    result: FullAiAssistedResult,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Render a guarded FullAiAssistedResult as escaped HTML."""

    labels = _labels(language)
    meta = (
        '<div class="sentinel-brief-meta">'
        f'<span class="sentinel-brief-chip det">{html.escape(labels["chip"])}</span>'
        f'<span class="sentinel-brief-chip">provider_mode: {html.escape(result.provider_mode)}</span>'
        f'<span class="sentinel-brief-chip">provider_status: {html.escape(result.provider_status)}</span>'
        f'<span class="sentinel-brief-chip">llm_status: {html.escape(result.llm_status)}</span>'
        f'<span class="sentinel-brief-chip">guardrail_status: {html.escape(result.guardrail_status)}</span>'
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
    body = "".join(
        [
            _item_section(labels["advisory_summary"], result.generated_summary, "advisory"),
            _item_section(labels["investigation_plan"], result.generated_investigation_plan, "deterministic"),
            _plain_section(labels["evidence_gaps"], result.evidence_gaps, "gap"),
            _plain_section(labels["unsafe_assumptions"], result.unsafe_assumptions, "unsafe"),
            _rag_source_section(result, labels["rag_sources"]),
            _plain_section(labels["similar_case_context"], result.similar_case_context, "advisory"),
            _plain_section(labels["graph_context"], result.graph_context, "advisory"),
            _citation_section(result, labels["citations"]),
            _plain_section(labels["boundary"], result.advisory_boundary, "unsafe"),
        ]
    )
    return f'<div class="sentinel-brief">{meta}{verdict}{body}</div>'


def _prompt_language(language: str) -> PromptLanguage:
    return "zh-TW" if language == "zh-TW" else "en"


def _labels(language: str) -> dict[str, str]:
    if language == "zh-TW":
        return {
            "chip": "\u5b8c\u6574 AI \u8f14\u52a9\u5efa\u8b70",
            "empty": "\u8acb\u5148\u57f7\u884c\u4e00\u6b21\u5206\u6790\uff0c\u624d\u80fd\u7522\u751f\u5b8c\u6574 AI \u8f14\u52a9\u5efa\u8b70\u7d50\u679c\u3002",
            "verdict": "\u5b98\u65b9\u78ba\u5b9a\u6027\u5224\u5b9a",
            "advisory_summary": "\u5efa\u8b70\u6458\u8981",
            "investigation_plan": "\u8abf\u67e5\u5efa\u8b70",
            "evidence_gaps": "\u8b49\u64da\u7f3a\u53e3",
            "unsafe_assumptions": "\u4e0d\u5b89\u5168\u5047\u8a2d",
            "rag_sources": "RAG \u4f86\u6e90\uff08\u50c5\u4f9b\u53c3\u8003\uff09",
            "similar_case_context": "\u76f8\u4f3c\u6848\u4f8b\u8108\u7d61\uff08\u50c5\u4f9b\u53c3\u8003\uff1b\u4e0d\u662f\u8b49\u660e\uff09",
            "graph_context": "Graph \u8108\u7d61\uff08\u50c5\u4f9b\u53c3\u8003\uff1b\u4e0d\u662f\u5075\u6e2c\u4f86\u6e90\uff09",
            "citations": "\u5f15\u7528\u4f9d\u64da",
            "boundary": "\u5b89\u5168 / \u4eba\u5de5\u8907\u6838\u908a\u754c",
        }
    return {
        "chip": "Full AI-assisted advisory",
        "empty": "Run an analysis first to generate a Full AI-assisted advisory result.",
        "verdict": "Official Deterministic Verdict",
        "advisory_summary": "Advisory Summary",
        "investigation_plan": "Investigation Plan",
        "evidence_gaps": "Evidence Gaps",
        "unsafe_assumptions": "Unsafe Assumptions",
        "rag_sources": "RAG Sources (advisory only)",
        "similar_case_context": "Similar Case Context (advisory; not proof)",
        "graph_context": "Graph Context (advisory; not a detection source)",
        "citations": "Grounded Citations",
        "boundary": "Safety / Human Review Boundary",
    }


def _item_section(title: str, items: list[GroundedBriefItem], variant: str) -> str:
    body = "".join(_item_html(item) for item in items)
    if not body:
        return ""
    return (
        f'<div class="sentinel-brief-section {html.escape(variant)}">'
        f'<div class="sentinel-brief-h">{html.escape(title)}</div>'
        f"<ul>{body}</ul>"
        "</div>"
    )


def _item_html(item: GroundedBriefItem) -> str:
    citation_text = ""
    if item.citation_ids:
        citation_text = (
            ' <span class="sentinel-brief-citation">'
            f"[{html.escape(', '.join(item.citation_ids))}]</span>"
        )
    return f"<li>{html.escape(item.text)}{citation_text}</li>"


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


def _rag_source_section(result: FullAiAssistedResult, title: str) -> str:
    rows = []
    for source in result.rag_sources:
        citation_id = html.escape(str(source.get("citation_id") or "N/A"))
        confidence = html.escape(str(source.get("confidence") or "N/A"))
        advisory_only = html.escape(str(source.get("advisory_only") or False).lower())
        sources = ", ".join(str(value) for value in source.get("sources", []) if str(value).strip())
        rows.append(
            f"<li>{citation_id}; confidence={confidence}; advisory_only={advisory_only}; "
            f"sources={html.escape(sources or 'None')}</li>"
        )
    if not rows:
        return ""
    return (
        '<div class="sentinel-brief-section advisory">'
        f'<div class="sentinel-brief-h">{html.escape(title)}</div>'
        f"<ul>{''.join(rows)}</ul>"
        "</div>"
    )


def _citation_section(result: FullAiAssistedResult, title: str) -> str:
    rows = "".join(
        "<li>"
        f"{html.escape(citation.citation_id)} - {html.escape(citation.kind)} - "
        f"{html.escape(citation.label)}"
        "</li>"
        for citation in result.grounded_citations
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
    "build_empty_full_ai_assisted_html",
    "build_full_ai_assisted_result_from_cli_state",
    "build_full_ai_assisted_result_html",
    "render_full_ai_assisted_panel_html",
]
