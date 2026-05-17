import sys

import pytest
from pydantic import ValidationError

from modules.rag_intent import build_rag_retrieval_plan
from modules.rag_metadata import KnowledgeDocMetadata, load_metadata_from_directory
from modules.rag_retrieval_planner import (
    MetadataAwareRetrievalPlan,
    MetadataRetrievalCandidate,
    build_metadata_aware_retrieval_plan,
)
from modules.rag_source_assembly import (
    assemble_answer_with_sources,
    build_answer_from_plan,
    build_source_citations,
    default_limitations_for_plan,
    ids_by_kind_for_answer,
    source_citation_from_candidate,
    source_citation_from_metadata,
)
from modules.rag_types import ExtractedId, ExtractedIds, SourceCitation


def make_metadata(
    doc_id: str = "report.risk_level_decision",
    doc_type: str = "report_explainer",
    applies_to: list[str] | None = None,
    related_tools: list[str] | None = None,
    keywords: list[str] | None = None,
    source_path: str | None = "knowledge/blue_team/report_explainer/risk_level_decision.md",
) -> KnowledgeDocMetadata:
    return KnowledgeDocMetadata(
        doc_id=doc_id,
        doc_type=doc_type,
        applies_to=applies_to or [],
        related_tools=related_tools or [],
        keywords=keywords or [],
        source_path=source_path,
    )


def make_candidate(
    metadata: KnowledgeDocMetadata | None = None,
    score: int = 7,
    reasons: list[str] | None = None,
) -> MetadataRetrievalCandidate:
    return MetadataRetrievalCandidate(
        metadata=metadata or make_metadata(),
        score=score,
        reasons=reasons or ["matched metadata_filters", "preferred doc_type"],
    )


def make_citation() -> SourceCitation:
    return SourceCitation(
        source="knowledge/blue_team/report_explainer/risk_level_decision.md",
        kind="knowledge_doc",
        identifier="report.risk_level_decision",
    )


def test_source_citation_from_metadata_uses_source_path_when_available() -> None:
    citation = source_citation_from_metadata(make_metadata())

    assert citation.source == "knowledge/blue_team/report_explainer/risk_level_decision.md"
    assert citation.identifier == "report.risk_level_decision"
    assert citation.kind == "knowledge_doc"


def test_source_citation_from_metadata_falls_back_to_doc_id_when_source_path_missing() -> None:
    citation = source_citation_from_metadata(make_metadata(source_path=None))

    assert citation.source == "report.risk_level_decision"


def test_source_citation_from_metadata_includes_lightweight_metadata() -> None:
    metadata = make_metadata(
        applies_to=["Security Triage Report"],
        related_tools=["report_followup"],
        keywords=["decision"],
    )

    citation = source_citation_from_metadata(metadata, heading="Decision")

    assert citation.heading == "Decision"
    assert citation.metadata == {
        "doc_type": "report_explainer",
        "applies_to": ["Security Triage Report"],
        "related_tools": ["report_followup"],
        "keywords": ["decision"],
    }


def test_source_citation_from_candidate_includes_score_and_reasons() -> None:
    candidate = make_candidate(score=9, reasons=["preferred doc_type"])

    citation = source_citation_from_candidate(candidate)

    assert citation.metadata["score"] == 9
    assert citation.metadata["reasons"] == ["preferred doc_type"]


def test_build_source_citations_preserves_order() -> None:
    first = make_candidate(make_metadata(doc_id="report.a", source_path="a.md"))
    second = make_candidate(make_metadata(doc_id="report.b", source_path="b.md"))

    citations = build_source_citations([first, second])

    assert [citation.identifier for citation in citations] == ["report.a", "report.b"]


def test_build_source_citations_deduplicates_duplicate_candidates() -> None:
    metadata = make_metadata()

    citations = build_source_citations([make_candidate(metadata), make_candidate(metadata)])

    assert len(citations) == 1


def test_build_source_citations_respects_limit() -> None:
    first = make_candidate(make_metadata(doc_id="report.a", source_path="a.md"))
    second = make_candidate(make_metadata(doc_id="report.b", source_path="b.md"))

    citations = build_source_citations([first, second], limit=1)

    assert len(citations) == 1
    assert citations[0].identifier == "report.a"


def test_build_source_citations_returns_empty_list_for_empty_candidates() -> None:
    assert build_source_citations([]) == []


