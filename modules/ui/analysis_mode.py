"""Pure analysis-mode helpers for the Streamlit analyst console."""

from __future__ import annotations

from modules.smart_router import route_user_input

FAST_DETERMINISTIC_MODE = "Fast deterministic"
FULL_AI_ASSISTED_MODE = "Full AI-assisted"
ANALYSIS_MODE_OPTIONS = (FAST_DETERMINISTIC_MODE, FULL_AI_ASSISTED_MODE)
DEFAULT_ANALYSIS_MODE = FAST_DETERMINISTIC_MODE
STATE_ANALYSIS_MODE = "sentinel_analysis_mode"

FAST_MODE_NOTE = (
    "Fast deterministic mode uses rule-based detection and deterministic policy, "
    "then skips optional AI/RAG explanation layers."
)
FULL_MODE_NOTE = (
    "Full AI-assisted mode preserves the existing orchestrator / SecurityAgent path."
)
SHARED_MODE_BOUNDARY_NOTE = (
    "Risk Level and Decision remain deterministic; no real enforcement is executed."
)


def normalize_analysis_mode(value: str | None) -> str:
    """Return a supported analysis mode, defaulting to fast deterministic."""

    text = str(value or "").strip()
    if text in ANALYSIS_MODE_OPTIONS:
        return text
    return DEFAULT_ANALYSIS_MODE


def is_fast_deterministic_mode(value: str | None) -> bool:
    """Return whether the selected UI mode is fast deterministic mode."""

    return normalize_analysis_mode(value) == FAST_DETERMINISTIC_MODE


def should_use_fast_payload_analysis(user_input: str, analysis_mode: str | None) -> bool:
    """Fast mode applies only to explicit payload/event routes."""

    if not is_fast_deterministic_mode(analysis_mode):
        return False
    return route_user_input(str(user_input or "")).route == "payload_triage"


def analysis_mode_notes(value: str | None) -> tuple[str, ...]:
    """Return concise UI notes for the selected analysis mode."""

    mode = normalize_analysis_mode(value)
    if mode == FULL_AI_ASSISTED_MODE:
        return (FULL_MODE_NOTE, SHARED_MODE_BOUNDARY_NOTE)
    return (FAST_MODE_NOTE, SHARED_MODE_BOUNDARY_NOTE)
