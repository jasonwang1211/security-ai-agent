import sys
from pathlib import Path

from modules.ui.case_draft_view import (
    CASE_DRAFT_SAFETY_NOTES,
    STATUS_CANCELLED,
    STATUS_DRAFT_CREATED,
    STATUS_DUPLICATE_DETECTED,
    STATUS_NO_ACTIVE_CONTEXT,
    STATUS_NO_PENDING_DRAFT,
    STATUS_NO_PENDING_REQUEST,
    STATUS_PENDING_APPROVAL,
    build_case_draft_display,
    case_draft_safety_notes,
)


def _active_event_state(*, pending: object | None = None) -> dict[str, object | str | None]:
    return {
        "active_context_kind": "event",
        "active_event_context": object(),
        "active_incident_context": None,
        "pending_case_draft_request": pending,
    }


def test_no_pending_draft_and_no_active_context_display_safe_empty_status() -> None:
    display = build_case_draft_display("", {})

    assert display.status == STATUS_NO_ACTIVE_CONTEXT
    assert display.has_active_context is False
    assert display.has_pending_request is False
    assert display.draft_path == ""
    assert "No active payload event" in display.message


def test_active_context_without_pending_request_displays_no_pending_draft() -> None:
    display = build_case_draft_display("", _active_event_state())

    assert display.status == STATUS_NO_PENDING_DRAFT
    assert display.has_active_context is True
    assert display.has_pending_request is False
    assert display.draft_path == ""


def test_pending_draft_request_displays_pending_approval() -> None:
    display = build_case_draft_display("", _active_event_state(pending={"fingerprint": "abc"}))

    assert display.status == STATUS_PENDING_APPROVAL
    assert display.has_pending_request is True
    assert "pending explicit approval" in display.message


def test_request_prepared_output_displays_pending_approval() -> None:
    display = build_case_draft_display(
        "Case draft request prepared from the current active context. Explicit approval is required.",
        _active_event_state(pending={"fingerprint": "abc"}),
    )

    assert display.status == STATUS_PENDING_APPROVAL
    assert "Case draft request prepared" in display.message
    assert display.draft_path == ""


def test_created_output_extracts_draft_path() -> None:
    display = build_case_draft_display(
        "Case draft created for human review: workbench/case_drafts/active-event-high-block-abc.md",
        _active_event_state(),
    )

    assert display.status == STATUS_DRAFT_CREATED
    assert display.draft_path == "workbench/case_drafts/active-event-high-block-abc.md"
    assert "human review" in display.message


def test_duplicate_output_displays_no_overwrite_and_path() -> None:
    display = build_case_draft_display(
        "Duplicate case draft detected; no file was overwritten: workbench/case_drafts/active-event-high-block-abc.md",
        _active_event_state(),
    )

    assert display.status == STATUS_DUPLICATE_DETECTED
    assert display.draft_path == "workbench/case_drafts/active-event-high-block-abc.md"
    assert "no file was overwritten" in display.message


def test_cancelled_output_displays_cancelled_status() -> None:
    display = build_case_draft_display(
        "Pending case draft request cancelled. No file was written.",
        _active_event_state(),
    )

    assert display.status == STATUS_CANCELLED
    assert display.draft_path == ""
    assert "No file was written" in display.message


def test_no_pending_request_output_displays_no_pending_status() -> None:
    display = build_case_draft_display(
        "No pending case draft request exists; no file was written.",
        _active_event_state(),
    )

    assert display.status == STATUS_NO_PENDING_REQUEST
    assert display.draft_path == ""
    assert "No pending case draft request exists" in display.message


def test_safety_notes_include_required_case_draft_boundaries() -> None:
    display = build_case_draft_display("", _active_event_state())

    assert display.safety_notes == CASE_DRAFT_SAFETY_NOTES
    joined = "\n".join(display.safety_notes)
    assert "isolated under workbench/case_drafts/" in joined
    assert "not live knowledge" in joined
    assert "not ingested" in joined
    assert "not approved for promotion" in joined
    assert "Human review is required" in joined
    assert "safety_reviewed is false by default" in joined
    assert "No real firewall" in joined


def test_case_draft_view_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/case_draft_view.py").read_text(encoding="utf-8")

    assert "streamlit" not in source
    assert "streamlit" not in sys.modules


# --- v2.6-R language-aware case-draft safety boundary ------------------------


def test_case_draft_safety_notes_default_is_english() -> None:
    assert case_draft_safety_notes() == CASE_DRAFT_SAFETY_NOTES
    assert case_draft_safety_notes("en") == CASE_DRAFT_SAFETY_NOTES


def test_case_draft_safety_notes_zh_tw_uses_chinese_bullets() -> None:
    zh = case_draft_safety_notes("zh-TW")

    joined = "\n".join(zh)
    assert "草稿檔案不是即時知識。" in joined
    assert "草稿檔案不會被匯入知識庫。" in joined
    assert "`safety_reviewed` 預設為 false。" in joined
    assert "未執行任何真實防火牆" in joined
    # English wording must not leak in zh-TW bullets.
    assert "Draft files are not live knowledge." not in joined


def test_case_draft_safety_notes_bilingual_is_compact() -> None:
    bilingual = case_draft_safety_notes("bilingual")

    assert any(" / Draft files are not live knowledge." in note for note in bilingual)
    assert any(note.startswith("草稿檔案不是即時知識。 / ") for note in bilingual)


def test_unsupported_case_draft_language_falls_back_to_english() -> None:
    assert case_draft_safety_notes("fr") == CASE_DRAFT_SAFETY_NOTES


def test_language_only_localizes_safety_notes_not_status_or_message() -> None:
    en = build_case_draft_display("", _active_event_state(pending={"fingerprint": "abc"}))
    zh = build_case_draft_display(
        "", _active_event_state(pending={"fingerprint": "abc"}), language="zh-TW"
    )

    # draft status / message / path behavior is unchanged across languages.
    assert zh.status == en.status == STATUS_PENDING_APPROVAL
    assert zh.message == en.message
    assert zh.draft_path == en.draft_path
    assert zh.has_pending_request == en.has_pending_request
    assert zh.has_active_context == en.has_active_context
    # only the fixed safety bullets are localized.
    assert zh.safety_notes == case_draft_safety_notes("zh-TW")
    assert zh.safety_notes != en.safety_notes
