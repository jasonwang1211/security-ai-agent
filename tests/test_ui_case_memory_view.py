import shutil
import sys
from pathlib import Path

from modules.ui.case_memory_view import (
    APPROVED_CASE_SEED_DIR,
    APPROVED_REVIEW_STATUS,
    CASE_MEMORY_BOUNDARY_NOTES,
    build_case_memory_display,
    case_memory_table_rows,
)


def test_loads_three_expected_approved_seed_files() -> None:
    display = build_case_memory_display()

    assert display.approved_seed_count == 3
    assert display.approved_for_retrieval_count == 3
    assert display.source_directory == APPROVED_CASE_SEED_DIR.as_posix()


def test_returns_expected_seed_ids_in_deterministic_order() -> None:
    display = build_case_memory_display()

    assert [seed.case_id for seed in display.seeds] == [
        "CASE-SEED-001",
        "CASE-SEED-002",
        "CASE-SEED-003",
    ]


def test_all_loaded_seeds_are_approved_for_retrieval() -> None:
    display = build_case_memory_display()

    assert all(seed.approved_for_retrieval is True for seed in display.seeds)


def test_all_loaded_seeds_have_approved_review_status() -> None:
    display = build_case_memory_display()

    assert all(seed.review_status == APPROVED_REVIEW_STATUS for seed in display.seeds)


def test_display_model_includes_rule_evidence_and_finding_types() -> None:
    display = build_case_memory_display()
    by_id = {seed.case_id: seed for seed in display.seeds}

    assert by_id["CASE-SEED-001"].rule_ids == ("CMD-001",)
    assert by_id["CASE-SEED-001"].evidence_types == ("shell_metacharacter_payload",)
    assert by_id["CASE-SEED-002"].finding_types == ("possible_account_compromise",)
    assert "success_after_failures" in by_id["CASE-SEED-002"].evidence_types
    assert by_id["CASE-SEED-003"].rule_ids == ("SQLI-001",)
    assert by_id["CASE-SEED-003"].evidence_types == ("sql_injection_payload",)


def test_generated_workbench_case_drafts_are_not_loaded(tmp_path: Path) -> None:
    seed_dir = tmp_path / "data" / "approved_case_seeds"
    draft_dir = tmp_path / "workbench" / "case_drafts"
    seed_dir.mkdir(parents=True)
    draft_dir.mkdir(parents=True)
    shutil.copy(
        Path("data/approved_case_seeds/CASE-SEED-001.yml"),
        seed_dir / "CASE-SEED-001.yml",
    )
    (draft_dir / "draft.yml").write_text(
        """
schema_version: v2.5-approved-case1
case_id: DRAFT-001
title: Draft Should Not Load
review_status: approved_for_similarity_demo
approved_for_retrieval: true
""".strip(),
        encoding="utf-8",
    )
    (draft_dir / "draft.md").write_text("# generated draft", encoding="utf-8")

    display = build_case_memory_display(seed_dir)

    assert [seed.case_id for seed in display.seeds] == ["CASE-SEED-001"]
    assert all("workbench/case_drafts" not in seed.source_path for seed in display.seeds)


def test_missing_seed_directory_returns_empty_display(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing" / "approved_case_seeds"

    display = build_case_memory_display(missing_dir)

    assert display.source_directory == missing_dir.as_posix()
    assert display.seeds == ()
    assert display.approved_seed_count == 0
    assert display.approved_for_retrieval_count == 0


def test_case_memory_table_rows_are_compact_and_read_only() -> None:
    display = build_case_memory_display()

    rows = case_memory_table_rows(display.seeds)

    assert rows[0] == {
        "case_id": "CASE-SEED-001",
        "title": "Command Injection Payload With Simulated BLOCK",
        "case_type": "payload_event",
        "risk_level": "HIGH",
        "decision": "BLOCK",
        "approved_for_retrieval": True,
    }
    assert "summary" not in rows[0]


def test_case_memory_boundary_notes_are_visible() -> None:
    display = build_case_memory_display()

    assert display.boundary_notes == CASE_MEMORY_BOUNDARY_NOTES
    assert any("advisory references only" in note for note in display.boundary_notes)
    assert any("not generated drafts" in note for note in display.boundary_notes)


def test_case_memory_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/case_memory_view.py").read_text(encoding="utf-8")

    assert "streamlit" not in source
    assert "streamlit" not in sys.modules
