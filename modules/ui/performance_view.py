"""Pure performance display helpers for the analyst console."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

ANALYZE_AUTHENTICATION_LOG_SKILL = "AnalyzeAuthenticationLogSkill"
ANALYZE_PAYLOAD_SKILL = "AnalyzePayloadSkill"
DRAFT_CASE_CAPTURE_SKILL = "DraftCaseCaptureSkill"
RETRIEVE_APPROVED_SIMILAR_CASE_SKILL = "RetrieveApprovedSimilarCaseSkill"

OUTPUT_KIND_ANALYSIS = "analysis"
OUTPUT_KIND_SIMILAR_CASE = "similar-case"
OUTPUT_KIND_DRAFT = "draft"
OUTPUT_KIND_NONE = "none"

STATE_TIMING_ACTION_LABEL = "sentinel_timing_action_label"
STATE_TIMING_SELECTED_SKILL = "sentinel_timing_selected_skill"
STATE_TIMING_INPUT_TEXT = "sentinel_timing_input_text"
STATE_TIMING_STATUS = "sentinel_timing_status"
STATE_TIMING_OUTPUT_KIND = "sentinel_timing_output_kind"
STATE_TIMING_STARTED_AT = "sentinel_timing_started_at"
STATE_TIMING_ENDED_AT = "sentinel_timing_ended_at"
STATE_TIMING_ELAPSED_SECONDS = "sentinel_timing_elapsed_seconds"

NO_ACTION_LABEL = "No action yet"
NO_SELECTED_SKILL = "None"
NO_ACTION_STATUS = "no action yet"


@dataclass(frozen=True)
class RuntimeTimingDisplay:
    """Small immutable display model for latest UI-triggered runtime timing."""

    action_label: str
    selected_skill: str
    elapsed_seconds: float
    elapsed_display: str
    input_text: str
    status: str
    output_kind: str
    started_at: str
    ended_at: str
    timestamp: str
    notes: tuple[str, ...]


def record_runtime_timing(
    session_state: MutableMapping[str, Any],
    *,
    action_label: str,
    selected_skill: str | None,
    input_text: str,
    status: str,
    output_kind: str,
    started_at: str,
    ended_at: str,
    elapsed_seconds: float,
) -> None:
    """Store the latest action timing in a dict-like session mapping."""

    session_state[STATE_TIMING_ACTION_LABEL] = str(action_label or "").strip()
    session_state[STATE_TIMING_SELECTED_SKILL] = str(selected_skill or "clarification_required")
    session_state[STATE_TIMING_INPUT_TEXT] = str(input_text or "")
    session_state[STATE_TIMING_STATUS] = str(status or "")
    session_state[STATE_TIMING_OUTPUT_KIND] = str(output_kind or OUTPUT_KIND_NONE)
    session_state[STATE_TIMING_STARTED_AT] = str(started_at or "")
    session_state[STATE_TIMING_ENDED_AT] = str(ended_at or "")
    session_state[STATE_TIMING_ELAPSED_SECONDS] = _safe_elapsed(elapsed_seconds)


def build_runtime_timing_display(
    session_state: Mapping[str, Any] | None = None,
) -> RuntimeTimingDisplay:
    """Build display data for the latest recorded UI-triggered action."""

    state = session_state if session_state is not None else {}
    action_label = str(state.get(STATE_TIMING_ACTION_LABEL) or "").strip()
    if not action_label:
        return RuntimeTimingDisplay(
            action_label=NO_ACTION_LABEL,
            selected_skill=NO_SELECTED_SKILL,
            elapsed_seconds=0.0,
            elapsed_display=format_elapsed_seconds(0.0),
            input_text="",
            status=NO_ACTION_STATUS,
            output_kind=OUTPUT_KIND_NONE,
            started_at="",
            ended_at="",
            timestamp="",
            notes=_notes_for(OUTPUT_KIND_NONE, ""),
        )

    selected_skill = str(state.get(STATE_TIMING_SELECTED_SKILL) or NO_SELECTED_SKILL)
    output_kind = str(state.get(STATE_TIMING_OUTPUT_KIND) or OUTPUT_KIND_NONE)
    elapsed_seconds = _safe_elapsed(state.get(STATE_TIMING_ELAPSED_SECONDS))
    ended_at = str(state.get(STATE_TIMING_ENDED_AT) or "")
    return RuntimeTimingDisplay(
        action_label=action_label,
        selected_skill=selected_skill,
        elapsed_seconds=elapsed_seconds,
        elapsed_display=format_elapsed_seconds(elapsed_seconds),
        input_text=str(state.get(STATE_TIMING_INPUT_TEXT) or ""),
        status=str(state.get(STATE_TIMING_STATUS) or ""),
        output_kind=output_kind,
        started_at=str(state.get(STATE_TIMING_STARTED_AT) or ""),
        ended_at=ended_at,
        timestamp=ended_at,
        notes=_notes_for(output_kind, selected_skill),
    )


def format_elapsed_seconds(elapsed_seconds: float) -> str:
    """Format elapsed seconds with stable precision for UI and tests."""

    return f"{_safe_elapsed(elapsed_seconds):.3f}s"


def _notes_for(output_kind: str, selected_skill: str) -> tuple[str, ...]:
    notes: list[str] = []
    if output_kind == OUTPUT_KIND_SIMILAR_CASE or selected_skill == RETRIEVE_APPROVED_SIMILAR_CASE_SKILL:
        notes.append("Similar-case retrieval is deterministic and read-only.")
    elif output_kind == OUTPUT_KIND_DRAFT or selected_skill == DRAFT_CASE_CAPTURE_SKILL:
        notes.append("Draft actions may write only after explicit approval.")
    elif output_kind == OUTPUT_KIND_ANALYSIS or selected_skill in {
        ANALYZE_AUTHENTICATION_LOG_SKILL,
        ANALYZE_PAYLOAD_SKILL,
    }:
        notes.append("Analysis timing preserves deterministic risk and decision semantics.")

    notes.extend(
        [
            "Long analysis time is likely from optional AI/RAG explanation layers, not rule matching.",
            "Timing is for the local demo environment only.",
            "Fast UI Mode is deferred in this pass; timing is observability-only to preserve output semantics.",
        ]
    )
    return tuple(dict.fromkeys(notes))


def _safe_elapsed(value: Any) -> float:
    try:
        return max(0.0, float(value or 0.0))
    except (TypeError, ValueError):
        return 0.0
