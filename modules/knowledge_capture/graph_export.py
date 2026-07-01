"""Graph candidate export for approved knowledge notes."""

from __future__ import annotations

from typing import Any

from .extractor import compact_unique, evaluate_note_safety_flags
from .types import (
    ApprovedKnowledgeNote,
    FLAG_MISSING_PROVENANCE,
    GraphEdgeCandidate,
    GraphNodeCandidate,
    KnowledgeCaptureSafetyError,
)


def export_approved_note_to_graph_candidates(
    note: ApprovedKnowledgeNote | Any,
) -> tuple[list[GraphNodeCandidate], list[GraphEdgeCandidate]]:
    approved = _require_approved_note(note)
    node_id = f"knowledge-note:{approved.note_id}"
    node = GraphNodeCandidate(
        node_id=node_id,
        source_note_id=approved.note_id,
        label=approved.title,
        summary=approved.body,
        provenance=approved.provenance,
    )
    edge = GraphEdgeCandidate(
        edge_id=f"knowledge-edge:{approved.note_id}:source-event",
        source_note_id=approved.note_id,
        source_node_id=approved.provenance.source_event_id,
        target_node_id=node_id,
        provenance=approved.provenance,
    )
    return [node], [edge]


def _require_approved_note(note: ApprovedKnowledgeNote | Any) -> ApprovedKnowledgeNote:
    if not isinstance(note, ApprovedKnowledgeNote) or getattr(note, "status", None) != "approved":
        raise ValueError("Only approved knowledge notes can be exported as graph candidates.")
    existing_flags = compact_unique([*note.safety_flags, *note.provenance.safety_flags])
    if existing_flags:
        raise ValueError("Flagged knowledge notes cannot be exported as graph candidates.")
    if not note.approved_by.strip():
        raise KnowledgeCaptureSafetyError(
            "Approved knowledge note requires non-empty approved_by before export.",
            [FLAG_MISSING_PROVENANCE],
        )
    final_flags = evaluate_note_safety_flags(
        title=note.title,
        body=note.body,
        provenance=note.provenance,
    )
    if final_flags:
        raise KnowledgeCaptureSafetyError(
            "Approved knowledge note failed final graph export safety validation.", final_flags
        )
    return note


__all__ = ["export_approved_note_to_graph_candidates"]
