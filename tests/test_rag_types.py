import json

import pytest
from pydantic import ValidationError

from modules.rag_types import (
    AnswerWithSources,
    ExtractedId,
    ExtractedIds,
    RAGIntentDecision,
    RAGRetrievalPlan,
    SourceCitation,
    make_insufficient_answer,
)


def make_source() -> SourceCitation:
    return SourceCitation(
        source="knowledge/blue_team/report_explainer/risk_level_decision.md",
        kind="knowledge_doc",
        heading="Decision",
        identifier="report.risk_level_decision",
    )


def test_source_citation_accepts_valid_knowledge_doc_citation() -> None:
    citation = make_source()

    assert citation.source == "knowledge/blue_team/report_explainer/risk_level_decision.md"
    assert citation.kind == "knowledge_doc"
    assert citation.heading == "Decision"
    assert citation.identifier == "report.risk_level_decision"
    assert citation.metadata == {}


def test_source_citation_rejects_blank_source() -> None:
    with pytest.raises(ValidationError):
        SourceCitation(source=" ", kind="knowledge_doc")


def test_source_citation_rejects_blank_heading_if_provided() -> None:
    with pytest.raises(ValidationError):
        SourceCitation(source="knowledge/example.md", kind="knowledge_doc", heading=" ")


def test_extracted_id_normalizes_rule_id_to_uppercase() -> None:
    extracted = ExtractedId(value="cmd-001", kind="rule_id", normalized="cmd-001")

    assert extracted.normalized == "CMD-001"


def test_extracted_id_normalizes_mitre_id_to_uppercase() -> None:
    extracted = ExtractedId(value="t1059", kind="mitre_technique_id", normalized="t1059")

    assert extracted.normalized == "T1059"


def test_extracted_id_does_not_over_normalize_incident_id() -> None:
    extracted = ExtractedId(value="INC-case-a", kind="incident_id", normalized="INC-case-a")

    assert extracted.normalized == "INC-case-a"


def test_extracted_ids_values_by_kind_returns_expected_normalized_ids() -> None:
    ids = ExtractedIds(
        items=[
            ExtractedId(value="EV-003", kind="evidence_id", normalized="EV-003"),
            ExtractedId(value="cmd-001", kind="rule_id", normalized="CMD-001"),
            ExtractedId(value="CMD-001", kind="rule_id", normalized="CMD-001"),
            ExtractedId(value="xss-001", kind="rule_id", normalized="XSS-001"),
        ]
    )

    assert ids.values_by_kind("rule_id") == ["CMD-001", "XSS-001"]


def test_extracted_ids_has_any_works() -> None:
    assert ExtractedIds().has_any() is False
    assert ExtractedIds(
        items=[ExtractedId(value="F-001", kind="finding_id", normalized="F-001")]
    ).has_any() is True


def test_rag_intent_decision_accepts_report_question() -> None:
    decision = RAGIntentDecision(
        intent="report_question",
        confidence="HIGH",
        reason="Question asks why the report made a decision.",
        requires_context=True,
    )

    assert decision.intent == "report_question"
    assert decision.requires_context is True


def test_rag_intent_decision_rejects_blank_reason() -> None:
    with pytest.raises(ValidationError):
        RAGIntentDecision(intent="report_question", confidence="MEDIUM", reason=" ")


def test_rag_intent_decision_unknown_requires_low_confidence() -> None:
    with pytest.raises(ValidationError):
        RAGIntentDecision(intent="unknown", confidence="MEDIUM", reason="No match.")

    decision = RAGIntentDecision(intent="unknown", confidence="LOW", reason="No match.")
    assert decision.confidence == "LOW"


def test_rag_retrieval_plan_accepts_default_fields() -> None:
    plan = RAGRetrievalPlan(intent="attack_knowledge", query="Command Injection 防禦")

    assert plan.metadata_filters == {}
    assert plan.exact_ids == ExtractedIds()
    assert plan.preferred_doc_types == []
    assert plan.use_vector_search is True
    assert plan.top_k == 5


def test_rag_retrieval_plan_rejects_blank_query() -> None:
    with pytest.raises(ValidationError):
        RAGRetrievalPlan(intent="attack_knowledge", query=" ")


def test_rag_retrieval_plan_rejects_top_k_zero() -> None:
    with pytest.raises(ValidationError):
        RAGRetrievalPlan(intent="attack_knowledge", query="Command Injection", top_k=0)


def test_rag_retrieval_plan_rejects_top_k_greater_than_twenty() -> None:
    with pytest.raises(ValidationError):
        RAGRetrievalPlan(intent="attack_knowledge", query="Command Injection", top_k=21)


def test_answer_with_sources_accepts_valid_answer_with_source() -> None:
    answer = AnswerWithSources(
        answer="Decision means the recommended analyst action.",
        sources=[make_source()],
        confidence="HIGH",
    )

    assert answer.answer == "Decision means the recommended analyst action."
    assert answer.sources[0].heading == "Decision"
    assert answer.confidence == "HIGH"


def test_answer_with_sources_rejects_blank_answer() -> None:
    with pytest.raises(ValidationError):
        AnswerWithSources(answer=" ", sources=[make_source()], confidence="LOW")


def test_answer_with_sources_rejects_empty_sources() -> None:
    with pytest.raises(ValidationError):
        AnswerWithSources(answer="Insufficient context.", sources=[], confidence="LOW")


def test_answer_with_sources_normalizes_evidence_finding_and_rule_ids() -> None:
    answer = AnswerWithSources(
        answer="The report references these IDs.",
        sources=[make_source()],
        evidence_ids=[" ev-003 ", "", "EV-004"],
        finding_ids=[" f-001 "],
        rule_ids=["cmd-001", " "],
        confidence="MEDIUM",
    )

    assert answer.evidence_ids == ["EV-003", "EV-004"]
    assert answer.finding_ids == ["F-001"]
    assert answer.rule_ids == ["CMD-001"]


def test_answer_with_sources_removes_blank_limitations() -> None:
    answer = AnswerWithSources(
        answer="Only partial context was available.",
        sources=[make_source()],
        confidence="LOW",
        limitations=[" ", "Current incident context is unavailable.", ""],
    )

    assert answer.limitations == ["Current incident context is unavailable."]


def test_model_serialization_works_with_model_dump_and_model_dump_json() -> None:
    answer = AnswerWithSources(
        answer="CMD-001 matched command injection metadata.",
        sources=[SourceCitation(source="detections/blue_team/command_injection.yml", kind="detection_rule")],
        rule_ids=["cmd-001"],
        confidence="HIGH",
    )

    dumped = answer.model_dump()
    dumped_json = json.loads(answer.model_dump_json())

    assert dumped["rule_ids"] == ["CMD-001"]
    assert dumped_json["sources"][0]["kind"] == "detection_rule"


def test_make_insufficient_answer_returns_low_confidence_answer() -> None:
    answer = make_insufficient_answer("Information is insufficient.")

    assert answer.answer == "Information is insufficient."
    assert answer.confidence == "LOW"
    assert answer.limitations == ["Information is insufficient from available sources."]
