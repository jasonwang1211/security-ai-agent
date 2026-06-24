"""RAG markdown export for approved knowledge notes."""

from __future__ import annotations

from typing import Any

from .types import ADVISORY_ONLY_WARNING, ApprovedKnowledgeNote, RagIngestionCandidate


def export_approved_note_to_rag_markdown(note: ApprovedKnowledgeNote | Any) -> RagIngestionCandidate:
    approved = _require_approved_note(note)
    provenance = approved.provenance
    markdown = "\n".join(
        [
            f"# {approved.title}",
            "",
            f"> {ADVISORY_ONLY_WARNING}",
            "",
            "## Provenance",
            "",
            f"- source_event_id: `{provenance.source_event_id}`",
            f"- official_risk_level: `{provenance.official_risk_level}` (copied deterministic context)",
            f"- official_decision: `{provenance.official_decision}` (copied deterministic context)",
            f"- source_rule_ids: {', '.join(provenance.source_rule_ids) or 'none'}",
            f"- source_evidence_ids: {', '.join(provenance.source_evidence_ids) or 'none'}",
            f"- source_gap_ids: {', '.join(provenance.source_gap_ids) or 'none'}",
            f"- source_rag_ids: {', '.join(provenance.source_rag_ids) or 'none'}",
            f"- source_case_ids: {', '.join(provenance.source_case_ids) or 'none'} (not proof of compromise)",
            f"- source_graph_ids: {', '.join(provenance.source_graph_ids) or 'none'} (not a detection source)",
            f"- approved_by: `{approved.approved_by}`",
            "",
            "## Approved Note",
            "",
            approved.body,
            "",
            "## Safety Boundary",
            "",
            "- Advisory-only RAG candidate.",
            "- Not official detection logic.",
            "- Does not override Risk Level or Decision.",
            "- No real enforcement is authorized.",
        ]
    )
    return RagIngestionCandidate(
        source_note_id=approved.note_id,
        title=approved.title,
        markdown=markdown,
        provenance=provenance,
    )


def _require_approved_note(note: ApprovedKnowledgeNote | Any) -> ApprovedKnowledgeNote:
    if not isinstance(note, ApprovedKnowledgeNote) or getattr(note, "status", None) != "approved":
        raise ValueError("Only approved knowledge notes can be exported for RAG.")
    if note.safety_flags:
        raise ValueError("Flagged knowledge notes cannot be exported for RAG.")
    return note


__all__ = ["export_approved_note_to_rag_markdown"]