def test_ids_by_kind_for_answer_returns_evidence_finding_rule_ids() -> None:
    extracted_ids = ExtractedIds(
        items=[
            ExtractedId(value="ev-003", kind="evidence_id", normalized="EV-003"),
            ExtractedId(value="F-001", kind="finding_id", normalized="F-001"),
            ExtractedId(value="cmd-001", kind="rule_id", normalized="CMD-001"),
        ]
    )

    assert ids_by_kind_for_answer(extracted_ids) == {
        "evidence_ids": ["EV-003"],
        "finding_ids": ["F-001"],
        "rule_ids": ["CMD-001"],
    }


def test_ids_by_kind_for_answer_excludes_incident_and_mitre_ids() -> None:
    extracted_ids = ExtractedIds(
        items=[
            ExtractedId(value="INC-001", kind="incident_id", normalized="INC-001"),
            ExtractedId(value="T1059", kind="mitre_technique_id", normalized="T1059"),
        ]
    )

    assert ids_by_kind_for_answer(extracted_ids) == {
        "evidence_ids": [],
        "finding_ids": [],
        "rule_ids": [],
    }


def test_assemble_answer_with_sources_creates_valid_answer_with_sources() -> None:
    answer = assemble_answer_with_sources(
        answer="The report decision is supported by the selected source.",
        citations=[make_citation()],
        evidence_ids=["ev-003"],
        confidence="HIGH",
        limitations=["Limited to selected metadata."],
    )

    assert answer.evidence_ids == ["EV-003"]
    assert answer.confidence == "HIGH"
    assert answer.sources[0].identifier == "report.risk_level_decision"


def test_assemble_answer_with_sources_rejects_empty_citations_through_model_validation() -> None:
    with pytest.raises(ValidationError):
        assemble_answer_with_sources(
            answer="This answer has no citations.",
            citations=[],
        )


def test_build_answer_from_plan_creates_answer_with_sources_from_candidates() -> None:
    plan = MetadataAwareRetrievalPlan(
        base_plan=build_rag_retrieval_plan("Why is the decision MONITOR?"),
        candidates=[make_candidate()],
        use_vector_search=False,
    )

    answer = build_answer_from_plan("The decision is supported by report metadata.", plan)

    assert answer.answer == "The decision is supported by report metadata."
    assert answer.sources[0].identifier == "report.risk_level_decision"
    assert answer.confidence == "MEDIUM"


def test_build_answer_from_plan_populates_evidence_finding_rule_ids_from_exact_ids() -> None:
    plan = MetadataAwareRetrievalPlan(
        base_plan=build_rag_retrieval_plan("Explain EV-003 F-001 CMD-001"),
        candidates=[make_candidate()],
        use_vector_search=False,
    )

    answer = build_answer_from_plan("The selected source supports these IDs.", plan)

    assert answer.evidence_ids == ["EV-003"]
    assert answer.finding_ids == ["F-001"]
    assert answer.rule_ids == ["CMD-001"]


def test_build_answer_from_plan_returns_insufficient_answer_when_no_citations_exist() -> None:
    plan = MetadataAwareRetrievalPlan(
        base_plan=build_rag_retrieval_plan("unrelated"),
        candidates=[],
    )

    answer = build_answer_from_plan("Unsupported answer.", plan)

    assert answer.answer == "目前沒有足夠可引用來源支撐這個回答。"
    assert answer.confidence == "LOW"
    assert answer.sources[0].source == "insufficient_information"


def test_default_limitations_for_plan_includes_no_source_limitation_when_candidates_empty() -> None:
    plan = MetadataAwareRetrievalPlan(
        base_plan=build_rag_retrieval_plan("unrelated"),
        candidates=[],
        use_vector_search=False,
    )

    assert "No metadata-backed source was selected." in default_limitations_for_plan(plan)


def test_default_limitations_for_plan_includes_vector_retrieval_limitation_when_enabled() -> None:
    plan = MetadataAwareRetrievalPlan(
        base_plan=build_rag_retrieval_plan("Why is the decision MONITOR?"),
        candidates=[make_candidate()],
        use_vector_search=True,
    )

    assert "Vector retrieval may be needed for additional context." in default_limitations_for_plan(plan)


def test_real_report_explainer_metadata_can_be_assembled_into_answer_sources() -> None:
    metadata_items = load_metadata_from_directory("knowledge/blue_team/report_explainer")
    plan = build_metadata_aware_retrieval_plan("Why is the decision MONITOR?", metadata_items)

    answer = build_answer_from_plan("The decision is supported by report explainer metadata.", plan)

    assert answer.sources
    assert any("report_explainer" in citation.source for citation in answer.sources)


def test_module_does_not_import_rag_runtime_modules() -> None:
    forbidden_modules = [
        "app",
        "modules.rag_qa",
        "langchain",
        "chromadb",
        "sentence_transformers",
        "ollama",
        "torch",
    ]

    for module_name in forbidden_modules:
        assert module_name not in sys.modules
