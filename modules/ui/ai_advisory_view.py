"""Pure UI helper for the deterministic Evidence Gap Analyzer panel (v2.7-B).

Maps the current active context (event or authentication incident) into the
deterministic ``modules.ai_advisory`` Evidence Gap Analyzer and renders a
readable, escaped HTML panel for the AI Analyst tab.

This module is presentation-only and framework-light:

- It does not import any UI rendering framework.
- It does not call an LLM, RAG, or Ollama, and adds no generation.
- It never overrides or recomputes the deterministic Risk Level or Decision;
  it only surfaces advisory analyst context. Extraction is best-effort and
  read-only — it invents no evidence IDs, rules, or graph facts.
"""

from __future__ import annotations

import html
from collections.abc import Iterable, Mapping
from typing import Any

from modules.ai_advisory import (
    AIAdvisoryInput,
    EvidenceGapAnalysis,
    analyze_evidence_gap,
)
from modules.ui.console_state import (
    ACTIVE_CONTEXT_KIND_KEY,
    ACTIVE_EVENT_CONTEXT_KEY,
    ACTIVE_INCIDENT_CONTEXT_KEY,
)
from modules.ui.i18n import DEFAULT_LANGUAGE, t


# --------------------------------------------------------------------------- #
# Active context -> AIAdvisoryInput (best-effort, read-only extraction)
# --------------------------------------------------------------------------- #
def build_advisory_input(cli_state: Mapping[str, Any] | None) -> AIAdvisoryInput | None:
    """Build advisory input from the retained active context, or None.

    Mirrors ``summarize_active_context``: ``"event"`` uses the payload/event
    context, ``"incident"`` uses the authentication-incident context. Returns
    None when there is no active context so the panel can show an empty state.
    """

    state = cli_state or {}
    kind = str(state.get(ACTIVE_CONTEXT_KIND_KEY) or "")
    if kind == "event" and state.get(ACTIVE_EVENT_CONTEXT_KEY) is not None:
        return _event_advisory_input(state[ACTIVE_EVENT_CONTEXT_KEY])
    if kind == "incident" and state.get(ACTIVE_INCIDENT_CONTEXT_KEY) is not None:
        return _incident_advisory_input(state[ACTIVE_INCIDENT_CONTEXT_KEY])
    return None


def _event_advisory_input(context: Any) -> AIAdvisoryInput:
    attack_types = _clean_list(getattr(context, "attack_types", ()) or ())
    rule_ids = _clean_list(getattr(context, "rule_ids", ()) or ())
    signatures = _flatten_signatures(getattr(context, "matched_signatures", {}) or {})
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        attack_type=", ".join(attack_types) or None,
        risk_label=_label_text(getattr(context, "risk_level", None)) or None,
        decision_label=_label_text(getattr(context, "decision", None)) or None,
        matched_rule_ids=rule_ids,
        matched_signatures=signatures,
        detection_source="rule_based_detection",
        source_label="active_event_context",
    )


def _incident_advisory_input(context: Any) -> AIAdvisoryInput:
    incident = getattr(context, "incident", None)
    finding_type = _first_nonempty(
        _label_text(getattr(incident, "attack_type", None)),
        _first_finding_type(incident),
        _label_text(getattr(incident, "title", None)),
    )
    bundle = getattr(incident, "evidence_bundle", None)
    items = list(getattr(bundle, "items", []) or [])
    evidence_labels = _clean_list(getattr(item, "type", "") for item in items)
    available_ids = getattr(bundle, "available_ids", None) or []
    evidence_ids = sorted(str(value) for value in available_ids)
    findings = list(getattr(incident, "findings", []) or [])
    finding_ids = _clean_list(getattr(finding, "id", "") for finding in findings)
    return AIAdvisoryInput(
        event_kind="authentication_incident",
        finding_type=finding_type or None,
        risk_label=_label_text(getattr(incident, "risk_level", None)) or None,
        decision_label=_label_text(getattr(incident, "decision", None)) or None,
        evidence_labels=evidence_labels,
        detection_source="rule_based_detection",
        incident_id=_label_text(getattr(incident, "id", None)) or None,
        finding_ids=finding_ids,
        evidence_ids=evidence_ids,
        source_label="active_incident_context",
    )


