import sys

from modules.rag_intent import build_rag_retrieval_plan
from modules.rag_metadata import KnowledgeDocMetadata, load_metadata_from_directory
from modules.rag_retrieval_planner import (
    MetadataAwareRetrievalPlan,
    MetadataRetrievalCandidate,
    build_metadata_aware_retrieval_plan,
    metadata_matches_filters,
    score_metadata_candidate,
    select_metadata_candidates,
)


def make_metadata(
    doc_id: str = "report.risk_level_decision",
    doc_type: str = "report_explainer",
    applies_to: list[str] | None = None,
    keywords: list[str] | None = None,
    rule_ids: list[str] | None = None,
    mitre_techniques: list[str] | None = None,
    related_tools: list[str] | None = None,
    source_path: str | None = "knowledge/blue_team/report_explainer/risk_level_decision.md",
) -> KnowledgeDocMetadata:
    return KnowledgeDocMetadata(
        doc_id=doc_id,
        doc_type=doc_type,
        applies_to=applies_to or [],
        keywords=keywords or [],
        rule_ids=rule_ids or [],
        mitre_techniques=mitre_techniques or [],
        related_tools=related_tools or [],
        source_path=source_path,
    )


def test_metadata_matches_filters_returns_true_for_empty_filters() -> None:
    assert metadata_matches_filters(make_metadata(), {}) is True


def test_metadata_matches_filters_matches_doc_type_exact() -> None:
    metadata = make_metadata(doc_type="report_explainer")

    assert metadata_matches_filters(metadata, {"doc_type": "report_explainer"}) is True
    assert metadata_matches_filters(metadata, {"doc_type": "detection_rule"}) is False


def test_metadata_matches_filters_matches_list_membership_keywords() -> None:
    metadata = make_metadata(keywords=["risk level", "decision"])

    assert metadata_matches_filters(metadata, {"keywords": "decision"}) is True


def test_metadata_matches_filters_matches_list_overlap() -> None:
    metadata = make_metadata(related_tools=["report_followup", "triage"])

    assert metadata_matches_filters(metadata, {"related_tools": ["chat", "report_followup"]}) is True


def test_metadata_matches_filters_returns_false_for_unknown_field() -> None:
    assert metadata_matches_filters(make_metadata(), {"unknown": "value"}) is False


def test_score_metadata_candidate_scores_metadata_filter_match() -> None:
    plan = build_rag_retrieval_plan("為什麼是 MONITOR")
    candidate = score_metadata_candidate(make_metadata(), plan)

    assert candidate.score >= 5
    assert "matched metadata_filters" in candidate.reasons


def test_score_metadata_candidate_scores_preferred_doc_type() -> None:
    plan = build_rag_retrieval_plan("為什麼是 MONITOR")
    candidate = score_metadata_candidate(make_metadata(), plan)

    assert candidate.score >= 4
    assert "preferred doc_type" in candidate.reasons


def test_score_metadata_candidate_scores_rule_id_overlap() -> None:
    plan = build_rag_retrieval_plan("Explain CMD-001")
    candidate = score_metadata_candidate(make_metadata(rule_ids=["CMD-001"]), plan)

    assert candidate.score >= 3
    assert "matched rule_id CMD-001" in candidate.reasons


def test_score_metadata_candidate_scores_mitre_overlap() -> None:
    plan = build_rag_retrieval_plan("Explain T1059")
    candidate = score_metadata_candidate(make_metadata(mitre_techniques=["T1059"]), plan)

    assert candidate.score >= 3
    assert "matched mitre_technique T1059" in candidate.reasons


def test_score_metadata_candidate_scores_keyword_overlap() -> None:
    plan = build_rag_retrieval_plan("Explain the decision")
    candidate = score_metadata_candidate(make_metadata(keywords=["decision"]), plan)

    assert candidate.score >= 2
    assert "matched keyword decision" in candidate.reasons


def test_score_metadata_candidate_includes_deterministic_reasons() -> None:
    plan = build_rag_retrieval_plan("Why did CMD-001 produce this decision?")
    metadata = make_metadata(rule_ids=["CMD-001"], keywords=["decision"])

    candidate = score_metadata_candidate(metadata, plan)

    assert candidate.reasons == [
        "preferred doc_type",
        "matched rule_id CMD-001",
        "matched keyword decision",
    ]


