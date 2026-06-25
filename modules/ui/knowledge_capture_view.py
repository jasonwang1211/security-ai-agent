"""Pure UI helpers for the v3.6 knowledge capture review queue.

The helpers render local JSONL-backed knowledge notes and expose explicit
approve/reject/export-preview operations. They import no Streamlit, do not call
RAG runtime ingest, do not mutate graph facts, and do not alter official Risk
Level / Decision.
"""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
from typing import Any

from modules.knowledge_capture import (
    ApprovedKnowledgeNote,
    CandidateKnowledgeNote,
    KnowledgeCaptureSafetyError,
    KnowledgeCaptureStore,
    RejectedKnowledgeNote,
    export_approved_note_to_graph_candidates,
    export_approved_note_to_rag_markdown,
)
from modules.ui.i18n import DEFAULT_LANGUAGE

DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE = Path(".tmp") / "knowledge_capture_ui" / "capture_store"


@dataclass(frozen=True)
class KnowledgeCaptureActionResult:
    ok: bool
    message: str
    safety_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeCaptureExportPreview:
    rag_markdown: str
    graph_candidates: dict[str, list[dict[str, Any]]]


def load_knowledge_capture_store(root: str | Path = DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE) -> KnowledgeCaptureStore:
    """Return a local review store without creating notes or runtime side effects."""

    return KnowledgeCaptureStore(Path(root))


def approve_pending_note(
    store: KnowledgeCaptureStore,
    note_id: str,
    *,
    approved_by: str,
    edited_body: str | None = None,
    approval_notes: str | None = None,
) -> KnowledgeCaptureActionResult:
    """Approve a pending note through the hardened store API."""

    try:
        approved = store.approve_note(
            note_id,
            approved_by=approved_by,
            edited_body=edited_body,
            approval_notes=approval_notes,
        )
    except KnowledgeCaptureSafetyError as error:
        return KnowledgeCaptureActionResult(False, str(error), tuple(error.safety_flags))
    except (KeyError, ValueError) as error:
        return KnowledgeCaptureActionResult(False, str(error))
    return KnowledgeCaptureActionResult(True, f"Approved knowledge note {approved.note_id}.")


def reject_pending_note(
    store: KnowledgeCaptureStore,
    note_id: str,
    *,
    rejected_by: str,
    rejection_reason: str,
) -> KnowledgeCaptureActionResult:
    """Reject a pending note with a non-empty reason."""

    reviewer = str(rejected_by or "").strip()
    reason = str(rejection_reason or "").strip()
    if not reviewer:
        return KnowledgeCaptureActionResult(False, "rejected_by is required before rejection.")
    if not reason:
        return KnowledgeCaptureActionResult(False, "rejection_reason is required before rejection.")
    try:
        rejected = store.reject_note(note_id, rejected_by=reviewer, rejection_reason=reason)
    except (KeyError, ValueError) as error:
        return KnowledgeCaptureActionResult(False, str(error))
    return KnowledgeCaptureActionResult(True, f"Rejected knowledge note {rejected.note_id}.")


