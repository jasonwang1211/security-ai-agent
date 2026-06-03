from pathlib import Path

from modules.rag.controlled_retrieval import select_controlled_sources
from modules.rag.metadata import KnowledgeDocMetadata, load_metadata_from_directory

REPORT_EXPLAINER_DIR = Path("knowledge/blue_team/report_explainer")


def real_report_metadata() -> list[KnowledgeDocMetadata]:
    return load_metadata_from_directory(REPORT_EXPLAINER_DIR)


def selected_filenames(question: str, metadata_items: list[KnowledgeDocMetadata] | None = None) -> list[str]:
    result = select_controlled_sources(question, metadata_items or real_report_metadata())
    return [Path(match.metadata.source_path or "").name for match in result.matches]


def test_sql_injection_question_resolves_to_approved_explainer() -> None:
    filenames = selected_filenames("什麼是 SQL Injection？")

    assert filenames[0] == "sql_injection_explainer.md"


def test_cmd_rule_question_resolves_to_command_injection_explainer() -> None:
    filenames = selected_filenames(
        "請說明 CMD-001 Command Injection 的判讀重點，以及 BLOCK 是否代表真實封鎖？"
    )

    assert filenames[0] == "command_injection_explainer.md"


def test_success_after_failures_resolves_to_authentication_explainer() -> None:
    filenames = selected_filenames(
        "success_after_failures 登入成功接在多次失敗後，應如何判讀？"
    )

    assert filenames[0] == "success_after_failures.md"


def test_unapproved_metadata_cannot_be_selected() -> None:
    metadata = KnowledgeDocMetadata(
        doc_id="report.unapproved_command_injection",
        doc_type="report_explainer",
        review_status="draft_only",
        attack_types=["Command Injection"],
        rule_ids=["CMD-001"],
        keywords=["CMD-001", "Command Injection"],
        source_path="knowledge/blue_team/report_explainer/unapproved.md",
    )

    result = select_controlled_sources("CMD-001 Command Injection", [metadata])

    assert not result.has_matches


def test_unknown_general_question_returns_no_controlled_match() -> None:
    result = select_controlled_sources("Please summarize today's lunch menu.", real_report_metadata())

    assert not result.has_matches