def test_select_metadata_candidates_sorts_by_score_descending() -> None:
    low = make_metadata(doc_id="report.low", keywords=["decision"], source_path="b.md")
    high = make_metadata(doc_id="report.high", rule_ids=["CMD-001"], source_path="a.md")
    plan = build_rag_retrieval_plan("CMD-001 decision")

    candidates = select_metadata_candidates([low, high], plan)

    assert [candidate.metadata.doc_id for candidate in candidates] == ["report.high", "report.low"]


def test_select_metadata_candidates_uses_deterministic_tie_break_by_source_path_or_doc_id() -> None:
    first = make_metadata(doc_id="report.b", keywords=["decision"], source_path="b.md")
    second = make_metadata(doc_id="report.a", keywords=["decision"], source_path="a.md")
    third = make_metadata(doc_id="report.c", keywords=["decision"], source_path=None)
    plan = build_rag_retrieval_plan("decision")

    candidates = select_metadata_candidates([first, third, second], plan)

    assert [candidate.metadata.doc_id for candidate in candidates] == [
        "report.a",
        "report.b",
        "report.c",
    ]


def test_select_metadata_candidates_respects_limit() -> None:
    plan = build_rag_retrieval_plan("decision")
    metadata_items = [
        make_metadata(doc_id="report.a", keywords=["decision"], source_path="a.md"),
        make_metadata(doc_id="report.b", keywords=["decision"], source_path="b.md"),
    ]

    candidates = select_metadata_candidates(metadata_items, plan, limit=1)

    assert len(candidates) == 1


def test_select_metadata_candidates_drops_zero_score_candidates() -> None:
    plan = build_rag_retrieval_plan("unrelated")
    metadata = make_metadata(doc_type="attack_technique", source_path="a.md")

    assert select_metadata_candidates([metadata], plan) == []


def test_build_metadata_aware_retrieval_plan_creates_base_plan_from_question() -> None:
    plan = build_metadata_aware_retrieval_plan("EV-003 是什麼")

    assert isinstance(plan, MetadataAwareRetrievalPlan)
    assert plan.base_plan.intent == "evidence_question"


def test_build_metadata_aware_retrieval_plan_returns_candidates_for_report_question() -> None:
    metadata = make_metadata(keywords=["monitor"])

    plan = build_metadata_aware_retrieval_plan("為什麼是 MONITOR？", [metadata])

    assert plan.candidates
    assert plan.candidates[0].metadata.doc_id == "report.risk_level_decision"


def test_build_metadata_aware_retrieval_plan_returns_empty_candidates_and_warning_when_none_match() -> None:
    metadata = make_metadata(doc_type="attack_technique", source_path="attack.md")

    plan = build_metadata_aware_retrieval_plan("unrelated", [metadata])

    assert plan.candidates == []
    assert plan.warnings == ["No metadata candidates matched the retrieval plan."]
    assert plan.use_vector_search is True


def test_build_metadata_aware_retrieval_plan_with_no_metadata_items_does_not_read_files() -> None:
    plan = build_metadata_aware_retrieval_plan("為什麼是 MONITOR？")

    assert plan.candidates == []
    assert plan.warnings == []
    assert plan.use_vector_search is True


def test_planner_uses_real_report_explainer_metadata_without_runtime_initialization() -> None:
    metadata_items = load_metadata_from_directory("knowledge/blue_team/report_explainer")

    plan = build_metadata_aware_retrieval_plan("為什麼是 MONITOR？", metadata_items)

    assert plan.candidates
    assert plan.candidates[0].metadata.doc_type == "report_explainer"
    assert plan.use_vector_search is True


def test_models_remove_blank_reasons_and_warnings() -> None:
    candidate = MetadataRetrievalCandidate(metadata=make_metadata(), score=1, reasons=[" ", "matched"])
    plan = MetadataAwareRetrievalPlan(
        base_plan=build_rag_retrieval_plan("decision"),
        candidates=[candidate],
        warnings=["", "missing"],
    )

    assert candidate.reasons == ["matched"]
    assert plan.warnings == ["missing"]


def test_planner_module_does_not_import_rag_runtime_modules() -> None:
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
