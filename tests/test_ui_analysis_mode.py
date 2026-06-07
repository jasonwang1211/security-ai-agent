import sys
from pathlib import Path

from modules.ui.analysis_mode import (
    ANALYSIS_MODE_OPTIONS,
    DEFAULT_ANALYSIS_MODE,
    FAST_DETERMINISTIC_MODE,
    FULL_AI_ASSISTED_MODE,
    analysis_mode_notes,
    is_fast_deterministic_mode,
    normalize_analysis_mode,
    should_use_fast_payload_analysis,
)


def test_fast_mode_selector_defaults_to_fast_deterministic() -> None:
    assert DEFAULT_ANALYSIS_MODE == FAST_DETERMINISTIC_MODE
    assert ANALYSIS_MODE_OPTIONS == (FAST_DETERMINISTIC_MODE, FULL_AI_ASSISTED_MODE)
    assert normalize_analysis_mode(None) == FAST_DETERMINISTIC_MODE
    assert normalize_analysis_mode("unsupported") == FAST_DETERMINISTIC_MODE
    assert is_fast_deterministic_mode(None) is True


def test_fast_mode_applies_only_to_payload_event_routes() -> None:
    assert should_use_fast_payload_analysis("test; rm -rf /tmp/test", FAST_DETERMINISTIC_MODE) is True
    assert should_use_fast_payload_analysis("demo_logs/scenario_a_mixed_auth.log", FAST_DETERMINISTIC_MODE) is False
    assert should_use_fast_payload_analysis("What is SQL injection?", FAST_DETERMINISTIC_MODE) is False


def test_full_ai_assisted_mode_preserves_existing_orchestrator_path() -> None:
    assert is_fast_deterministic_mode(FULL_AI_ASSISTED_MODE) is False
    assert should_use_fast_payload_analysis("test; rm -rf /tmp/test", FULL_AI_ASSISTED_MODE) is False


def test_analysis_mode_notes_describe_mode_boundaries() -> None:
    fast_notes = analysis_mode_notes(FAST_DETERMINISTIC_MODE)
    full_notes = analysis_mode_notes(FULL_AI_ASSISTED_MODE)

    assert any("skips optional AI/RAG" in note for note in fast_notes)
    assert any("existing orchestrator / SecurityAgent path" in note for note in full_notes)
    assert any("Risk Level and Decision remain deterministic" in note for note in fast_notes)
    assert any("Risk Level and Decision remain deterministic" in note for note in full_notes)


def test_analysis_mode_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/analysis_mode.py").read_text(encoding="utf-8")

    assert "streamlit" not in source
    assert "streamlit" not in sys.modules
