from pathlib import Path
import re
import subprocess
import sys
from typing import TypedDict

import pytest
from pydantic import ValidationError
import yaml

from modules.triage_policy import TriagePolicy

from modules.rag.metadata import (
    KnowledgeDocMetadata,
    load_knowledge_metadata,
    load_metadata_from_directory,
    parse_frontmatter_metadata,
    split_frontmatter,
)


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


VALID_DOC = """---
doc_id: report.risk_level_decision
doc_type: report_explainer
title: Risk Level and Decision
review_status: approved_for_runtime_promotion
applies_to:
  - Security Triage Report
  - ""
related_tools:
  - report_followup
attack_types:
  - Possible Account Compromise
finding_types:
  - possible_account_compromise
evidence_types:
  - success_after_failures
severity:
  - HIGH
decision_labels:
  - monitor
rule_ids:
  - cmd-001
mitre_techniques:
  - t1059
keywords:
  - monitor
  - " "
tags:
  - report
  - " "
---

# Risk Level and Decision

Body text.
"""


REPORT_EXPLAINER_DIR = Path("knowledge/blue_team/report_explainer")


class RuleExplainerExpectation(TypedDict):
    doc_path: Path
    rule_path: Path
    expected_risk: str
    expected_decision: str


PROMOTED_REPORT_EXPLAINER_DOCS = [
    REPORT_EXPLAINER_DIR / "possible_account_compromise.md",
    REPORT_EXPLAINER_DIR / "success_after_failures.md",
    REPORT_EXPLAINER_DIR / "monitor_decision_investigation.md",
    REPORT_EXPLAINER_DIR / "authentication_investigation_checklist.md",
    REPORT_EXPLAINER_DIR / "authentication_false_positive_considerations.md",
    REPORT_EXPLAINER_DIR / "xss_explainer.md",
    REPORT_EXPLAINER_DIR / "sql_injection_explainer.md",
    REPORT_EXPLAINER_DIR / "path_traversal_explainer.md",
    REPORT_EXPLAINER_DIR / "command_injection_explainer.md",
]

GENERIC_AUTHENTICATION_DOCS = [
    REPORT_EXPLAINER_DIR / "possible_account_compromise.md",
    REPORT_EXPLAINER_DIR / "success_after_failures.md",
    REPORT_EXPLAINER_DIR / "monitor_decision_investigation.md",
    REPORT_EXPLAINER_DIR / "authentication_investigation_checklist.md",
    REPORT_EXPLAINER_DIR / "authentication_false_positive_considerations.md",
]

RULE_EXPLAINER_EXPECTATIONS: dict[str, RuleExplainerExpectation] = {
    "XSS-001": {
        "doc_path": REPORT_EXPLAINER_DIR / "xss_explainer.md",
        "rule_path": Path("detections/blue_team/xss/xss_basic.yml"),
        "expected_risk": "MEDIUM",
        "expected_decision": "MONITOR",
    },
    "SQLI-001": {
        "doc_path": REPORT_EXPLAINER_DIR / "sql_injection_explainer.md",
        "rule_path": Path("detections/blue_team/sql_injection/sql_injection_basic.yml"),
        "expected_risk": "HIGH",
        "expected_decision": "BLOCK",
    },
    "PATH-001": {
        "doc_path": REPORT_EXPLAINER_DIR / "path_traversal_explainer.md",
        "rule_path": Path("detections/blue_team/path_traversal/path_traversal_basic.yml"),
        "expected_risk": "HIGH",
        "expected_decision": "BLOCK",
    },
    "CMD-001": {
        "doc_path": REPORT_EXPLAINER_DIR / "command_injection_explainer.md",
        "rule_path": Path("detections/blue_team/command_injection/command_injection_basic.yml"),
        "expected_risk": "HIGH",
        "expected_decision": "BLOCK",
    },
}


def test_split_frontmatter_returns_frontmatter_and_body() -> None:
    frontmatter, body = split_frontmatter(VALID_DOC)

    assert "doc_id: report.risk_level_decision" in frontmatter
    assert body.startswith("\n# Risk Level and Decision")


