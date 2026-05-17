from modules.rag_metadata import KnowledgeDocMetadata
from modules.rag_retrieval_planner import (
    MetadataAwareRetrievalPlan,
    MetadataRetrievalCandidate,
)
from modules.rag_types import (
    AnswerWithSources,
    ExtractedIds,
    RAGConfidence,
    SourceCitation,
    make_insufficient_answer,
)

_INSUFFICIENT_SOURCE_MESSAGE = "目前沒有足夠可引用來源支撐這個回答。"


def source_citation_from_metadata(
    metadata: KnowledgeDocMetadata,
    heading: str | None = None,
) -> SourceCitation:
    return SourceCitation(
        source=metadata.source_path or metadata.doc_id,
        kind="knowledge_doc",
        heading=heading,
        identifier=metadata.doc_id,
        metadata={
            "doc_type": metadata.doc_type,
            "applies_to": metadata.applies_to,
            "related_tools": metadata.related_tools,
            "keywords": metadata.keywords,
        },
    )


def source_citation_from_candidate(
    candidate: MetadataRetrievalCandidate,
) -> SourceCitation:
    citation = source_citation_from_metadata(candidate.metadata)
    citation.metadata["score"] = candidate.score
    citation.metadata["reasons"] = candidate.reasons
    return citation


def build_source_citations(
    candidates: list[MetadataRetrievalCandidate],
    limit: int | None = None,
) -> list[SourceCitation]:
    citations: list[SourceCitation] = []
    seen: set[tuple[str, str | None, str | None]] = set()

    for candidate in candidates:
        citation = source_citation_from_candidate(candidate)
        dedupe_key = (citation.source, citation.identifier, citation.heading)
        if dedupe_key in seen:
            continue

        citations.append(citation)
        seen.add(dedupe_key)

        if limit is not None and len(citations) >= limit:
            break

    return citations


def ids_by_kind_for_answer(extracted_ids: ExtractedIds) -> dict[str, list[str]]:
    return {
        "evidence_ids": extracted_ids.values_by_kind("evidence_id"),
        "finding_ids": extracted_ids.values_by_kind("finding_id"),
        "rule_ids": extracted_ids.values_by_kind("rule_id"),
    }


def assemble_answer_with_sources(
    answer: str,
    citations: list[SourceCitation],
    confidence: RAGConfidence = "MEDIUM",
    evidence_ids: list[str] | None = None,
    finding_ids: list[str] | None = None,
    rule_ids: list[str] | None = None,
    limitations: list[str] | None = None,
) -> AnswerWithSources:
    return AnswerWithSources(
        answer=answer,
        sources=citations,
        evidence_ids=evidence_ids or [],
        finding_ids=finding_ids or [],
        rule_ids=rule_ids or [],
        confidence=confidence,
        limitations=limitations or [],
    )


def build_answer_from_plan(
    answer: str,
    plan: MetadataAwareRetrievalPlan,
    confidence: RAGConfidence = "MEDIUM",
    limitations: list[str] | None = None,
) -> AnswerWithSources:
    citations = build_source_citations(plan.candidates)
    if not citations:
        return make_insufficient_answer(_INSUFFICIENT_SOURCE_MESSAGE)

    answer_ids = ids_by_kind_for_answer(plan.base_plan.exact_ids)
    return assemble_answer_with_sources(
        answer=answer,
        citations=citations,
        confidence=confidence,
        evidence_ids=answer_ids["evidence_ids"],
        finding_ids=answer_ids["finding_ids"],
        rule_ids=answer_ids["rule_ids"],
        limitations=limitations or default_limitations_for_plan(plan),
    )


def default_limitations_for_plan(plan: MetadataAwareRetrievalPlan) -> list[str]:
    limitations: list[str] = []

    if not plan.candidates:
        limitations.append("No metadata-backed source was selected.")

    if (
        plan.base_plan.intent in {"evidence_question", "finding_question", "report_question"}
        and not plan.base_plan.exact_ids.has_any()
    ):
        limitations.append("No exact EV-ID, F-ID, or rule ID was found in the question.")

    if plan.use_vector_search:
        limitations.append("Vector retrieval may be needed for additional context.")

    return limitations
