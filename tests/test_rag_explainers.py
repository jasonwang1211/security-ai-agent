import subprocess
import sys

from modules.rag.explainers import explain_report_question, explain_rule_question
from modules.rag.metadata import KnowledgeDocMetadata, load_metadata_from_directory
from modules.rag.types import AnswerWithSources


def assert_module_imports_without_runtime_dependencies(module_name: str) -> None:
    code = f"""
import importlib
import json
import sys

forbidden = [
    "app",
    "modules.rag_qa",
    "langchain",
    "chromadb",
    "sentence_transformers",
    "ollama",
    "torch",
]

importlib.import_module({module_name!r})

loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]

print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def make_metadata(
    doc_id: str = "report.risk_level_decision",
    doc_type: str = "report_explainer",
    applies_to: list[str] | None = None,
    keywords: list[str] | None = None,
    rule_ids: list[str] | None = None,
    mitre_techniques: list[str] | None = None,
    source_path: str | None = "knowledge/blue_team/report_explainer/risk_level_decision.md",
) -> KnowledgeDocMetadata:
    return KnowledgeDocMetadata(
        doc_id=doc_id,
        doc_type=doc_type,
        applies_to=applies_to or ["Security Triage Report"],
        keywords=keywords or ["decision", "monitor"],
        rule_ids=rule_ids or [],
        mitre_techniques=mitre_techniques or [],
        source_path=source_path,
    )


def make_rule_metadata_doc() -> KnowledgeDocMetadata:
    return make_metadata(
        doc_id="rule.cmd_001",
        doc_type="detection_rule",
        keywords=["command injection", "cmd"],
        rule_ids=["CMD-001"],
        mitre_techniques=["T1059"],
        source_path="detections/blue_team/command_injection.yml",
    )


def test_explain_report_question_returns_answer_with_sources() -> None:
    answer = explain_report_question("Why is the decision MONITOR?", [make_metadata()])

    assert isinstance(answer, AnswerWithSources)


def test_explain_report_question_for_monitor_mentions_simulated_policy_controlled_decision() -> None:
    answer = explain_report_question("為什麼是 MONITOR？", [make_metadata()])

    assert "simulated" in answer.answer
    assert "policy-controlled" in answer.answer
    assert "deterministic" in answer.answer


def test_explain_report_question_includes_source_citation_when_metadata_matches() -> None:
    answer = explain_report_question("Why is the decision MONITOR?", [make_metadata()])

    assert answer.sources
    assert answer.sources[0].identifier == "report.risk_level_decision"


def test_explain_report_question_includes_extracted_ev_id_in_evidence_ids() -> None:
    answer = explain_report_question("Explain EV-003", [make_metadata(keywords=["evidence"])])

    assert answer.evidence_ids == ["EV-003"]


def test_explain_report_question_for_next_step_gives_safe_analyst_review_wording() -> None:
    answer = explain_report_question(
        "What next steps should I review?",
        [make_metadata(keywords=["review"], source_path="review.md")],
    )

    assert "safe analyst review" in answer.answer
    assert "not confirmed compromise" in answer.answer
    assert "No automated response" in answer.answer


def test_explain_report_question_with_no_metadata_candidates_returns_insufficient_fallback() -> None:
    metadata = make_metadata(doc_type="attack_technique", keywords=["xss"], source_path="xss.md")

    answer = explain_report_question("unrelated", [metadata])

    assert answer.confidence == "LOW"
    assert answer.sources[0].source == "insufficient_information"


def test_explain_rule_question_returns_answer_with_sources() -> None:
    answer = explain_rule_question("CMD-001 是什麼？", [make_rule_metadata_doc()])

    assert isinstance(answer, AnswerWithSources)


def test_explain_rule_question_with_cmd_rule_metadata_includes_rule_id() -> None:
    answer = explain_rule_question(
        "CMD-001 是什麼？",
        [make_rule_metadata_doc()],
        rule_metadata={"CMD-001": {"attack_type": "Command Injection"}},
    )

    assert "CMD-001" in answer.answer


def test_explain_rule_question_includes_attack_type_severity_confidence_when_provided() -> None:
    answer = explain_rule_question(
        "CMD-001 是什麼？",
        [make_rule_metadata_doc()],
        rule_metadata={
            "CMD-001": {
                "attack_type": "Command Injection",
                "severity": "HIGH",
                "confidence": "HIGH",
            }
        },
    )

    assert "attack_type: Command Injection" in answer.answer
    assert "severity: HIGH" in answer.answer
    assert "confidence: HIGH" in answer.answer


def test_explain_rule_question_does_not_claim_to_generate_or_activate_rules() -> None:
    answer = explain_rule_question(
        "CMD-001 是什麼？",
        [make_rule_metadata_doc()],
        rule_metadata={"CMD-001": {"attack_type": "Command Injection"}},
    )

    assert "does not generate or activate rules" in answer.answer
    assert "does not create or activate new rules" in answer.answer


def test_explain_rule_question_with_missing_rule_metadata_states_unavailable() -> None:
    answer = explain_rule_question("CMD-001 是什麼？", [make_rule_metadata_doc()], rule_metadata={})

    assert "rule metadata is not available" in answer.answer


def test_explain_rule_question_includes_rule_id_in_answer_with_sources_rule_ids() -> None:
    answer = explain_rule_question("CMD-001 是什麼？", [make_rule_metadata_doc()])

    assert answer.rule_ids == ["CMD-001"]


def test_explain_rule_question_with_no_metadata_candidates_returns_insufficient_fallback() -> None:
    metadata = make_metadata(doc_type="attack_technique", keywords=["xss"], source_path="xss.md")

    answer = explain_rule_question("unrelated", [metadata])

    assert answer.confidence == "LOW"
    assert answer.sources[0].source == "insufficient_information"


def test_report_explainer_does_not_import_rag_runtime_modules() -> None:
    assert_module_imports_without_runtime_dependencies("modules.rag.explainers")


def test_rule_explainer_does_not_import_rag_runtime_modules() -> None:
    assert_module_imports_without_runtime_dependencies("modules.rag.explainers")


def test_legacy_rag_explainers_module_re_exports_canonical_symbols() -> None:
    legacy = __import__("modules.rag_explainers", fromlist=["explain_report_question"])
    canonical = __import__("modules.rag.explainers", fromlist=["explain_report_question"])

    assert legacy.explain_report_question is canonical.explain_report_question


def test_real_report_explainer_metadata_can_support_monitor_answer() -> None:
    metadata_items = load_metadata_from_directory("knowledge/blue_team/report_explainer")

    answer = explain_report_question("為什麼是 MONITOR？", metadata_items)

    assert answer.sources
    assert any("report_explainer" in citation.source for citation in answer.sources)
