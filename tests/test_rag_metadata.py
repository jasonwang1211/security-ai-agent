from pathlib import Path
import subprocess
import sys

import pytest
from pydantic import ValidationError

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
applies_to:
  - Security Triage Report
  - ""
related_tools:
  - report_followup
attack_types:
  - Possible Account Compromise
severity:
  - HIGH
rule_ids:
  - cmd-001
mitre_techniques:
  - t1059
keywords:
  - monitor
  - " "
---

# Risk Level and Decision

Body text.
"""


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
    assert metadata.applies_to == ["Security Triage Report"]
    assert metadata.related_tools == ["report_followup"]
    assert metadata.rule_ids == ["CMD-001"]
    assert metadata.mitre_techniques == ["T1059"]
    assert metadata.keywords == ["monitor"]
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
        keywords=["monitor", ""],
    )

    assert metadata.applies_to == ["Report"]
    assert metadata.keywords == ["monitor"]


def test_knowledge_doc_metadata_normalizes_rule_ids_to_uppercase() -> None:
    metadata = KnowledgeDocMetadata(
        doc_id="report.example",
        doc_type="report_explainer",
        rule_ids=["cmd-001", " ", "xss-001"],
    )

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
    doc_paths = sorted(Path("knowledge/blue_team/report_explainer").glob("*.md"))

    assert len(doc_paths) == 11
    for doc_path in doc_paths:
        frontmatter, _body = split_frontmatter(doc_path.read_text(encoding="utf-8"))
        assert frontmatter, f"{doc_path} should have frontmatter"


def test_all_report_explainer_docs_parse_into_metadata() -> None:
    metadata = load_metadata_from_directory("knowledge/blue_team/report_explainer")

    assert len(metadata) == 11
    assert all(isinstance(item, KnowledgeDocMetadata) for item in metadata)


def test_all_report_explainer_docs_have_unique_doc_id() -> None:
    metadata = load_metadata_from_directory("knowledge/blue_team/report_explainer")
    doc_ids = [item.doc_id for item in metadata]

    assert len(doc_ids) == len(set(doc_ids))


def test_all_report_explainer_docs_have_report_explainer_doc_type() -> None:
    metadata = load_metadata_from_directory("knowledge/blue_team/report_explainer")

    assert {item.doc_type for item in metadata} == {"report_explainer"}


def test_all_report_explainer_docs_have_non_empty_applies_to() -> None:
    metadata = load_metadata_from_directory("knowledge/blue_team/report_explainer")

    assert all(item.applies_to for item in metadata)


def test_all_report_explainer_docs_have_non_empty_related_tools() -> None:
    metadata = load_metadata_from_directory("knowledge/blue_team/report_explainer")

    assert all(item.related_tools for item in metadata)


def test_all_report_explainer_docs_have_non_empty_keywords() -> None:
    metadata = load_metadata_from_directory("knowledge/blue_team/report_explainer")

    assert all(item.keywords for item in metadata)


def test_metadata_parser_does_not_import_or_initialize_rag_runtime_modules() -> None:
    assert_module_imports_without_runtime_dependencies("modules.rag.metadata")


def test_legacy_rag_metadata_module_re_exports_canonical_symbols() -> None:
    legacy = __import__("modules.rag_metadata", fromlist=["KnowledgeDocMetadata"])
    canonical = __import__("modules.rag.metadata", fromlist=["KnowledgeDocMetadata"])

    assert legacy.KnowledgeDocMetadata is canonical.KnowledgeDocMetadata
