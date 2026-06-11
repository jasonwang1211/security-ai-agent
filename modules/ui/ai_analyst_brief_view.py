"""Pure UI helper for the deterministic AI Analyst Brief panel (v2.7-H).

Maps the current active context into the v2.7-G deterministic AI Analyst Brief
backend and renders a readable, escaped HTML panel for the AI Analyst tab.
This module is presentation-only and framework-light: no UI framework import, no
LLM/RAG/Ollama calls, no detector/risk/decision changes, and no writes.
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from typing import Any

from modules.ai_advisory import (
    AIAnalystBrief,
    AIAnalystBriefInput,
    build_ai_analyst_brief,
)
from modules.ui.ai_advisory_view import build_advisory_input
from modules.ui.i18n import DEFAULT_LANGUAGE, t


def build_ai_analyst_brief_from_cli_state(
    cli_state: Mapping[str, Any] | None,
    language: str = DEFAULT_LANGUAGE,
) -> AIAnalystBrief | None:
    """Build a deterministic brief from current active context, or None.

    Reuses the Evidence Gap UI's read-only active-context extraction so event
    and incident facts are mapped consistently. Optional similar-case, graph,
    and draft context are intentionally omitted unless a lightweight structured
    source already exists; this helper invents no case IDs or graph facts.
    """

    advisory_input = build_advisory_input(cli_state)
    if advisory_input is None:
        return None
    return build_ai_analyst_brief(
        AIAnalystBriefInput(advisory_input=advisory_input, evidence_gap=None),
        language=language,
    )


def render_ai_analyst_brief_panel_html(
    cli_state: Mapping[str, Any] | None,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Return full panel HTML: empty state or deterministic analyst brief."""

    brief = build_ai_analyst_brief_from_cli_state(cli_state, language=language)
    if brief is None:
        return build_empty_brief_state_html(language)
    return build_ai_analyst_brief_html(brief, language=language)


def build_empty_brief_state_html(language: str = DEFAULT_LANGUAGE) -> str:
    """Render the no-active-context empty state for the brief panel."""

    return (
        '<div class="sentinel-empty-card">'
        '<span class="sentinel-empty-icon">&#128203;</span>'
        f'{html.escape(t("ai_analyst_brief_empty", language))}</div>'
    )


def build_ai_analyst_brief_html(
    brief: AIAnalystBrief,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Render a populated AI Analyst Brief as escaped HTML cards."""

    meta = (
        '<div class="sentinel-brief-meta">'
        f'<span class="sentinel-brief-chip det">{html.escape(t("ai_analyst_brief_chip", language))}</span>'
        f'<span class="sentinel-brief-chip">llm_status: {html.escape(brief.llm_status)}</span>'
        f'<span class="sentinel-brief-chip">source: {html.escape(brief.source)}</span>'
        '</div>'
    )
    sections = ''.join(
        [
            _section_html(
                variant="neutral",
                heading=t("ai_analyst_brief_what_happened", language),
                items=brief.what_happened,
            ),
            _section_html(
                variant="neutral",
                heading=t("ai_analyst_brief_why_it_matters", language),
                items=brief.why_it_matters,
            ),
            _section_html(
                variant="deterministic",
                heading=t("ai_analyst_brief_deterministic_verdict", language),
                items=brief.deterministic_verdict,
            ),
            _section_html(
                variant="advisory",
                heading=t("ai_analyst_brief_advisory_summary", language),
                items=brief.advisory_summary,
            ),
            _section_html(
                variant="gap",
                heading=t("ai_analyst_brief_evidence_gap", language),
                items=brief.evidence_gap_summary,
            ),
            _section_html(
                variant="deterministic",
                heading=t("ai_analyst_brief_next_steps", language),
                items=brief.recommended_next_steps,
            ),
            _section_html(
                variant="unsafe",
                heading=t("ai_analyst_brief_unsafe", language),
                items=brief.unsafe_assumptions,
            ),
        ]
    )
    boundary = (
        f'<div class="sentinel-brief-boundary">{html.escape(brief.safety_boundary)}</div>'
        if brief.safety_boundary.strip()
        else ''
    )
    return f'<div class="sentinel-brief">{meta}{sections}{boundary}</div>'


def _section_html(*, variant: str, heading: str, items: list[str]) -> str:
    body = ''.join(
        f'<li>{html.escape(str(item).strip())}</li>'
        for item in items
        if str(item).strip()
    )
    if not body:
        return ''
    return (
        f'<div class="sentinel-brief-section {html.escape(variant)}">'
        f'<div class="sentinel-brief-h">{html.escape(heading)}</div>'
        f'<ul>{body}</ul>'
        '</div>'
    )


__all__ = [
    "build_ai_analyst_brief_from_cli_state",
    "build_ai_analyst_brief_html",
    "build_empty_brief_state_html",
    "render_ai_analyst_brief_panel_html",
]
