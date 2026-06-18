"""Pure renderer for the v2.9 Evidence-Grounded AI Brief panel.

This helper maps current UI state to the v2.9 evidence-grounded backend and
renders escaped HTML. It imports no Streamlit and performs no retrieval,
generation, mutation, file writes, or enforcement action.
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

from modules.ai_advisory.evidence_bundle import (
    EvidenceGroundingBundle,
    build_evidence_grounding_bundle,
)
from modules.ai_advisory.evidence_gap import analyze_evidence_gap
from modules.ai_advisory.grounded_brief import (
    GroundedAnalystBrief,
    GroundedBriefItem,
    generate_grounded_analyst_brief,
)
from modules.ui.ai_advisory_view import build_advisory_input
from modules.ui.i18n import DEFAULT_LANGUAGE


def build_evidence_grounding_bundle_from_cli_state(
    cli_state: Mapping[str, Any] | None,
    *,
    language: str = DEFAULT_LANGUAGE,
    rag_answer_text: str = "",
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
) -> EvidenceGroundingBundle | None:
    """Build the shared evidence bundle consumed by UI advisory panels.

    ``rag_answer_text`` is optional display-state context from the already-run
    Knowledge Q&A panel. ``similar_case_result`` / ``graph_snapshot`` are optional
    already-computed structured advisory objects (a ``SimilarCaseResult`` and a
    ``GraphSnapshot``) passed straight through to the bundle builder. None of
    these trigger retrieval, graph computation, case lookup, or LLM work; they are
    advisory only and never override the official Risk Level or Decision. When a
    structured object is absent the bundle simply omits that context.
    """

    advisory_input = build_advisory_input(cli_state)
    if advisory_input is None:
        return None
    evidence_gap = analyze_evidence_gap(advisory_input, language=language)
    return build_evidence_grounding_bundle(
        advisory_input,
        evidence_gap=evidence_gap,
        rag_answer=_rag_answer_from_text(rag_answer_text),
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
    )


def build_evidence_grounded_brief_from_cli_state(
    cli_state: Mapping[str, Any] | None,
    *,
    language: str = DEFAULT_LANGUAGE,
    rag_answer_text: str = "",
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
) -> GroundedAnalystBrief | None:
    """Build a deterministic fallback brief from current active context."""

    bundle = build_evidence_grounding_bundle_from_cli_state(
        cli_state,
        language=language,
        rag_answer_text=rag_answer_text,
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
    )
    if bundle is None:
        return None
    return generate_grounded_analyst_brief(bundle)


def render_evidence_grounded_brief_panel_html(
    cli_state: Mapping[str, Any] | None,
    *,
    language: str = DEFAULT_LANGUAGE,
    rag_answer_text: str = "",
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
) -> str:
    """Return full panel HTML for the v2.9 grounded brief."""

    brief = build_evidence_grounded_brief_from_cli_state(
        cli_state,
        language=language,
        rag_answer_text=rag_answer_text,
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
    )
    if brief is None:
        return build_empty_grounded_brief_html()
    return build_evidence_grounded_brief_html(brief)


def _rag_answer_from_text(text: str) -> SimpleNamespace | None:
    answer = str(text or "").strip()
    if not answer:
        return None
    return SimpleNamespace(
        answer=answer,
        sources=(),
        confidence=None,
        limitations=("Display text copied from the already-run Knowledge Q&A panel.",),
    )


def build_empty_grounded_brief_html() -> str:
    return (
        '<div class="sentinel-empty-card">'
        '<span class="sentinel-empty-icon">&#128203;</span>'
        "Run an analysis first to generate an evidence-grounded analyst brief."
        "</div>"
    )


def build_evidence_grounded_brief_html(brief: GroundedAnalystBrief) -> str:
    """Render a structured grounded brief as escaped HTML."""

    meta = (
        '<div class="sentinel-brief-meta">'
        '<span class="sentinel-brief-chip det">Evidence-grounded advisory</span>'
        f'<span class="sentinel-brief-chip">llm_status: {html.escape(brief.llm_status)}</span>'
        f'<span class="sentinel-brief-chip">schema: {html.escape(brief.schema_version)}</span>'
        "</div>"
    )
    verdict = (
        '<div class="sentinel-brief-section deterministic">'
        '<div class="sentinel-brief-h">Official Verdict</div>'
        "<ul>"
        f"<li>Risk Level: {html.escape(str(brief.official_verdict.risk_level or 'N/A'))}</li>"
        f"<li>Decision: {html.escape(str(brief.official_verdict.decision or 'N/A'))}</li>"
        f"<li>simulated_decision: {str(brief.official_verdict.simulated_decision).lower()}</li>"
        f"<li>authority: {html.escape(brief.official_verdict.authority)}</li>"
        "</ul>"
        "</div>"
    )
    sections = "".join(
        [
            _plain_section("Context Summary", [brief.context_summary], "neutral"),
            _item_section("Executive Summary", brief.executive_summary, "advisory"),
            _item_section("What Happened", brief.what_happened, "neutral"),
            _item_section("Why It Matters", brief.why_it_matters, "neutral"),
            _item_section("Supporting Evidence", brief.supporting_evidence, "deterministic"),
            _item_section("Evidence Gap Summary", brief.evidence_gap_summary, "gap"),
            _item_section("Advisory Context", brief.advisory_context, "advisory"),
            _item_section("Recommended Next Steps", brief.recommended_next_steps, "deterministic"),
            _item_section("Unsafe Assumptions", brief.unsafe_assumptions, "unsafe"),
            _plain_section("Limitations", brief.limitations, "unsafe"),
            _citation_section(brief),
        ]
    )
    boundary = _plain_section("Safety / Human Review Boundary", brief.safety_boundary, "unsafe")
    return f'<div class="sentinel-brief">{meta}{verdict}{sections}{boundary}</div>'


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


def _item_html(item: GroundedBriefItem) -> str:
    citation_text = ""
    if item.citation_ids:
        citation_text = (
            f' <span class="sentinel-brief-citation">'
            f"[{html.escape(', '.join(item.citation_ids))}]</span>"
        )
    return f"<li>{html.escape(item.text)}{citation_text}</li>"


def _citation_section(brief: GroundedAnalystBrief) -> str:
    rows = "".join(
        "<li>"
        f"{html.escape(citation.citation_id)} - {html.escape(citation.kind)} - "
        f"{html.escape(citation.label)}"
        "</li>"
        for citation in brief.citations
    )
    if not rows:
        return ""
    return (
        '<div class="sentinel-brief-section neutral">'
        '<div class="sentinel-brief-h">Citations</div>'
        f"<ul>{rows}</ul>"
        "</div>"
    )


__all__ = [
    "build_empty_grounded_brief_html",
    "build_evidence_grounding_bundle_from_cli_state",
    "build_evidence_grounded_brief_from_cli_state",
    "build_evidence_grounded_brief_html",
    "render_evidence_grounded_brief_panel_html",
]
