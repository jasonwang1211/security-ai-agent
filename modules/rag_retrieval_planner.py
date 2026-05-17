import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from modules.rag_intent import build_rag_retrieval_plan
from modules.rag_metadata import KnowledgeDocMetadata
from modules.rag_types import RAGRetrievalPlan


class MetadataRetrievalCandidate(BaseModel):
    metadata: KnowledgeDocMetadata
    score: int = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)

    @field_validator("reasons")
    @classmethod
    def reasons_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return [reason.strip() for reason in value if reason.strip()]


class MetadataAwareRetrievalPlan(BaseModel):
    base_plan: RAGRetrievalPlan
    candidates: list[MetadataRetrievalCandidate] = Field(default_factory=list)
    use_vector_search: bool = True
    warnings: list[str] = Field(default_factory=list)

    @field_validator("warnings")
    @classmethod
    def warnings_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return [warning.strip() for warning in value if warning.strip()]


def metadata_matches_filters(
    metadata: KnowledgeDocMetadata,
    filters: dict[str, object],
) -> bool:
    if not filters:
        return True

    for field_name, filter_value in filters.items():
        metadata_value = getattr(metadata, field_name, None)
        if metadata_value is None:
            return False
        if not _value_matches_filter(metadata_value, filter_value):
            return False

    return True


def score_metadata_candidate(
    metadata: KnowledgeDocMetadata,
    plan: RAGRetrievalPlan,
) -> MetadataRetrievalCandidate:
    score = 0
    reasons: list[str] = []

    if plan.metadata_filters and metadata_matches_filters(metadata, plan.metadata_filters):
        score += 5
        reasons.append("matched metadata_filters")

    if metadata.doc_type in plan.preferred_doc_types:
        score += 4
        reasons.append("preferred doc_type")

    for rule_id in _overlap(plan.exact_ids.values_by_kind("rule_id"), metadata.rule_ids):
        score += 3
        reasons.append(f"matched rule_id {rule_id}")

    for mitre_id in _overlap(
        plan.exact_ids.values_by_kind("mitre_technique_id"),
        metadata.mitre_techniques,
    ):
        score += 3
        reasons.append(f"matched mitre_technique {mitre_id}")

    for keyword in _query_keyword_matches(plan.query, metadata.keywords):
        score += 2
        reasons.append(f"matched keyword {keyword}")

    if _text_list_overlaps(plan.query, metadata.applies_to):
        score += 1
        reasons.append("matched applies_to")

    return MetadataRetrievalCandidate(metadata=metadata, score=score, reasons=reasons)


def select_metadata_candidates(
    metadata_items: list[KnowledgeDocMetadata],
    plan: RAGRetrievalPlan,
    limit: int | None = None,
) -> list[MetadataRetrievalCandidate]:
    candidates = [
        candidate
        for candidate in (score_metadata_candidate(metadata, plan) for metadata in metadata_items)
        if candidate.score > 0
    ]
    candidates.sort(key=lambda candidate: (-candidate.score, _candidate_sort_key(candidate)))

    if limit is not None:
        return candidates[:limit]
    return candidates


def build_metadata_aware_retrieval_plan(
    question: str,
    metadata_items: list[KnowledgeDocMetadata] | None = None,
    limit: int | None = None,
) -> MetadataAwareRetrievalPlan:
    base_plan = build_rag_retrieval_plan(question)
    candidates: list[MetadataRetrievalCandidate] = []
    warnings: list[str] = []

    if metadata_items is not None:
        candidates = select_metadata_candidates(metadata_items, base_plan, limit=limit)
        if not candidates:
            warnings.append("No metadata candidates matched the retrieval plan.")

    return MetadataAwareRetrievalPlan(
        base_plan=base_plan,
        candidates=candidates,
        use_vector_search=base_plan.use_vector_search or not candidates,
        warnings=warnings,
    )


def _value_matches_filter(metadata_value: Any, filter_value: object) -> bool:
    if isinstance(metadata_value, list):
        metadata_values = {_normalize_match_value(value) for value in metadata_value}
        filter_values = _filter_values(filter_value)
        return bool(metadata_values.intersection(filter_values))

    metadata_scalar = _normalize_match_value(metadata_value)
    filter_values = _filter_values(filter_value)
    return metadata_scalar in filter_values


def _filter_values(filter_value: object) -> set[str]:
    if isinstance(filter_value, list | tuple | set):
        return {_normalize_match_value(value) for value in filter_value}
    return {_normalize_match_value(filter_value)}


def _normalize_match_value(value: object) -> str:
    return str(value).strip().casefold()


def _overlap(left: list[str], right: list[str]) -> list[str]:
    right_values = {_normalize_match_value(value) for value in right}
    return [value for value in left if _normalize_match_value(value) in right_values]


def _query_keyword_matches(query: str, keywords: list[str]) -> list[str]:
    query_terms = _tokenize(query)
    matches: list[str] = []

    for keyword in keywords:
        keyword_terms = _tokenize(keyword)
        normalized_keyword = _normalize_match_value(keyword)
        if normalized_keyword and (
            normalized_keyword in _normalize_match_value(query)
            or bool(query_terms.intersection(keyword_terms))
        ):
            matches.append(keyword)

    return matches


def _text_list_overlaps(query: str, values: list[str]) -> bool:
    query_terms = _tokenize(query)
    normalized_query = _normalize_match_value(query)

    for value in values:
        normalized_value = _normalize_match_value(value)
        if normalized_value and normalized_value in normalized_query:
            return True
        if query_terms.intersection(_tokenize(value)):
            return True

    return False


def _tokenize(text: str) -> set[str]:
    return {token.casefold() for token in re.findall(r"[A-Za-z0-9]+", text)}


def _candidate_sort_key(candidate: MetadataRetrievalCandidate) -> str:
    return candidate.metadata.source_path or candidate.metadata.doc_id
