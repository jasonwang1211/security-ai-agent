"""Typed contracts for human-approved knowledge capture.

The v3.5 foundation intentionally stops before RAG ingest or graph mutation.
It stores candidate notes for human review and exports approved notes only as
advisory artifacts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

KnowledgeNoteStatus = Literal["pending_review", "approved", "rejected"]
ConfidenceLabel = Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"]

ADVISORY_ONLY_WARNING = (
    "Human-approved advisory knowledge only. This note is not a detection "
    "source, does not prove compromise, does not override deterministic Risk "
    "Level or Decision, and requires human review before operational use."
)

FLAG_MISSING_PROVENANCE = "missing_provenance"
FLAG_UNSAFE_CONTENT = "unsafe_content"
FLAG_VERDICT_OVERRIDE = "verdict_override_attempt"
FLAG_SIMILAR_CASE_PROOF = "similar_case_as_proof"
FLAG_GRAPH_DETECTION_SOURCE = "graph_as_detection_source"
FLAG_SECRET_OR_PII = "secret_or_pii_risk"

HARD_REJECT_SAFETY_FLAGS = frozenset(
    {
        FLAG_MISSING_PROVENANCE,
        FLAG_UNSAFE_CONTENT,
        FLAG_VERDICT_OVERRIDE,
        FLAG_SIMILAR_CASE_PROOF,
        FLAG_GRAPH_DETECTION_SOURCE,
        FLAG_SECRET_OR_PII,
    }
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_note_id() -> str:
    return f"KC-{uuid4().hex[:12].upper()}"


class KnowledgeCaptureSafetyError(ValueError):
    """Raised when a note cannot enter the human-review queue safely."""

    def __init__(self, message: str, safety_flags: list[str] | None = None) -> None:
        super().__init__(message)
        self.safety_flags = list(safety_flags or [])


class KnowledgeCaptureProvenance(BaseModel):
    """Provenance required for every candidate, approved, or rejected note."""

    model_config = ConfigDict(extra="forbid")

    source_event_id: str
    source_question: str
    source_answer_summary: str
    source_evidence_ids: list[str] = Field(default_factory=list)
    source_rule_ids: list[str] = Field(default_factory=list)
    source_gap_ids: list[str] = Field(default_factory=list)
    source_rag_ids: list[str] = Field(default_factory=list)
    source_case_ids: list[str] = Field(default_factory=list)
    source_graph_ids: list[str] = Field(default_factory=list)
    official_risk_level: str
    official_decision: str
    created_at: datetime = Field(default_factory=utc_now)
    created_by: str
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejected_at: datetime | None = None
    rejected_by: str | None = None
    status: KnowledgeNoteStatus = "pending_review"
    confidence_label: ConfidenceLabel = "UNKNOWN"
    safety_flags: list[str] = Field(default_factory=list)

    def source_reference_ids(self) -> list[str]:
        return [
            *self.source_evidence_ids,
            *self.source_rule_ids,
            *self.source_gap_ids,
            *self.source_rag_ids,
            *self.source_case_ids,
            *self.source_graph_ids,
        ]


class CandidateKnowledgeNote(BaseModel):
    """Pending note that requires human review before export."""

    model_config = ConfigDict(extra="forbid")

    note_id: str = Field(default_factory=new_note_id)
    title: str
    body: str
    provenance: KnowledgeCaptureProvenance
    status: Literal["pending_review"] = "pending_review"
    safety_flags: list[str] = Field(default_factory=list)
    advisory_only: bool = True
    not_detection_source: bool = True
    not_proof: bool = True
    advisory_boundary: str = ADVISORY_ONLY_WARNING


class ApprovedKnowledgeNote(BaseModel):
    """Human-approved note eligible for advisory export."""

    model_config = ConfigDict(extra="forbid")

    note_id: str
    source_candidate_id: str
    title: str
    body: str
    provenance: KnowledgeCaptureProvenance
    approved_at: datetime
    approved_by: str
    approval_notes: str | None = None
    status: Literal["approved"] = "approved"
    safety_flags: list[str] = Field(default_factory=list)
    advisory_only: bool = True
    not_detection_source: bool = True
    not_proof: bool = True
    advisory_boundary: str = ADVISORY_ONLY_WARNING


class RejectedKnowledgeNote(BaseModel):
    """Human-rejected note retained for provenance but never exportable."""

    model_config = ConfigDict(extra="forbid")

    note_id: str
    source_candidate_id: str
    title: str
    body: str
    provenance: KnowledgeCaptureProvenance
    rejected_at: datetime
    rejected_by: str
    rejection_reason: str
    status: Literal["rejected"] = "rejected"
    safety_flags: list[str] = Field(default_factory=list)
    advisory_only: bool = True
    not_detection_source: bool = True
    not_proof: bool = True
    advisory_boundary: str = ADVISORY_ONLY_WARNING


class RagIngestionCandidate(BaseModel):
    """Markdown-ready advisory snippet for future reviewed RAG ingestion."""

    model_config = ConfigDict(extra="forbid")

    source_note_id: str
    title: str
    markdown: str
    provenance: KnowledgeCaptureProvenance
    advisory_only: bool = True
    not_detection_source: bool = True
    not_proof: bool = True
    advisory_boundary: str = ADVISORY_ONLY_WARNING


class GraphNodeCandidate(BaseModel):
    """Advisory-only graph node candidate derived from an approved note."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    source_note_id: str
    label: str
    node_type: str = "knowledge_note_candidate"
    summary: str
    provenance: KnowledgeCaptureProvenance
    advisory_only: bool = True
    not_detection_source: bool = True
    not_proof: bool = True


class GraphEdgeCandidate(BaseModel):
    """Advisory-only graph edge candidate derived from an approved note."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str
    source_note_id: str
    source_node_id: str
    target_node_id: str
    relation: str = "ADVISORY_CONTEXT_FOR"
    provenance: KnowledgeCaptureProvenance
    advisory_only: bool = True
    not_detection_source: bool = True
    not_proof: bool = True


__all__ = [
    "ADVISORY_ONLY_WARNING",
    "CandidateKnowledgeNote",
    "ApprovedKnowledgeNote",
    "ConfidenceLabel",
    "GraphEdgeCandidate",
    "GraphNodeCandidate",
    "HARD_REJECT_SAFETY_FLAGS",
    "KnowledgeCaptureProvenance",
    "KnowledgeCaptureSafetyError",
    "KnowledgeNoteStatus",
    "RagIngestionCandidate",
    "RejectedKnowledgeNote",
    "FLAG_GRAPH_DETECTION_SOURCE",
    "FLAG_MISSING_PROVENANCE",
    "FLAG_SECRET_OR_PII",
    "FLAG_SIMILAR_CASE_PROOF",
    "FLAG_UNSAFE_CONTENT",
    "FLAG_VERDICT_OVERRIDE",
    "new_note_id",
    "utc_now",
]
