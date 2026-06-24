"""Local JSONL store for human-approved knowledge capture."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .types import (
    ApprovedKnowledgeNote,
    CandidateKnowledgeNote,
    KnowledgeCaptureSafetyError,
    RejectedKnowledgeNote,
    utc_now,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class KnowledgeCaptureStore:
    """Append-oriented JSONL store with explicit approve/reject transitions."""

    def __init__(self, root: str | Path = "data/knowledge_capture") -> None:
        self.root = Path(root)
        self.pending_path = self.root / "pending_notes.jsonl"
        self.approved_path = self.root / "approved_notes.jsonl"
        self.rejected_path = self.root / "rejected_notes.jsonl"

    def append_pending_note(self, note: CandidateKnowledgeNote) -> CandidateKnowledgeNote:
        if note.safety_flags:
            raise KnowledgeCaptureSafetyError(
                "Flagged knowledge notes cannot enter the pending queue.", list(note.safety_flags)
            )
        self._append_model(self.pending_path, note)
        return note

    def list_pending_notes(self) -> list[CandidateKnowledgeNote]:
        return self._read_models(self.pending_path, CandidateKnowledgeNote)

    def list_approved_notes(self) -> list[ApprovedKnowledgeNote]:
        return self._read_models(self.approved_path, ApprovedKnowledgeNote)

    def list_rejected_notes(self) -> list[RejectedKnowledgeNote]:
        return self._read_models(self.rejected_path, RejectedKnowledgeNote)

    def approve_note(
        self,
        note_id: str,
        *,
        approved_by: str,
        edited_body: str | None = None,
        approval_notes: str | None = None,
    ) -> ApprovedKnowledgeNote:
        pending = self.list_pending_notes()
        note = self._find_pending(pending, note_id)
        if note.safety_flags:
            raise KnowledgeCaptureSafetyError(
                "Flagged knowledge notes cannot be approved.", list(note.safety_flags)
            )
        approved_at = utc_now()
        approved_provenance = note.provenance.model_copy(
            update={
                "status": "approved",
                "approved_at": approved_at,
                "approved_by": approved_by,
            }
        )
        approved = ApprovedKnowledgeNote(
            note_id=note.note_id,
            source_candidate_id=note.note_id,
            title=note.title,
            body=(edited_body if edited_body is not None else note.body).strip(),
            provenance=approved_provenance,
            approved_at=approved_at,
            approved_by=approved_by,
            approval_notes=approval_notes,
            safety_flags=list(note.safety_flags),
        )
        self._write_models(self.pending_path, [item for item in pending if item.note_id != note.note_id])
        self._append_model(self.approved_path, approved)
        return approved

    def reject_note(
        self,
        note_id: str,
        *,
        rejected_by: str,
        rejection_reason: str,
    ) -> RejectedKnowledgeNote:
        pending = self.list_pending_notes()
        note = self._find_pending(pending, note_id)
        rejected_at = utc_now()
        rejected_provenance = note.provenance.model_copy(
            update={
                "status": "rejected",
                "rejected_at": rejected_at,
                "rejected_by": rejected_by,
            }
        )
        rejected = RejectedKnowledgeNote(
            note_id=note.note_id,
            source_candidate_id=note.note_id,
            title=note.title,
            body=note.body,
            provenance=rejected_provenance,
            rejected_at=rejected_at,
            rejected_by=rejected_by,
            rejection_reason=rejection_reason,
            safety_flags=list(note.safety_flags),
        )
        self._write_models(self.pending_path, [item for item in pending if item.note_id != note.note_id])
        self._append_model(self.rejected_path, rejected)
        return rejected

    def _find_pending(self, pending: list[CandidateKnowledgeNote], note_id: str) -> CandidateKnowledgeNote:
        for note in pending:
            if note.note_id == note_id:
                return note
        raise KeyError(f"Pending note not found: {note_id}")

    def _append_model(self, path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(model.model_dump_json())
            file.write("\n")

    def _read_models(self, path: Path, model_type: type[ModelT]) -> list[ModelT]:
        if not path.exists():
            return []
        result: list[ModelT] = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if stripped:
                    result.append(model_type.model_validate_json(stripped))
        return result

    def _write_models(self, path: Path, models: list[BaseModel]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as file:
            for model in models:
                file.write(model.model_dump_json())
                file.write("\n")


__all__ = ["KnowledgeCaptureStore"]
