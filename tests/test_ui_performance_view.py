import sys
from pathlib import Path

from modules.ui.analysis_mode import FAST_DETERMINISTIC_MODE, FULL_AI_ASSISTED_MODE
from modules.ui.performance_view import (
    ANALYZE_PAYLOAD_SKILL,
    DRAFT_CASE_CAPTURE_SKILL,
    OUTPUT_KIND_ANALYSIS,
    OUTPUT_KIND_DRAFT,
    OUTPUT_KIND_SIMILAR_CASE,
    RETRIEVE_APPROVED_SIMILAR_CASE_SKILL,
    STATE_TIMING_ACTION_LABEL,
    STATE_TIMING_ANALYSIS_MODE,
    STATE_TIMING_ELAPSED_SECONDS,
    STATE_TIMING_INPUT_TEXT,
    STATE_TIMING_SELECTED_SKILL,
    build_runtime_timing_display,
    format_elapsed_seconds,
    record_runtime_timing,
)


def test_default_timing_display_handles_no_action_yet() -> None:
    display = build_runtime_timing_display({})

    assert display.action_label == "No action yet"
    assert display.selected_skill == "None"
    assert display.elapsed_seconds == 0.0
    assert display.elapsed_display == "0.000s"
    assert display.input_text == ""
    assert display.status == "no action yet"
    assert display.output_kind == "none"
    assert display.analysis_mode == "N/A"


def test_records_action_skill_input_elapsed_seconds_and_mode() -> None:
    state: dict[str, object] = {}

    record_runtime_timing(
        state,
        action_label="Run input",
        selected_skill=ANALYZE_PAYLOAD_SKILL,
        input_text="test; rm -rf /tmp/test",
        status="ok",
        output_kind=OUTPUT_KIND_ANALYSIS,
        started_at="2026-06-07T10:00:00+08:00",
        ended_at="2026-06-07T10:00:02+08:00",
        elapsed_seconds=1.23456,
        analysis_mode=FAST_DETERMINISTIC_MODE,
    )
    display = build_runtime_timing_display(state)

    assert state[STATE_TIMING_ACTION_LABEL] == "Run input"
    assert state[STATE_TIMING_SELECTED_SKILL] == ANALYZE_PAYLOAD_SKILL
    assert state[STATE_TIMING_INPUT_TEXT] == "test; rm -rf /tmp/test"
    assert state[STATE_TIMING_ELAPSED_SECONDS] == 1.23456
    assert state[STATE_TIMING_ANALYSIS_MODE] == FAST_DETERMINISTIC_MODE
    assert display.action_label == "Run input"
    assert display.selected_skill == ANALYZE_PAYLOAD_SKILL
    assert display.input_text == "test; rm -rf /tmp/test"
    assert display.elapsed_seconds == 1.23456
    assert display.elapsed_display == "1.235s"
    assert display.timestamp == "2026-06-07T10:00:02+08:00"
    assert display.analysis_mode == FAST_DETERMINISTIC_MODE


def test_formats_elapsed_seconds_stably() -> None:
    assert format_elapsed_seconds(0) == "0.000s"
    assert format_elapsed_seconds(0.1234) == "0.123s"
    assert format_elapsed_seconds(2.9999) == "3.000s"
    assert format_elapsed_seconds(-2.0) == "0.000s"


def test_analysis_action_notes_name_ai_rag_layers_without_semantic_change() -> None:
    state: dict[str, object] = {}
    record_runtime_timing(
        state,
        action_label="Run input",
        selected_skill=ANALYZE_PAYLOAD_SKILL,
        input_text="test; rm -rf /tmp/test",
        status="ok",
        output_kind=OUTPUT_KIND_ANALYSIS,
        started_at="start",
        ended_at="end",
        elapsed_seconds=42.0,
        analysis_mode=FAST_DETERMINISTIC_MODE,
    )

    notes = build_runtime_timing_display(state).notes

    assert any("optional AI/RAG explanation layers" in note for note in notes)
    assert any("preserves deterministic risk and decision semantics" in note for note in notes)
    assert any("local demo environment" in note for note in notes)


def test_similar_case_action_notes_are_read_only() -> None:
    state: dict[str, object] = {}
    record_runtime_timing(
        state,
        action_label="Find Similar Cases",
        selected_skill=RETRIEVE_APPROVED_SIMILAR_CASE_SKILL,
        input_text="find similar cases",
        status="ok",
        output_kind=OUTPUT_KIND_SIMILAR_CASE,
        started_at="start",
        ended_at="end",
        elapsed_seconds=0.01,
    )

    notes = build_runtime_timing_display(state).notes

    assert any("Similar-case retrieval is deterministic and read-only" in note for note in notes)
    assert any("local demo environment" in note for note in notes)


def test_draft_action_notes_allow_writes_only_after_approval() -> None:
    state: dict[str, object] = {}
    record_runtime_timing(
        state,
        action_label="Request Draft",
        selected_skill=DRAFT_CASE_CAPTURE_SKILL,
        input_text="save this case as a draft",
        status="clarification_required",
        output_kind=OUTPUT_KIND_DRAFT,
        started_at="start",
        ended_at="end",
        elapsed_seconds=0.02,
    )

    notes = build_runtime_timing_display(state).notes

    assert any("Draft actions may write only after explicit approval" in note for note in notes)
    assert any("Fast mode is for demo responsiveness" in note for note in notes)


def test_performance_display_distinguishes_fast_and_full_analysis_modes() -> None:
    fast_state: dict[str, object] = {}
    full_state: dict[str, object] = {}
    record_runtime_timing(
        fast_state,
        action_label="Run input",
        selected_skill=ANALYZE_PAYLOAD_SKILL,
        input_text="test; rm -rf /tmp/test",
        status="ok",
        output_kind=OUTPUT_KIND_ANALYSIS,
        started_at="start",
        ended_at="end",
        elapsed_seconds=1.0,
        analysis_mode=FAST_DETERMINISTIC_MODE,
    )
    record_runtime_timing(
        full_state,
        action_label="Run input",
        selected_skill=ANALYZE_PAYLOAD_SKILL,
        input_text="test; rm -rf /tmp/test",
        status="ok",
        output_kind=OUTPUT_KIND_ANALYSIS,
        started_at="start",
        ended_at="end",
        elapsed_seconds=1.0,
        analysis_mode=FULL_AI_ASSISTED_MODE,
    )

    fast = build_runtime_timing_display(fast_state)
    full = build_runtime_timing_display(full_state)

    assert fast.analysis_mode == FAST_DETERMINISTIC_MODE
    assert full.analysis_mode == FULL_AI_ASSISTED_MODE
    assert any("Fast deterministic mode" in note for note in fast.notes)
    assert any("Full AI-assisted mode" in note for note in full.notes)


def test_performance_view_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/performance_view.py").read_text(encoding="utf-8")

    assert "streamlit" not in source
    assert "streamlit" not in sys.modules
