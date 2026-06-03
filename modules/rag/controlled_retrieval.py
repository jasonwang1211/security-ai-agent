"""Controlled curated source selection for Mode 3 RAG questions.

This module is deterministic and metadata-only. It does not call Chroma,
embeddings, LLMs, graph builders, or ingest code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.rag.intent import build_rag_retrieval_plan
from modules.rag.metadata import KnowledgeDocMetadata

APPROVED_REVIEW_STATUS = "approved_for_runtime_promotion"


@dataclass(frozen=True)
class ControlledRetrievalMatch:
    metadata: KnowledgeDocMetadata
    score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ControlledRetrievalResult:
    matches: tuple[ControlledRetrievalMatch, ...]

    @property
    def has_matches(self) -> bool:
        return bool(self.matches)

    @property
    def source_paths(self) -> list[str]:
        return [
            match.metadata.source_path
            for match in self.matches
            if match.metadata.source_path
        ]


def select_controlled_sources(
    question: str,
    metadata_items: list[KnowledgeDocMetadata],
    *,
    limit: int = 3,
) -> ControlledRetrievalResult:
    """Return approved curated KB matches for exact IDs and reviewed concepts."""

    if not question.strip() or limit < 1:
        return ControlledRetrievalResult(matches=())

    plan = build_rag_retrieval_plan(question)
    matches = [
        match
        for metadata in metadata_items
        if _is_approved(metadata)
        for match in [_score_metadata(question, metadata, plan)]
        if match.score > 0
    ]
    matches.sort(key=lambda match: (-match.score, match.metadata.source_path or match.metadata.doc_id))
    return ControlledRetrievalResult(matches=tuple(matches[:limit]))


def _is_approved(metadata: KnowledgeDocMetadata) -> bool:
    return metadata.review_status == APPROVED_REVIEW_STATUS


def _score_metadata(question: str, metadata: KnowledgeDocMetadata, plan) -> ControlledRetrievalMatch:
    normalized_question = _normalize(question)
    score = 0
    reasons: list[str] = []

    for alias in _document_aliases(metadata):
        if _phrase_in_question(alias, normalized_question):
            score += 90
            reasons.append(f"matched document alias {alias}")

    for rule_id in plan.exact_ids.values_by_kind("rule_id"):
        if _contains_normalized(metadata.rule_ids, rule_id):
            score += 100
            reasons.append(f"matched rule_id {rule_id}")

    for attack_type in metadata.attack_types:
        if _phrase_in_question(attack_type, normalized_question):
            score += 80
            reasons.append(f"matched attack_type {attack_type}")

    for evidence_type in metadata.evidence_types:
        if _phrase_in_question(evidence_type, normalized_question):
            score += 70
            reasons.append(f"matched evidence_type {evidence_type}")

    for finding_type in metadata.finding_types:
        if _phrase_in_question(finding_type, normalized_question):
            score += 60
            reasons.append(f"matched finding_type {finding_type}")

    for keyword in metadata.keywords:
        if _phrase_in_question(keyword, normalized_question):
            score += 20
            reasons.append(f"matched keyword {keyword}")

    return ControlledRetrievalMatch(
        metadata=metadata,
        score=score,
        reasons=tuple(reasons),
    )


def _contains_normalized(values: list[str], expected: str) -> bool:
    expected_normalized = _normalize(expected)
    return any(_normalize(value) == expected_normalized for value in values)


def _document_aliases(metadata: KnowledgeDocMetadata) -> list[str]:
    aliases: list[str] = []
    if "." in metadata.doc_id:
        aliases.append(metadata.doc_id.rsplit(".", 1)[-1])
    else:
        aliases.append(metadata.doc_id)

    if metadata.source_path:
        aliases.append(Path(metadata.source_path).stem)

    return list(dict.fromkeys(alias for alias in aliases if alias))


def _phrase_in_question(value: str, normalized_question: str) -> bool:
    normalized_value = _normalize(value)
    return bool(normalized_value) and normalized_value in normalized_question


def _normalize(value: str) -> str:
    return " ".join(str(value or "").casefold().replace("_", " ").split())
