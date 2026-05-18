import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from modules.eval_cases import (
    AnswerSafetyCase,
    PayloadDetectionCase,
    ReportQACase,
    RouterCase,
    load_all_eval_cases,
    load_answer_safety_cases,
    load_jsonl,
    load_payload_detection_cases,
    load_report_qa_cases,
    load_router_cases,
)


def test_load_jsonl_reads_valid_jsonl(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text('{"id": "one"}\n{"id": "two"}\n', encoding="utf-8")

    assert load_jsonl(path) == [{"id": "one"}, {"id": "two"}]


def test_load_jsonl_ignores_blank_lines(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text('\n{"id": "one"}\n  \n{"id": "two"}\n', encoding="utf-8")

    assert load_jsonl(path) == [{"id": "one"}, {"id": "two"}]


def test_load_jsonl_raises_value_error_with_line_number_on_invalid_json(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text('{"id": "one"}\n{"id": \n', encoding="utf-8")

    with pytest.raises(ValueError, match="line 2"):
        load_jsonl(path)


def test_load_jsonl_rejects_non_object_json_line(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text('{"id": "one"}\n["bad"]\n', encoding="utf-8")

    with pytest.raises(ValueError, match="line 2"):
        load_jsonl(path)


def test_answer_safety_case_validates_safe_case():
    case = AnswerSafetyCase(
        id="safe",
        answer="This is a cited explanation.",
        sources=["knowledge/example.md"],
    )

    assert case.kind == "answer_safety"
    assert case.sources == ["knowledge/example.md"]


def test_answer_safety_case_removes_blank_list_entries():
    case = AnswerSafetyCase(
        id="safe",
        answer="This is a cited explanation.",
        sources=[" knowledge/example.md ", "", "  "],
        expected_findings=[" safe ", ""],
        forbidden_claims=[" blocked ", ""],
    )

    assert case.sources == ["knowledge/example.md"]
    assert case.expected_findings == ["safe"]
    assert case.forbidden_claims == ["blocked"]


def test_report_qa_case_validates_expected_fields():
    case = ReportQACase(
        id="report",
        question="Why MONITOR?",
        expected_contains=["MONITOR"],
        forbidden_contains=["blocked"],
        expected_sources=["knowledge/example.md"],
    )

    assert case.kind == "report_qa"
    assert case.expected_contains == ["MONITOR"]


def test_router_case_validates_expected_route_fields():
    case = RouterCase(
        id="router",
        user_input="<script>alert(1)</script>",
        expected_input_kind="payload_or_event",
        expected_route="payload_triage",
    )

    assert case.kind == "router"
    assert case.expected_route == "payload_triage"


def test_payload_detection_case_validates_expected_status_and_decision():
    case = PayloadDetectionCase(
        id="payload",
        payload="<script>alert(1)</script>",
        expected_status="SUSPICIOUS",
        expected_attack_types=["XSS"],
        expected_decision="MONITOR",
    )

    assert case.kind == "payload_detection"
    assert case.expected_status == "SUSPICIOUS"
    assert case.expected_decision == "MONITOR"


def test_blank_id_is_rejected():
    with pytest.raises(ValidationError):
        AnswerSafetyCase(id=" ", answer="Safe answer.")


def test_blank_required_text_is_rejected():
    with pytest.raises(ValidationError):
        RouterCase(
            id="router",
            user_input=" ",
            expected_input_kind="payload_or_event",
            expected_route="payload_triage",
        )


def test_load_answer_safety_cases_loads_bundled_file():
    cases = load_answer_safety_cases("eval_cases/answer_safety_cases.jsonl")

    assert len(cases) == 5
    assert all(case.kind == "answer_safety" for case in cases)


def test_load_report_qa_cases_loads_bundled_file():
    cases = load_report_qa_cases("eval_cases/report_qa_cases.jsonl")

    assert len(cases) == 5
    assert all(case.kind == "report_qa" for case in cases)


def test_load_router_cases_loads_bundled_file():
    cases = load_router_cases("eval_cases/router_cases.jsonl")

    assert len(cases) == 8
    assert all(case.kind == "router" for case in cases)


def test_load_payload_detection_cases_loads_bundled_file():
    cases = load_payload_detection_cases("eval_cases/payload_detection_cases.jsonl")

    assert len(cases) == 6
    assert all(case.kind == "payload_detection" for case in cases)


def test_load_all_eval_cases_loads_all_four_files():
    cases_by_kind = load_all_eval_cases()

    assert set(cases_by_kind) == {
        "answer_safety",
        "report_qa",
        "router",
        "payload_detection",
    }
    assert sum(len(cases) for cases in cases_by_kind.values()) == 24


def test_all_bundled_cases_have_unique_ids_globally():
    cases_by_kind = load_all_eval_cases()
    ids = [case.id for cases in cases_by_kind.values() for case in cases]

    assert len(ids) == len(set(ids))


def test_bundled_answer_safety_cases_include_forbidden_real_enforcement_claim():
    cases = load_answer_safety_cases("eval_cases/answer_safety_cases.jsonl")

    assert any(
        "fake_enforcement_claim" in case.expected_findings
        and any("firewall" in claim for claim in case.forbidden_claims)
        for case in cases
    )


def test_bundled_report_qa_cases_include_monitor_question():
    cases = load_report_qa_cases("eval_cases/report_qa_cases.jsonl")

    assert any("MONITOR" in case.question for case in cases)


def test_bundled_router_cases_include_unknown_clarification_case():
    cases = load_router_cases("eval_cases/router_cases.jsonl")

    assert any(
        case.expected_input_kind == "unknown" and case.expected_route == "clarification_required"
        for case in cases
    )


def test_bundled_router_cases_use_allowed_kinds_and_routes():
    cases = load_router_cases("eval_cases/router_cases.jsonl")
    allowed_input_kinds = {
        "payload_or_event",
        "raw_log_line",
        "log_file_path",
        "security_knowledge_question",
        "report_followup",
        "incident_export",
        "unknown",
    }
    allowed_routes = {
        "payload_triage",
        "raw_log_translate",
        "log_file_ingest",
        "rag_security_qa",
        "report_followup",
        "incident_json_export",
        "clarification_required",
    }

    assert {case.expected_input_kind for case in cases}.issubset(allowed_input_kinds)
    assert {case.expected_route for case in cases}.issubset(allowed_routes)


def test_bundled_router_cases_cover_required_categories():
    cases = load_router_cases("eval_cases/router_cases.jsonl")
    required_input_kinds = {
        "payload_or_event",
        "raw_log_line",
        "log_file_path",
        "security_knowledge_question",
        "report_followup",
        "incident_export",
        "unknown",
    }

    assert required_input_kinds.issubset({case.expected_input_kind for case in cases})


def test_bundled_payload_detection_cases_include_benign_case():
    cases = load_payload_detection_cases("eval_cases/payload_detection_cases.jsonl")

    assert any(
        case.expected_status == "CLEAN" and case.expected_decision == "ALLOW" for case in cases
    )


def test_bundled_report_explainer_source_paths_exist():
    cases_by_kind = load_all_eval_cases()
    report_explainer_prefix = "knowledge/blue_team/report_explainer/"
    source_paths: list[str] = []

    for cases in cases_by_kind.values():
        for case in cases:
            source_paths.extend(getattr(case, "sources", []))
            source_paths.extend(getattr(case, "expected_sources", []))

    report_explainer_paths = [
        source.split("#", maxsplit=1)[0]
        for source in source_paths
        if source.startswith(report_explainer_prefix)
    ]

    assert report_explainer_paths
    assert all(Path(source).is_file() for source in report_explainer_paths)


def test_eval_loader_does_not_import_detector_rag_or_llm_runtime_modules():
    forbidden_imports = {
        "app",
        "modules.detector",
        "modules.rag_qa",
        "chromadb",
        "ollama",
        "langchain",
        "torch",
    }
    source = Path("modules/eval_cases.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    assert forbidden_imports.isdisjoint(imported_modules)