def test_split_frontmatter_returns_empty_frontmatter_when_missing() -> None:
    text = "# No Frontmatter\n\nBody text."

    frontmatter, body = split_frontmatter(text)

    assert frontmatter == ""
    assert body == text


def test_split_frontmatter_returns_original_text_when_not_closed() -> None:
    text = "---\ndoc_id: report.example\n# Missing close\n"

    frontmatter, body = split_frontmatter(text)

    assert frontmatter == ""
    assert body == text


def test_parse_frontmatter_metadata_returns_none_without_frontmatter() -> None:
    assert parse_frontmatter_metadata("# Plain doc") is None


def test_parse_frontmatter_metadata_accepts_valid_metadata() -> None:
    metadata = parse_frontmatter_metadata(VALID_DOC, source_path="knowledge/example.md")

    assert metadata is not None
    assert metadata.doc_id == "report.risk_level_decision"
    assert metadata.doc_type == "report_explainer"
    assert metadata.title == "Risk Level and Decision"
    assert metadata.review_status == "approved_for_runtime_promotion"
    assert metadata.applies_to == ["Security Triage Report"]
    assert metadata.related_tools == ["report_followup"]
    assert metadata.finding_types == ["possible_account_compromise"]
    assert metadata.evidence_types == ["success_after_failures"]
    assert metadata.decision_labels == ["MONITOR"]
    assert metadata.rule_ids == ["CMD-001"]
    assert metadata.mitre_techniques == ["T1059"]
    assert metadata.keywords == ["monitor"]
    assert metadata.tags == ["report"]
    assert metadata.source_path == "knowledge/example.md"


def test_parse_frontmatter_metadata_rejects_invalid_yaml() -> None:
    with pytest.raises(ValueError):
        parse_frontmatter_metadata("---\ndoc_id: [unterminated\n---\nBody")


def test_parse_frontmatter_metadata_rejects_non_mapping_yaml() -> None:
    with pytest.raises(ValueError):
        parse_frontmatter_metadata("---\n- one\n- two\n---\nBody")


def test_knowledge_doc_metadata_rejects_blank_doc_id() -> None:
    with pytest.raises(ValidationError):
        KnowledgeDocMetadata(doc_id=" ", doc_type="report_explainer")


def test_knowledge_doc_metadata_rejects_blank_doc_type() -> None:
    with pytest.raises(ValidationError):
        KnowledgeDocMetadata(doc_id="report.example", doc_type=" ")


def test_knowledge_doc_metadata_removes_blank_list_entries() -> None:
    metadata = KnowledgeDocMetadata(
        doc_id="report.example",
        doc_type="report_explainer",
        applies_to=["Report", " ", ""],
        finding_types=["possible_account_compromise", ""],
        evidence_types=["success_after_failures", " "],
        keywords=["monitor", ""],
        tags=["authentication", ""],
    )

    assert metadata.applies_to == ["Report"]
    assert metadata.finding_types == ["possible_account_compromise"]
    assert metadata.evidence_types == ["success_after_failures"]
    assert metadata.keywords == ["monitor"]
    assert metadata.tags == ["authentication"]


def test_knowledge_doc_metadata_normalizes_rule_ids_to_uppercase() -> None:
    metadata = KnowledgeDocMetadata(
        doc_id="report.example",
        doc_type="report_explainer",
        decision_labels=["monitor", " ", "block"],
        rule_ids=["cmd-001", " ", "xss-001"],
    )

    assert metadata.decision_labels == ["MONITOR", "BLOCK"]
    assert metadata.rule_ids == ["CMD-001", "XSS-001"]


def test_knowledge_doc_metadata_normalizes_mitre_techniques_to_uppercase() -> None:
    metadata = KnowledgeDocMetadata(
        doc_id="report.example",
        doc_type="report_explainer",
        mitre_techniques=["t1059", " ", "T1190"],
    )

    assert metadata.mitre_techniques == ["T1059", "T1190"]


def test_knowledge_doc_metadata_rejects_blank_source_path() -> None:
    with pytest.raises(ValidationError):
        KnowledgeDocMetadata(doc_id="report.example", doc_type="report_explainer", source_path=" ")


