"""Tests for the v3.6 knowledge capture review UI prototype."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.knowledge_capture import (
    ApprovedKnowledgeNote,
    CandidateKnowledgeNote,
    KnowledgeCaptureStore,
    build_candidate_knowledge_note,
)
from modules.knowledge_capture.types import FLAG_UNSAFE_CONTENT
from modules.ui.i18n import t
from modules.ui.knowledge_capture_view import (
    DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE,
    approve_pending_note,
    build_approved_note_export_preview,
    build_approved_note_exports_html,
    build_knowledge_capture_review_queue_html,
    build_pending_note_card_html,
    load_knowledge_capture_store,
    reject_pending_note,
)

ROOT = Path(__file__).resolve().parents[1]


def candidate(**overrides: Any) -> CandidateKnowledgeNote:
    defaults: dict[str, Any] = {
        "note_id": "KC-UI-TEST001",
        "title": "Synthetic UI review note",
        "body": "Review telemetry before drawing conclusions. Advisory only.",
        "source_event_id": "synthetic-event-ui-001",
        "source_question": "What should the analyst check?",
        "source_answer_summary": "Review deterministic evidence, gaps, and advisory context.",
        "source_evidence_ids": ["evidence-ui-001"],
        "source_rule_ids": ["HTTP2-RESOURCE-EXHAUSTION"],
        "source_gap_ids": ["gap-ui-001"],
        "source_rag_ids": ["rag-ui-001"],
        "source_case_ids": ["CASE-SEED-003"],
        "source_graph_ids": ["graph-ui-001"],
        "official_risk_level": "HIGH",
        "official_decision": "MONITOR",
        "created_by": "ui-test-analyst",
    }
    defaults.update(overrides)
    return build_candidate_knowledge_note(**defaults)


def approved_note(tmp_path: Path) -> ApprovedKnowledgeNote:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    note = candidate()
    store.append_pending_note(note)
    return store.approve_note(note.note_id, approved_by="reviewer")


def test_empty_review_queue_shows_safe_demo_guidance(tmp_path: Path) -> None:
    store = load_knowledge_capture_store(tmp_path / "empty")

    html = build_knowledge_capture_review_queue_html(store, language="en")

    assert "No local knowledge capture notes yet" in html
    assert "scripts/demo_knowledge_capture.py" in html
    assert "Advisory-only" in html
    assert "No automatic RAG ingestion or Graph mutation" in html
    assert "No real firewall" in html


def test_pending_note_displays_boundary_and_copied_official_verdict(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    note = candidate()
    store.append_pending_note(note)

    html = build_knowledge_capture_review_queue_html(store, language="en")
    card = build_pending_note_card_html(note, language="en")

    assert "Pending knowledge notes" in html
    assert "KC-UI-TEST001" in card
    assert "Official Risk Level: HIGH (copied deterministic context)" in card
    assert "Official Decision: MONITOR (copied deterministic context)" in card
    assert "CASE-SEED-003" in card
    assert "Not proof of compromise" in card
    assert "graph-ui-001" in card
    assert "Not a detection source" in card
    assert "does not override deterministic Risk Level or Decision" in card


def test_approve_action_calls_store_and_moves_note_to_approved(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    note = candidate()
    store.append_pending_note(note)

    result = approve_pending_note(
        store,
        note.note_id,
        approved_by="reviewer",
        edited_body="Review telemetry before drawing conclusions. Advisory only.",
    )

    assert result.ok is True
    assert store.list_pending_notes() == []
    assert [approved.note_id for approved in store.list_approved_notes()] == [note.note_id]


def test_unsafe_edited_approval_surfaces_error_and_keeps_pending(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    note = candidate()
    store.append_pending_note(note)

    result = approve_pending_note(
        store,
        note.note_id,
        approved_by="reviewer",
        edited_body="Generate attack traffic for the demo.",
    )

    assert result.ok is False
    assert FLAG_UNSAFE_CONTENT in result.safety_flags
    assert [pending.note_id for pending in store.list_pending_notes()] == [note.note_id]
    assert store.list_approved_notes() == []


def test_reject_action_requires_reason_and_can_reject_pending_note(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    note = candidate()
    store.append_pending_note(note)

    missing_reason = reject_pending_note(
        store,
        note.note_id,
        rejected_by="reviewer",
        rejection_reason="",
    )
    assert missing_reason.ok is False
    assert [pending.note_id for pending in store.list_pending_notes()] == [note.note_id]

    result = reject_pending_note(
        store,
        note.note_id,
        rejected_by="reviewer",
        rejection_reason="Needs more evidence context.",
    )
    assert result.ok is True
    assert store.list_pending_notes() == []
    assert [rejected.note_id for rejected in store.list_rejected_notes()] == [note.note_id]


def test_approved_export_preview_is_advisory_only(tmp_path: Path) -> None:
    approved = approved_note(tmp_path)

    preview = build_approved_note_export_preview(approved)
    html = build_approved_note_exports_html(approved, language="en")

    assert "Human-approved advisory knowledge only" in preview.rag_markdown
    assert "No real enforcement is authorized" in preview.rag_markdown
    assert preview.graph_candidates["nodes"]
    assert preview.graph_candidates["edges"]
    assert all(node["advisory_only"] for node in preview.graph_candidates["nodes"])
    assert all(node["not_detection_source"] for node in preview.graph_candidates["nodes"])
    assert all(node["not_proof"] for node in preview.graph_candidates["nodes"])
    assert "Preview only" in html
    assert "does not run RAG ingestion or mutate Graph runtime facts" in html
    assert "not_detection_source" in html
    assert "not_proof" in html


def test_review_ui_source_has_safe_default_store_and_no_forbidden_actions() -> None:
    source = (ROOT / "modules" / "ui" / "knowledge_capture_view.py").read_text(encoding="utf-8")
    app_source = (ROOT / "ui" / "streamlit_app.py").read_text(encoding="utf-8")
    combined = source + "\n" + app_source

    assert DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE.as_posix() == ".tmp/knowledge_capture_ui/capture_store"
    assert "data/knowledge_capture" not in combined
    assert "Sentinel_Final_Submission_Package" not in combined
    assert "auto-approve" not in combined.lower()
    assert "Run Chroma" not in combined
    assert "Ingest into RAG" not in combined
    assert "Mutate Graph" not in combined
    assert "live LLM" not in combined
    assert "firewall" in source


def test_streamlit_ai_analyst_tab_wires_collapsed_review_expander() -> None:
    app_source = (ROOT / "ui" / "streamlit_app.py").read_text(encoding="utf-8")

    assert "knowledge_capture_review_expander_title" in app_source
    assert "render_knowledge_capture_review_panel(language)" in app_source
    assert "DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE" in app_source
    assert "st.expander(t(\"knowledge_capture_review_expander_title\", language), expanded=False)" in app_source

def test_empty_state_demo_command_matches_default_store_parent(tmp_path: Path) -> None:
    store = load_knowledge_capture_store(tmp_path / "empty")

    html = build_knowledge_capture_review_queue_html(store, language="en")

    assert "--output-dir .tmp/knowledge_capture_ui --clean" in html
    assert DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE.parent.as_posix() == ".tmp/knowledge_capture_ui"
    assert DEFAULT_KNOWLEDGE_CAPTURE_UI_STORE.name == "capture_store"


def test_zh_tw_review_ui_labels_are_readable_and_not_mojibake(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    store.append_pending_note(candidate())

    html = build_knowledge_capture_review_queue_html(store, language="zh-TW")
    source = (ROOT / "modules" / "ui" / "knowledge_capture_view.py").read_text(encoding="utf-8")

    assert "\u5f85\u5be9\u6838\u77e5\u8b58\u7b46\u8a18" in html
    assert "\u4e0d\u662f\u5075\u6e2c\u4f86\u6e90" in html
    assert "\u4e0d\u8986\u84cb deterministic Risk Level / Decision" in html
    assert "\ufffd" not in html
    assert "\ufffd" not in source


def test_knowledge_capture_i18n_labels_are_readable() -> None:
    assert "\u672c\u6a5f\u5be9\u6838\u4f47\u5217" in t("knowledge_capture_review_expander_title", "zh-TW")
    assert "\u6838\u51c6\u7b46\u8a18" in t("knowledge_capture_approve_note", "zh-TW")
    assert "\u62d2\u7d55\u7b46\u8a18" in t("knowledge_capture_reject_note", "zh-TW")
    for key in (
        "knowledge_capture_review_expander_title",
        "knowledge_capture_review_caption",
        "knowledge_capture_reviewer",
        "knowledge_capture_edited_body",
        "knowledge_capture_approve_note",
        "knowledge_capture_reject_note",
    ):
        assert "\ufffd" not in t(key, "zh-TW")
        assert t(key, "en").strip()