def build_knowledge_capture_review_queue_html(
    store: KnowledgeCaptureStore,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Render the current local review queue as escaped HTML."""

    pending = store.list_pending_notes()
    approved = store.list_approved_notes()
    rejected = store.list_rejected_notes()
    labels = _labels(language)
    sections = [build_safety_boundary_html(language)]
    if not (pending or approved or rejected):
        sections.append(build_empty_knowledge_capture_review_html(language))
    else:
        if pending:
            sections.append(_note_group(labels["pending"], [build_pending_note_card_html(note, language=language) for note in pending]))
        if approved:
            sections.append(_note_group(labels["approved"], [build_approved_note_card_html(note, language=language) for note in approved]))
        if rejected:
            sections.append(_note_group(labels["rejected"], [build_rejected_note_card_html(note, language=language) for note in rejected]))
    return '<div class="sentinel-brief knowledge-capture-review">' + "".join(sections) + "</div>"


def build_empty_knowledge_capture_review_html(language: str = DEFAULT_LANGUAGE) -> str:
    labels = _labels(language)
    return (
        '<div class="sentinel-empty-card">'
        '<span class="sentinel-empty-icon">&#128196;</span>'
        f'{html.escape(labels["empty"])} '
        '<code>python scripts/demo_knowledge_capture.py --output-dir .tmp/knowledge_capture_ui --clean</code>'
        "</div>"
    )


def build_safety_boundary_html(language: str = DEFAULT_LANGUAGE) -> str:
    labels = _labels(language)
    items = [
        labels["advisory_only"],
        labels["not_detection_source"],
        labels["not_proof"],
        labels["no_verdict_override"],
        labels["no_enforcement"],
        labels["no_auto_ingest"],
    ]
    return _plain_section(labels["boundary"], items, "unsafe")


def build_pending_note_card_html(
    note: CandidateKnowledgeNote,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    labels = _labels(language)
    return _note_card(
        note_id=note.note_id,
        title=note.title,
        body=note.body,
        status=note.status,
        provenance_items=_provenance_items(note.provenance, labels),
        boundary=note.advisory_boundary,
        labels=labels,
    )


def build_approved_note_card_html(
    note: ApprovedKnowledgeNote,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    labels = _labels(language)
    return _note_card(
        note_id=note.note_id,
        title=note.title,
        body=note.body,
        status=note.status,
        provenance_items=_provenance_items(note.provenance, labels),
        boundary=note.advisory_boundary,
        labels=labels,
    )


def build_rejected_note_card_html(
    note: RejectedKnowledgeNote,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    labels = _labels(language)
    return _note_card(
        note_id=note.note_id,
        title=note.title,
        body=note.body,
        status=note.status,
        provenance_items=[*_provenance_items(note.provenance, labels), f'{labels["rejection_reason"]}: {note.rejection_reason}'],
        boundary=note.advisory_boundary,
        labels=labels,
    )


def build_approved_note_export_preview(note: ApprovedKnowledgeNote) -> KnowledgeCaptureExportPreview:
    """Build approved-only RAG/Graph preview artifacts without runtime mutation."""

    rag_candidate = export_approved_note_to_rag_markdown(note)
    nodes, edges = export_approved_note_to_graph_candidates(note)
    return KnowledgeCaptureExportPreview(
        rag_markdown=rag_candidate.markdown,
        graph_candidates={
            "nodes": [node.model_dump(mode="json") for node in nodes],
            "edges": [edge.model_dump(mode="json") for edge in edges],
        },
    )


def build_approved_note_exports_html(
    note: ApprovedKnowledgeNote,
    *,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    labels = _labels(language)
    preview = build_approved_note_export_preview(note)
    graph_json = json.dumps(preview.graph_candidates, indent=2)
    return (
        '<div class="sentinel-brief-section advisory">'
        f'<div class="sentinel-brief-h">{html.escape(labels["exports"])}</div>'
        f'<p>{html.escape(labels["export_boundary"])}</p>'
        f'<div><strong>{html.escape(labels["rag_preview"])}</strong></div>'
        f'<pre><code>{html.escape(preview.rag_markdown)}</code></pre>'
        f'<div><strong>{html.escape(labels["graph_preview"])}</strong></div>'
        f'<pre><code>{html.escape(graph_json)}</code></pre>'
        "</div>"
    )


def _note_group(title: str, cards: list[str]) -> str:
    return (
        '<div class="sentinel-brief-section neutral">'
        f'<div class="sentinel-brief-h">{html.escape(title)}</div>'
        f'{"".join(cards)}'
        "</div>"
    )


def _note_card(
    *,
    note_id: str,
    title: str,
    body: str,
    status: str,
    provenance_items: list[str],
    boundary: str,
    labels: dict[str, str],
) -> str:
    provenance = "".join(f"<li>{html.escape(item)}</li>" for item in provenance_items if item)
    return (
        '<div class="sentinel-brief-section advisory">'
        f'<div class="sentinel-brief-h">{html.escape(note_id)} - {html.escape(title)}</div>'
        '<div class="sentinel-brief-meta">'
        f'<span class="sentinel-brief-chip">status: {html.escape(status)}</span>'
        '<span class="sentinel-brief-chip">advisory_only: true</span>'
        '<span class="sentinel-brief-chip">not_detection_source: true</span>'
        '<span class="sentinel-brief-chip">not_proof: true</span>'
        "</div>"
        f'<p>{html.escape(body)}</p>'
        f'<div><strong>{html.escape(labels["provenance"])}</strong></div>'
        f"<ul>{provenance}</ul>"
        f'<p><strong>{html.escape(labels["boundary"])}</strong>: {html.escape(boundary)}</p>'
        "</div>"
    )


def _provenance_items(provenance: Any, labels: dict[str, str]) -> list[str]:
    return [
        f'{labels["source_event"]}: {provenance.source_event_id}',
        f'{labels["source_question"]}: {provenance.source_question}',
        f'{labels["source_answer"]}: {provenance.source_answer_summary}',
        f'{labels["risk"]}: {provenance.official_risk_level} ({labels["copied_context"]})',
        f'{labels["decision"]}: {provenance.official_decision} ({labels["copied_context"]})',
        f'source_rule_ids: {", ".join(provenance.source_rule_ids) or "none"}',
        f'source_evidence_ids: {", ".join(provenance.source_evidence_ids) or "none"}',
        f'source_gap_ids: {", ".join(provenance.source_gap_ids) or "none"}',
        f'source_rag_ids: {", ".join(provenance.source_rag_ids) or "none"}',
        f'source_case_ids: {", ".join(provenance.source_case_ids) or "none"} ({labels["not_proof"]})',
        f'source_graph_ids: {", ".join(provenance.source_graph_ids) or "none"} ({labels["not_detection_source"]})',
    ]


def _plain_section(title: str, items: list[str], variant: str) -> str:
    rows = "".join(f"<li>{html.escape(item)}</li>" for item in items if item)
    return (
        f'<div class="sentinel-brief-section {html.escape(variant)}">'
        f'<div class="sentinel-brief-h">{html.escape(title)}</div>'
        f"<ul>{rows}</ul>"
        "</div>"
    )


def _labels(language: str) -> dict[str, str]:
    if language == "zh-TW":
        return {
            "pending": "Pending knowledge notes / \u5f85\u5be9\u6838\u77e5\u8b58\u7b46\u8a18",
            "approved": "Approved knowledge notes / \u5df2\u6838\u51c6\u77e5\u8b58\u7b46\u8a18",
            "rejected": "Rejected knowledge notes / \u5df2\u62d2\u7d55\u77e5\u8b58\u7b46\u8a18",
            "empty": "\u76ee\u524d\u6c92\u6709\u672c\u6a5f knowledge capture \u7b46\u8a18\u3002\u53ef\u4f7f\u7528\u4ee5\u4e0b\u6307\u4ee4\u7522\u751f synthetic demo notes\uff1a",
            "boundary": "\u5b89\u5168 / \u4eba\u5de5\u8907\u6838\u908a\u754c",
            "advisory_only": "\u50c5\u4f9b\u53c3\u8003\uff1b\u9700\u8981 human review\u3002",
            "not_detection_source": "\u4e0d\u662f\u5075\u6e2c\u4f86\u6e90\u3002",
            "not_proof": "\u4e0d\u662f compromise \u6216\u6210\u529f\u653b\u64ca\u7684\u8b49\u660e\u3002",
            "no_verdict_override": "\u4e0d\u8986\u84cb deterministic Risk Level / Decision\u3002",
            "no_enforcement": "\u4e0d\u57f7\u884c\u771f\u5be6 firewall / WAF / EDR / account / cloud / SIEM / SOAR \u52d5\u4f5c\u3002",
            "no_auto_ingest": "\u4e0d\u81ea\u52d5\u9032\u884c RAG ingestion \u6216 Graph mutation\u3002",
            "provenance": "Provenance / \u4f86\u6e90\u8108\u7d61",
            "source_event": "source_event_id",
            "source_question": "source_question",
            "source_answer": "source_answer_summary",
            "risk": "Official Risk Level",
            "decision": "Official Decision",
            "copied_context": "copied deterministic context",
            "rejection_reason": "rejection_reason",
            "exports": "Approved export previews / \u6838\u51c6\u5f8c\u532f\u51fa\u9810\u89bd",
            "export_boundary": "\u50c5\u9810\u89bd\uff1b\u4e0d\u57f7\u884c RAG ingestion\uff0c\u4e5f\u4e0d\u4fee\u6539 Graph runtime facts\u3002",
            "rag_preview": "RAG markdown preview",
            "graph_preview": "Graph candidate JSON preview",
        }

    return {
        "pending": "Pending knowledge notes",
        "approved": "Approved knowledge notes",
        "rejected": "Rejected knowledge notes",
        "empty": "No local knowledge capture notes yet. Generate synthetic demo notes with:",
        "boundary": "Safety / Human Review Boundary",
        "advisory_only": "Advisory-only; human review required.",
        "not_detection_source": "Not a detection source.",
        "not_proof": "Not proof of compromise.",
        "no_verdict_override": "Does not override deterministic Risk Level / Decision.",
        "no_enforcement": "No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action.",
        "no_auto_ingest": "No automatic RAG ingestion or Graph mutation.",
        "provenance": "Provenance",
        "source_event": "source_event_id",
        "source_question": "source_question",
        "source_answer": "source_answer_summary",
        "risk": "Official Risk Level",
        "decision": "Official Decision",
        "copied_context": "copied deterministic context",
        "rejection_reason": "rejection_reason",
        "exports": "Approved export previews",
        "export_boundary": "Preview only; does not run RAG ingestion or mutate Graph runtime facts.",
        "rag_preview": "RAG markdown preview",
        "graph_preview": "Graph candidate JSON preview",
    }


__all__ = [
    "DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE",
    "KnowledgeCaptureActionResult",
    "KnowledgeCaptureExportPreview",
    "approve_pending_note",
    "build_approved_note_export_preview",
    "build_approved_note_exports_html",
    "build_approved_note_card_html",
    "build_empty_knowledge_capture_review_html",
    "build_knowledge_capture_review_queue_html",
    "build_pending_note_card_html",
    "build_rejected_note_card_html",
    "build_safety_boundary_html",
    "load_knowledge_capture_store",
    "reject_pending_note",
]
