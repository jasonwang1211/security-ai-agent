"""Pure display helpers for the Streamlit case draft tab.

The helper interprets already-produced orchestrator output and in-memory CLI
state. It does not read generated draft files or call the draft writer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

CASE_DRAFT_REQUEST_COMMAND = "save this case as a draft"
CASE_DRAFT_APPROVE_COMMAND = "approve draft case"
CASE_DRAFT_CANCEL_COMMAND = "cancel draft case"

PENDING_CASE_DRAFT_KEY = "pending_case_draft_request"
ACTIVE_CONTEXT_KIND_KEY = "active_context_kind"
ACTIVE_EVENT_CONTEXT_KEY = "active_event_context"
ACTIVE_INCIDENT_CONTEXT_KEY = "active_incident_context"

STATUS_NO_ACTIVE_CONTEXT = "no active context"
STATUS_NO_PENDING_DRAFT = "no pending draft"
STATUS_PENDING_APPROVAL = "pending approval"
STATUS_DRAFT_CREATED = "draft created"
STATUS_CANCELLED = "cancelled"
STATUS_DUPLICATE_DETECTED = "duplicate detected"
STATUS_NO_PENDING_REQUEST = "no pending request"

CASE_DRAFT_SAFETY_NOTES = (
    "Draft files are isolated under workbench/case_drafts/.",
    "Draft files are not live knowledge.",
    "Draft files are not ingested.",
    "Draft files are not approved for promotion.",
    "Human review is required before any draft is trusted or promoted.",
    "safety_reviewed is false by default.",
    "No real firewall, WAF, EDR, account, password reset, monitoring deployment, or enforcement action is executed.",
)

_CREATED_MARKER = "Case draft created for human review:"
_DUPLICATE_MARKER = "Duplicate case draft detected; no file was overwritten:"
_CANCELLED_MARKER = "Pending case draft request cancelled"
_NO_PENDING_MARKER = "No pending case draft request exists"
_NO_ACTIVE_MARKER = "No active payload event or authentication incident is available"
_REQUEST_PREPARED_MARKER = "Case draft request prepared"


@dataclass(frozen=True)
class CaseDraftDisplay:
    """Small immutable display model for the case draft tab."""

    status: str
    message: str
    draft_path: str
    has_active_context: bool
    has_pending_request: bool
    safety_notes: tuple[str, ...] = CASE_DRAFT_SAFETY_NOTES


def build_case_draft_display(
    last_output: str = "",
    cli_state: Mapping[str, Any] | None = None,
) -> CaseDraftDisplay:
    """Build Case Draft tab state from CLI state and latest orchestrator text."""

    text = str(last_output or "")
    has_active_context = _has_active_context(cli_state)
    has_pending_request = bool(_state_value(cli_state, PENDING_CASE_DRAFT_KEY))

    if _CREATED_MARKER in text:
        return CaseDraftDisplay(
            status=STATUS_DRAFT_CREATED,
            message="Case draft created for human review.",
            draft_path=_path_after_marker(text, _CREATED_MARKER),
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    if _DUPLICATE_MARKER in text:
        return CaseDraftDisplay(
            status=STATUS_DUPLICATE_DETECTED,
            message="Duplicate case draft detected; no file was overwritten.",
            draft_path=_path_after_marker(text, _DUPLICATE_MARKER),
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    if _CANCELLED_MARKER in text:
        return CaseDraftDisplay(
            status=STATUS_CANCELLED,
            message="Pending case draft request cancelled. No file was written.",
            draft_path="",
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    if _NO_PENDING_MARKER in text:
        return CaseDraftDisplay(
            status=STATUS_NO_PENDING_REQUEST,
            message="No pending case draft request exists; no file was written.",
            draft_path="",
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    if _NO_ACTIVE_MARKER in text:
        return CaseDraftDisplay(
            status=STATUS_NO_ACTIVE_CONTEXT,
            message="No active payload event or authentication incident is available for draft capture.",
            draft_path="",
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    if _REQUEST_PREPARED_MARKER in text:
        return CaseDraftDisplay(
            status=STATUS_PENDING_APPROVAL,
            message="Case draft request prepared; explicit approval is required before a markdown file is written.",
            draft_path="",
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    if has_pending_request:
        return CaseDraftDisplay(
            status=STATUS_PENDING_APPROVAL,
            message="Draft request is pending explicit approval.",
            draft_path="",
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    if not has_active_context:
        return CaseDraftDisplay(
            status=STATUS_NO_ACTIVE_CONTEXT,
            message="No active payload event or authentication incident is available for draft capture.",
            draft_path="",
            has_active_context=has_active_context,
            has_pending_request=has_pending_request,
        )

    return CaseDraftDisplay(
        status=STATUS_NO_PENDING_DRAFT,
        message="No pending draft request for the current active context.",
        draft_path="",
        has_active_context=has_active_context,
        has_pending_request=has_pending_request,
    )


def _has_active_context(cli_state: Mapping[str, Any] | None) -> bool:
    kind = str(_state_value(cli_state, ACTIVE_CONTEXT_KIND_KEY) or "")
    if kind == "event":
        return _state_value(cli_state, ACTIVE_EVENT_CONTEXT_KEY) is not None
    if kind == "incident":
        return _state_value(cli_state, ACTIVE_INCIDENT_CONTEXT_KEY) is not None
    return False


def _state_value(cli_state: Mapping[str, Any] | None, key: str) -> Any:
    if cli_state is None:
        return None
    return cli_state.get(key)


def _path_after_marker(text: str, marker: str) -> str:
    after_marker = text.split(marker, 1)[1].strip()
    first_line = after_marker.splitlines()[0].strip()
    return first_line.strip("` ")