def _first_finding_type(incident: Any) -> str:
    for finding in getattr(incident, "findings", []) or []:
        text = _label_text(getattr(finding, "finding_type", None))
        if text:
            return text
    return ""


def _first_nonempty(*values: str) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def _label_text(value: Any) -> str:
    """Normalize a str or str-Enum (e.g. RiskLevel/Decision) to plain text."""
    if value is None:
        return ""
    return str(getattr(value, "value", value)).strip()


def _clean_list(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _flatten_signatures(matched: Any) -> list[str]:
    out: list[str] = []
    if isinstance(matched, dict):
        for signatures in matched.values():
            for signature in signatures or ():
                text = str(signature or "").strip()
                if text and text not in out:
                    out.append(text)
    return out


# --------------------------------------------------------------------------- #
# Rendering (readable, escaped HTML; not a code block)
# --------------------------------------------------------------------------- #
def _list_items_html(items: list[str]) -> str:
    return "".join(
        f"<li>{html.escape(str(item).strip())}</li>" for item in items if str(item).strip()
    )


def _section_html(*, variant: str, icon: str, heading: str, items: list[str]) -> str:
    body = _list_items_html(items)
    if not body:
        return ""
    return (
        f'<div class="sentinel-gap-section {variant}">'
        f'<div class="sentinel-gap-h">{html.escape(icon)} {html.escape(heading)}</div>'
        f"<ul>{body}</ul>"
        "</div>"
    )


def build_evidence_gap_html(
    analysis: EvidenceGapAnalysis, *, language: str = DEFAULT_LANGUAGE
) -> str:
    """Render a populated evidence-gap panel as readable, escaped HTML.

    Section headings are fixed (translated) labels; the list contents and the
    advisory boundary are the deterministic analyzer's own text. The metadata
    row surfaces ``llm_status`` and ``source`` verbatim so the LLM-free,
    deterministic provenance is visible. No authoritative Risk Level / Decision
    verdict is emitted here.
    """

    meta = (
        '<div class="sentinel-gap-meta">'
        f'<span class="sentinel-gap-chip det">{html.escape(t("evidence_gap_advisory_chip", language))}</span>'
        f'<span class="sentinel-gap-chip">llm_status: {html.escape(analysis.llm_status)}</span>'
        f'<span class="sentinel-gap-chip">source: {html.escape(analysis.source)}</span>'
        "</div>"
    )
    sections = "".join(
        [
            _section_html(
                variant="confirmed",
                icon="✓",
                heading=t("evidence_gap_confirmed", language),
                items=list(analysis.confirmed_facts),
            ),
            _section_html(
                variant="missing",
                icon="▢",
                heading=t("evidence_gap_missing", language),
                items=list(analysis.missing_evidence),
            ),
            _section_html(
                variant="checks",
                icon="→",
                heading=t("evidence_gap_checks", language),
                items=list(analysis.recommended_checks),
            ),
            _section_html(
                variant="unsafe",
                icon="⚠",
                heading=t("evidence_gap_unsafe", language),
                items=list(analysis.unsafe_assumptions),
            ),
        ]
    )
    boundary = (
        f'<div class="sentinel-gap-boundary">{html.escape(analysis.advisory_boundary)}</div>'
        if analysis.advisory_boundary.strip()
        else ""
    )
    return f'<div class="sentinel-gap">{meta}{sections}{boundary}</div>'


def build_empty_state_html(language: str = DEFAULT_LANGUAGE) -> str:
    """Render the no-active-context empty state for the panel."""
    return (
        '<div class="sentinel-empty-card">'
        '<span class="sentinel-empty-icon">\U0001f9ed</span>'
        f'{html.escape(t("evidence_gap_empty", language))}</div>'
    )


def render_evidence_gap_panel_html(
    cli_state: Mapping[str, Any] | None, language: str = DEFAULT_LANGUAGE
) -> str:
    """Return the full panel HTML: empty state, or the analyzed evidence gap.

    Renders only when there is an active context; otherwise returns the
    empty-state card. The analysis is deterministic and advisory-only.
    """

    advisory_input = build_advisory_input(cli_state)
    if advisory_input is None:
        return build_empty_state_html(language)
    analysis = analyze_evidence_gap(advisory_input)
    return build_evidence_gap_html(analysis, language=language)
