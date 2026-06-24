"""Deterministic candidate extraction and safety filtering."""

from __future__ import annotations

import re
from datetime import datetime
from collections.abc import Iterable

from .types import (
    CandidateKnowledgeNote,
    ConfidenceLabel,
    FLAG_GRAPH_DETECTION_SOURCE,
    FLAG_MISSING_PROVENANCE,
    FLAG_SECRET_OR_PII,
    FLAG_SIMILAR_CASE_PROOF,
    FLAG_UNSAFE_CONTENT,
    FLAG_VERDICT_OVERRIDE,
    KnowledgeCaptureProvenance,
    KnowledgeCaptureSafetyError,
    new_note_id,
    utc_now,
)

UNSAFE_CONTENT_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bexploit\b",
        r"\bpoc\b",
        r"proof[- ]of[- ]concept",
        r"traffic generation",
        r"generate attack traffic",
        r"attack traffic",
        r"load testing",
        r"stress testing",
        r"offensive automation",
        r"weaponized",
    )
)

VERDICT_OVERRIDE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"change\s+risk\s+level",
        r"set\s+risk\s+level",
        r"risk\s+level\s+to\s+low",
        r"override\s+(risk|decision|verdict)",
        r"change\s+decision",
        r"force\s+decision",
        r"replace\s+official\s+verdict",
    )
)

SIMILAR_CASE_PROOF_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"similar cases?\s+(prove|proves|proved|confirmed|confirm|demonstrate|demonstrates)",
        r"case\s+history\s+(prove|proves|proved|confirmed|confirms)",
        r"approved\s+cases?\s+(prove|proves|proved|confirmed|confirms)",
    )
)

GRAPH_DETECTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"graph\s+(is|was)\s+the\s+detection\s+source",
        r"graph\s+(detected|identified|revealed)\s+the\s+attack",
        r"graph\s+source\s+of\s+detection",
    )
)

SECRET_OR_PII_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"api[_-]?key\s*[:=]",
        r"secret\s*[:=]",
        r"password\s*[:=]",
        r"bearer\s+[a-z0-9._-]{12,}",
        r"-----BEGIN\s+(RSA|OPENSSH|PRIVATE)\s+KEY-----",
    )
)


def compact_unique(values: Iterable[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if item and item not in result:
            result.append(item)
    return result


def evaluate_safety_flags(text: str, provenance: KnowledgeCaptureProvenance | None = None) -> list[str]:
    flags: list[str] = []
    if provenance is None or not _has_required_provenance(provenance):
        flags.append(FLAG_MISSING_PROVENANCE)
    if _matches_any(UNSAFE_CONTENT_PATTERNS, text):
        flags.append(FLAG_UNSAFE_CONTENT)
    if _matches_any(VERDICT_OVERRIDE_PATTERNS, text):
        flags.append(FLAG_VERDICT_OVERRIDE)
    if _matches_any(SIMILAR_CASE_PROOF_PATTERNS, text):
        flags.append(FLAG_SIMILAR_CASE_PROOF)
    if _matches_any(GRAPH_DETECTION_PATTERNS, text):
        flags.append(FLAG_GRAPH_DETECTION_SOURCE)
    if _matches_any(SECRET_OR_PII_PATTERNS, text):
        flags.append(FLAG_SECRET_OR_PII)
    return compact_unique(flags)


def build_candidate_knowledge_note(
    *,
    title: str,
    body: str,
    source_event_id: str,
    source_question: str,
    source_answer_summary: str,
    official_risk_level: str,
    official_decision: str,
    created_by: str,
    source_evidence_ids: Iterable[str] | None = None,
    source_rule_ids: Iterable[str] | None = None,
    source_gap_ids: Iterable[str] | None = None,
    source_rag_ids: Iterable[str] | None = None,
    source_case_ids: Iterable[str] | None = None,
    source_graph_ids: Iterable[str] | None = None,
    confidence_label: ConfidenceLabel = "UNKNOWN",
    note_id: str | None = None,
    created_at: datetime | None = None,
    reject_unsafe: bool = True,
) -> CandidateKnowledgeNote:
    """Build a pending note from already-reviewed local strings.

    The extractor is deterministic and does not call LLMs, RAG, graph builders,
    or external services. By default, unsafe or provenance-poor content is
    rejected before it enters the pending queue.
    """

    provenance = KnowledgeCaptureProvenance(
        source_event_id=str(source_event_id or "").strip(),
        source_question=str(source_question or "").strip(),
        source_answer_summary=str(source_answer_summary or "").strip(),
        source_evidence_ids=compact_unique(source_evidence_ids),
        source_rule_ids=compact_unique(source_rule_ids),
        source_gap_ids=compact_unique(source_gap_ids),
        source_rag_ids=compact_unique(source_rag_ids),
        source_case_ids=compact_unique(source_case_ids),
        source_graph_ids=compact_unique(source_graph_ids),
        official_risk_level=str(official_risk_level or "").strip(),
        official_decision=str(official_decision or "").strip(),
        created_at=created_at or utc_now(),
        created_by=str(created_by or "").strip(),
        status="pending_review",
        confidence_label=confidence_label,
    )
    combined_text = "\n".join([title, body, source_question, source_answer_summary])
    safety_flags = evaluate_safety_flags(combined_text, provenance)
    if reject_unsafe and safety_flags:
        raise KnowledgeCaptureSafetyError(
            "Knowledge note requires human-safe provenance before pending review.", safety_flags
        )
    provenance = provenance.model_copy(update={"safety_flags": safety_flags})
    return CandidateKnowledgeNote(
        note_id=note_id or new_note_id(),
        title=str(title or "").strip(),
        body=str(body or "").strip(),
        provenance=provenance,
        safety_flags=safety_flags,
    )


def _matches_any(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _has_required_provenance(provenance: KnowledgeCaptureProvenance) -> bool:
    return bool(
        provenance.source_event_id.strip()
        and provenance.created_by.strip()
        and provenance.official_risk_level.strip()
        and provenance.official_decision.strip()
        and provenance.source_reference_ids()
    )


__all__ = ["build_candidate_knowledge_note", "compact_unique", "evaluate_safety_flags"]
