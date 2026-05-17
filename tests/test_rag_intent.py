import sys

from modules.rag_intent import (
    build_rag_retrieval_plan,
    classify_rag_intent,
    extract_rag_ids,
    has_missing_ids,
    lookup_extracted_ids,
)
from modules.rag_types import ExtractedIds


def normalized_ids(text: str) -> list[str]:
    return [item.normalized for item in extract_rag_ids(text).items]


def test_extract_rag_ids_extracts_ev_id_and_normalizes_uppercase() -> None:
    ids = extract_rag_ids("Please explain ev-003 and EV 004.")

    assert [item.normalized for item in ids.items] == ["EV-003", "EV-004"]
    assert ids.items[0].kind == "evidence_id"


def test_extract_rag_ids_extracts_f_id() -> None:
    ids = extract_rag_ids("Why did f-002 matter?")

    assert ids.values_by_kind("finding_id") == ["F-002"]


def test_extract_rag_ids_extracts_inc_id() -> None:
    ids = extract_rag_ids("Open inc-abc-001 for context.")

    assert ids.values_by_kind("incident_id") == ["INC-ABC-001"]


def test_extract_rag_ids_extracts_rule_ids() -> None:
    assert normalized_ids("Compare cmd-001, XSS-001, SQLI-001, and PATH-001.") == [
        "CMD-001",
        "XSS-001",
        "SQLI-001",
        "PATH-001",
    ]


def test_extract_rag_ids_extracts_mitre_ids() -> None:
    assert normalized_ids("This maps to t1059 and T1190.") == ["T1059", "T1190"]


def test_extract_rag_ids_deduplicates_while_preserving_order() -> None:
    assert normalized_ids("ev-003 CMD-001 EV 003 cmd-001 F-001") == [
        "EV-003",
        "CMD-001",
        "F-001",
    ]


def test_classify_rag_intent_returns_evidence_question_for_ev_id_question() -> None:
    decision = classify_rag_intent("EV-003 是什麼證據？")

    assert decision.intent == "evidence_question"
    assert decision.confidence == "HIGH"
    assert decision.requires_context is True


def test_classify_rag_intent_returns_finding_question_for_f_id_question() -> None:
    decision = classify_rag_intent("請解釋 F-001")

    assert decision.intent == "finding_question"
    assert decision.confidence == "HIGH"
    assert decision.requires_context is True


def test_classify_rag_intent_returns_rule_question_for_cmd_id_question() -> None:
    decision = classify_rag_intent("CMD-001 為什麼命中？")

    assert decision.intent == "rule_question"
    assert decision.confidence == "HIGH"


def test_classify_rag_intent_returns_report_question_for_monitor_question() -> None:
    decision = classify_rag_intent("為什麼是 MONITOR")

    assert decision.intent == "report_question"
    assert decision.requires_context is True


def test_classify_rag_intent_returns_incident_response_for_next_step_question() -> None:
    decision = classify_rag_intent("下一步要查什麼")

    assert decision.intent == "incident_response"
    assert decision.requires_context is True


def test_classify_rag_intent_returns_false_positive_question_for_false_positive_text() -> None:
    decision = classify_rag_intent("這會不會是誤判？")

    assert decision.intent == "false_positive_question"


def test_classify_rag_intent_returns_attack_knowledge_for_xss_question() -> None:
    decision = classify_rag_intent("XSS 是什麼")

    assert decision.intent == "attack_knowledge"
    assert decision.requires_context is False


def test_classify_rag_intent_returns_unknown_with_low_confidence_for_unrelated_text() -> None:
    decision = classify_rag_intent("Please summarize today's lunch menu.")

    assert decision.intent == "unknown"
    assert decision.confidence == "LOW"


def test_unknown_intent_requires_confidence_low() -> None:
    decision = classify_rag_intent("Unrelated notebook reminder.")

    assert decision.intent == "unknown"
    assert decision.confidence == "LOW"


def test_build_rag_retrieval_plan_returns_report_explainer_filter_for_report_question() -> None:
    plan = build_rag_retrieval_plan("為什麼是 MONITOR")

    assert plan.intent == "report_question"
    assert plan.preferred_doc_types == ["report_explainer"]
    assert plan.metadata_filters == {"doc_type": "report_explainer"}


def test_build_rag_retrieval_plan_includes_exact_ids() -> None:
    plan = build_rag_retrieval_plan("Explain EV-003")

    assert plan.exact_ids.values_by_kind("evidence_id") == ["EV-003"]


def test_build_rag_retrieval_plan_for_rule_question_includes_rule_id() -> None:
    plan = build_rag_retrieval_plan("CMD-001 是哪條規則？")

    assert plan.intent == "rule_question"
    assert plan.preferred_doc_types == ["detection_rule", "report_explainer"]
    assert plan.exact_ids.values_by_kind("rule_id") == ["CMD-001"]


def test_lookup_extracted_ids_marks_existing_and_missing_ids() -> None:
    extracted_ids = extract_rag_ids("EV-001 EV-999 CMD-001")

    result = lookup_extracted_ids(extracted_ids, {"EV-001", "CMD-001"})

    assert result == {"EV-001": True, "EV-999": False, "CMD-001": True}
    assert has_missing_ids(result) is True


def test_lookup_extracted_ids_normalizes_available_ids() -> None:
    extracted_ids = extract_rag_ids("ev-001 cmd-001")

    result = lookup_extracted_ids(extracted_ids, ["ev-001", "cmd-001"])

    assert result == {"EV-001": True, "CMD-001": True}
    assert has_missing_ids(result) is False


def test_lookup_helpers_do_not_require_filesystem_or_chroma() -> None:
    result = lookup_extracted_ids(ExtractedIds(), [])

    assert result == {}


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