def test_load_knowledge_metadata_reads_utf8_and_sets_posix_source_path(tmp_path: Path) -> None:
    doc_path = tmp_path / "risk_level_decision.md"
    doc_path.write_text(VALID_DOC, encoding="utf-8")

    metadata = load_knowledge_metadata(doc_path)

    assert metadata is not None
    assert metadata.source_path == doc_path.as_posix()
    assert metadata.doc_id == "report.risk_level_decision"


def test_load_metadata_from_directory_loads_markdown_in_sorted_order(tmp_path: Path) -> None:
    (tmp_path / "b.md").write_text(
        "---\ndoc_id: report.b\ndoc_type: report_explainer\n---\n# B\n",
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text(
        "---\ndoc_id: report.a\ndoc_type: report_explainer\n---\n# A\n",
        encoding="utf-8",
    )
    (tmp_path / "plain.md").write_text("# Plain\n", encoding="utf-8")

    metadata = load_metadata_from_directory(tmp_path)

    assert [item.doc_id for item in metadata] == ["report.a", "report.b"]


def test_load_metadata_from_directory_ignores_docs_without_frontmatter(tmp_path: Path) -> None:
    (tmp_path / "with_metadata.md").write_text(
        "---\ndoc_id: report.with_metadata\ndoc_type: report_explainer\n---\n# With Metadata\n",
        encoding="utf-8",
    )
    (tmp_path / "without_metadata.md").write_text("# Without Metadata\n", encoding="utf-8")

    metadata = load_metadata_from_directory(tmp_path)

    assert [item.doc_id for item in metadata] == ["report.with_metadata"]


def test_load_metadata_from_directory_returns_empty_list_for_missing_directory(tmp_path: Path) -> None:
    assert load_metadata_from_directory(tmp_path / "missing") == []


def test_all_report_explainer_docs_have_frontmatter() -> None:
    doc_paths = sorted(REPORT_EXPLAINER_DIR.glob("*.md"))

    assert len(doc_paths) == 25
    for doc_path in doc_paths:
        frontmatter, _body = split_frontmatter(doc_path.read_text(encoding="utf-8"))
        assert frontmatter, f"{doc_path} should have frontmatter"


def test_all_report_explainer_docs_parse_into_metadata() -> None:
    metadata = load_metadata_from_directory(REPORT_EXPLAINER_DIR)

    assert len(metadata) == 25
    assert all(isinstance(item, KnowledgeDocMetadata) for item in metadata)


def test_all_report_explainer_docs_have_unique_doc_id() -> None:
    metadata = load_metadata_from_directory(REPORT_EXPLAINER_DIR)
    doc_ids = [item.doc_id for item in metadata]

    assert len(doc_ids) == len(set(doc_ids))


def test_all_report_explainer_docs_have_report_explainer_doc_type() -> None:
    metadata = load_metadata_from_directory(REPORT_EXPLAINER_DIR)

    assert {item.doc_type for item in metadata} == {"report_explainer"}


def test_all_report_explainer_docs_have_non_empty_applies_to() -> None:
    metadata = load_metadata_from_directory(REPORT_EXPLAINER_DIR)

    assert all(item.applies_to for item in metadata)


def test_all_report_explainer_docs_have_non_empty_related_tools() -> None:
    metadata = load_metadata_from_directory(REPORT_EXPLAINER_DIR)

    assert all(item.related_tools for item in metadata)


def test_all_report_explainer_docs_have_non_empty_keywords() -> None:
    metadata = load_metadata_from_directory(REPORT_EXPLAINER_DIR)

    assert all(item.keywords for item in metadata)


def test_promoted_report_explainer_docs_exist_and_are_approved() -> None:
    metadata_by_source = {
        Path(item.source_path or ""): item
        for item in load_metadata_from_directory(REPORT_EXPLAINER_DIR)
    }

    for doc_path in PROMOTED_REPORT_EXPLAINER_DOCS:
        metadata = metadata_by_source[doc_path]
        assert metadata.review_status == "approved_for_runtime_promotion"


def test_promoted_report_explainer_docs_use_live_schema_and_no_graph_links() -> None:
    for doc_path in PROMOTED_REPORT_EXPLAINER_DOCS:
        frontmatter, _body = split_frontmatter(doc_path.read_text(encoding="utf-8"))
        raw_metadata = yaml.safe_load(frontmatter)

        assert isinstance(raw_metadata, dict)
        assert raw_metadata["schema_version"] == "v2.2-live1"
        assert raw_metadata["review_status"] == "approved_for_runtime_promotion"
        assert "graph_links" not in raw_metadata


def test_promoted_docs_retain_reviewed_attack_and_rule_metadata() -> None:
    for doc_path in GENERIC_AUTHENTICATION_DOCS:
        frontmatter, _body = split_frontmatter(doc_path.read_text(encoding="utf-8"))
        raw_metadata = yaml.safe_load(frontmatter)

        assert isinstance(raw_metadata, dict)
        assert raw_metadata["attack_types"] == []
        assert raw_metadata["rule_ids"] == []

    for rule_id, expectation in RULE_EXPLAINER_EXPECTATIONS.items():
        frontmatter, _body = split_frontmatter(expectation["doc_path"].read_text(encoding="utf-8"))
        raw_metadata = yaml.safe_load(frontmatter)
        rule_data = yaml.safe_load(expectation["rule_path"].read_text(encoding="utf-8"))

        assert isinstance(raw_metadata, dict)
        assert raw_metadata["attack_types"] == [rule_data["attack_type"]]
        assert raw_metadata["rule_ids"] == [rule_id]


def test_promoted_report_explainer_docs_have_resolved_references() -> None:
    for doc_path in PROMOTED_REPORT_EXPLAINER_DOCS:
        text = doc_path.read_text(encoding="utf-8")
        frontmatter, _body = split_frontmatter(text)
        raw_metadata = yaml.safe_load(frontmatter)

        assert "reference_pending_review" not in text
        assert isinstance(raw_metadata, dict)
        references = raw_metadata.get("references")
        assert isinstance(references, list) and references
        for reference in references:
            assert reference["id"] != "reference_pending_review"
            assert reference["type"] != "pending_review"
            assert reference.get("source")
            if reference["type"] == "internal_provenance":
                assert Path(reference["source"]).exists()
            if reference["type"] == "external_defensive_reference":
                assert str(reference.get("url", "")).startswith("https://")


def test_generic_promoted_authentication_docs_do_not_bind_fixed_instances() -> None:
    fixed_instance_pattern = re.compile(r"\b(?:EV|F|INC)-\d+\b")

    for doc_path in GENERIC_AUTHENTICATION_DOCS:
        text = doc_path.read_text(encoding="utf-8")
        assert fixed_instance_pattern.search(text) is None


def test_promoted_rule_explainers_align_with_deterministic_policy() -> None:
    policy = TriagePolicy()

    for rule_id, expectation in RULE_EXPLAINER_EXPECTATIONS.items():
        rule_data = yaml.safe_load(expectation["rule_path"].read_text(encoding="utf-8"))
        metadata = load_knowledge_metadata(expectation["doc_path"])

        assert metadata is not None
        assert rule_data["id"] == rule_id
        assert rule_id in metadata.rule_ids
        assert metadata.severity == [expectation["expected_risk"]]
        assert metadata.decision_labels == [expectation["expected_decision"]]

        risk_result = policy.score_risk({"attack_types": [rule_data["attack_type"]]})
        decision_result = policy.decide(risk_result)

        assert risk_result["risk_level"] == expectation["expected_risk"]
        assert decision_result["decision"] == expectation["expected_decision"]


def test_metadata_parser_does_not_import_or_initialize_rag_runtime_modules() -> None:
    assert_module_imports_without_runtime_dependencies("modules.rag.metadata")


def test_legacy_rag_metadata_module_re_exports_canonical_symbols() -> None:
    legacy = __import__("modules.rag_metadata", fromlist=["KnowledgeDocMetadata"])
    canonical = __import__("modules.rag.metadata", fromlist=["KnowledgeDocMetadata"])

    assert legacy.KnowledgeDocMetadata is canonical.KnowledgeDocMetadata
