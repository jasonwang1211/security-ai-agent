"""Graph candidate export for approved knowledge notes."""

from __future__ import annotations

from typing import Any

from .types import ApprovedKnowledgeNote, GraphEdgeCandidate, GraphNodeCandidate


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
    if note.safety_flags:
        raise ValueError("Flagged knowledge notes cannot be exported as graph candidates.")
    return note


__all__ = ["export_approved_note_to_graph_candidates"]
