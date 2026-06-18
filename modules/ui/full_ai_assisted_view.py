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
        return build_empty_full_ai_assisted_html()
    return build_full_ai_assisted_result_html(result)


def build_empty_full_ai_assisted_html() -> str:
    return (
        '<div class="sentinel-empty-card">'
        '<span class="sentinel-empty-icon">&#128203;</span>'
        "Run an analysis first to generate a Full AI-assisted advisory result."
        "</div>"
    )


def build_full_ai_assisted_result_html(result: FullAiAssistedResult) -> str:
    """Render a guarded FullAiAssistedResult as escaped HTML."""

    meta = (
        '<div class="sentinel-brief-meta">'
        '<span class="sentinel-brief-chip det">Full AI-assisted advisory</span>'
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
        '<div class="sentinel-brief-h">Official Deterministic Verdict</div>'
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
            _item_section("Advisory Summary", result.generated_summary, "advisory"),
            _item_section("Investigation Plan", result.generated_investigation_plan, "deterministic"),
            _plain_section("Evidence Gaps", result.evidence_gaps, "gap"),
            _plain_section("Unsafe Assumptions", result.unsafe_assumptions, "unsafe"),
            _rag_source_section(result),
            _plain_section("Similar Case Context (advisory; not proof)", result.similar_case_context, "advisory"),
            _plain_section("Graph Context (advisory; not a detection source)", result.graph_context, "advisory"),
            _citation_section(result),
            _plain_section("Safety / Human Review Boundary", result.advisory_boundary, "unsafe"),
        ]
    )
    return f'<div class="sentinel-brief">{meta}{verdict}{body}</div>'


def _prompt_language(language: str) -> PromptLanguage:
    return "zh-TW" if language == "zh-TW" else "en"


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


def _rag_source_section(result: FullAiAssistedResult) -> str:
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
        '<div class="sentinel-brief-h">RAG Sources (advisory only)</div>'
        f"<ul>{''.join(rows)}</ul>"
        "</div>"
    )


def _citation_section(result: FullAiAssistedResult) -> str:
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
        '<div class="sentinel-brief-h">Grounded Citations</div>'
        f"<ul>{rows}</ul>"
        "</div>"
    )


__all__ = [
    "build_empty_full_ai_assisted_html",
    "build_full_ai_assisted_result_from_cli_state",
    "build_full_ai_assisted_result_html",
    "render_full_ai_assisted_panel_html",
]
