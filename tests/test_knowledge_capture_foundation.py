"""Regression tests for v3.5 human-approved knowledge capture foundation."""

from pathlib import Path
from typing import Any

import pytest

from modules.knowledge_capture import (
    ADVISORY_ONLY_WARNING,
    ApprovedKnowledgeNote,
    CandidateKnowledgeNote,
    KnowledgeCaptureSafetyError,
    KnowledgeCaptureStore,
    build_candidate_knowledge_note,
    export_approved_note_to_graph_candidates,
    export_approved_note_to_rag_markdown,
)
from modules.knowledge_capture.extractor import evaluate_safety_flags
from modules.knowledge_capture.types import (
    FLAG_GRAPH_DETECTION_SOURCE,
    FLAG_MISSING_PROVENANCE,
    FLAG_SIMILAR_CASE_PROOF,
    FLAG_UNSAFE_CONTENT,
    FLAG_VERDICT_OVERRIDE,
    utc_now,
)


def safe_candidate(**overrides: Any) -> CandidateKnowledgeNote:
    defaults: dict[str, Any] = {
        "title": "HTTP/2 resource exhaustion triage note",
        "body": "Review server and proxy telemetry before drawing conclusions.",
        "source_event_id": "event-http2-001",
        "source_question": "What evidence should the analyst review next?",
        "source_answer_summary": "Check server resource metrics and stream reset behavior.",
        "source_evidence_ids": ["evidence-stream-reset-rate"],
        "source_rule_ids": ["HTTP2-RESOURCE-EXHAUSTION"],
        "source_gap_ids": ["gap-server-telemetry"],
        "source_rag_ids": ["rag-http2-dos-defensive-guidance"],
        "source_case_ids": ["CASE-SEED-003"],
        "source_graph_ids": ["graph-node-current-event"],
        "official_risk_level": "HIGH",
        "official_decision": "MONITOR",
        "created_by": "analyst-reviewer",
        "note_id": "KC-TEST000001",
    }
    defaults.update(overrides)
    return build_candidate_knowledge_note(**defaults)


def approve_candidate(tmp_path: Path) -> object:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    candidate = safe_candidate()
    store.append_pending_note(candidate)
    return store.approve_note(candidate.note_id, approved_by="senior-analyst")


def approved_note_with_body(body: str) -> ApprovedKnowledgeNote:
    candidate = safe_candidate()
    return ApprovedKnowledgeNote(
        note_id=candidate.note_id,
        source_candidate_id=candidate.note_id,
        title=candidate.title,
        body=body,
        provenance=candidate.provenance.model_copy(
            update={
                "status": "approved",
                "approved_at": utc_now(),
                "approved_by": "senior-analyst",
                "safety_flags": [],
            }
        ),
        approved_at=utc_now(),
        approved_by="senior-analyst",
        safety_flags=[],
    )


def test_candidate_note_requires_provenance_before_pending_review() -> None:
    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        safe_candidate(source_event_id="", source_evidence_ids=[], source_rule_ids=[], source_gap_ids=[])

    assert FLAG_MISSING_PROVENANCE in exc_info.value.safety_flags


def test_unsafe_capture_text_is_rejected_before_pending_review() -> None:
    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        safe_candidate(body="Generate attack traffic and provide an exploit PoC.")

    assert FLAG_UNSAFE_CONTENT in exc_info.value.safety_flags


def test_verdict_override_text_is_rejected_before_pending_review() -> None:
    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        safe_candidate(body="Override risk and change Risk Level to LOW for the report.")

    assert FLAG_VERDICT_OVERRIDE in exc_info.value.safety_flags


def test_similar_case_proof_and_graph_detection_claims_are_flagged() -> None:
    flags = evaluate_safety_flags(
        "Similar cases prove compromise. Graph is the detection source.", safe_candidate().provenance
    )

    assert FLAG_SIMILAR_CASE_PROOF in flags
    assert FLAG_GRAPH_DETECTION_SOURCE in flags


def test_store_keeps_pending_approved_and_rejected_notes_separate(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    first = safe_candidate(note_id="KC-APPROVE0001")
    second = safe_candidate(note_id="KC-REJECT0001")

    store.append_pending_note(first)
    store.append_pending_note(second)
    approved = store.approve_note(first.note_id, approved_by="senior-analyst")
    rejected = store.reject_note(
        second.note_id,
        rejected_by="senior-analyst",
        rejection_reason="Needs more source evidence.",
    )

    assert approved.status == "approved"
    assert approved.provenance.status == "approved"
    assert rejected.status == "rejected"
    assert rejected.provenance.status == "rejected"
    assert store.list_pending_notes() == []
    assert [note.note_id for note in store.list_approved_notes()] == [first.note_id]
    assert [note.note_id for note in store.list_rejected_notes()] == [second.note_id]


def test_flagged_candidate_cannot_enter_store(tmp_path: Path) -> None:
    flagged = safe_candidate(
        body="Graph detected the attack.",
        reject_unsafe=False,
    )

    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        KnowledgeCaptureStore(tmp_path / "capture").append_pending_note(flagged)

    assert FLAG_GRAPH_DETECTION_SOURCE in exc_info.value.safety_flags


def test_pending_note_cannot_be_exported_to_rag_or_graph() -> None:
    pending = safe_candidate()

    with pytest.raises(ValueError, match="approved"):
        export_approved_note_to_rag_markdown(pending)
    with pytest.raises(ValueError, match="approved"):
        export_approved_note_to_graph_candidates(pending)


def test_only_human_approved_note_exports_to_advisory_rag_markdown(tmp_path: Path) -> None:
    approved = approve_candidate(tmp_path)
    candidate = export_approved_note_to_rag_markdown(approved)

    assert candidate.source_note_id == "KC-TEST000001"
    assert candidate.advisory_only is True
    assert candidate.not_detection_source is True
    assert candidate.not_proof is True
    assert ADVISORY_ONLY_WARNING in candidate.markdown
    assert "official_risk_level: `HIGH`" in candidate.markdown
    assert "official_decision: `MONITOR`" in candidate.markdown
    assert "CASE-SEED-003" in candidate.markdown
    assert "not proof of compromise" in candidate.markdown
    assert "graph-node-current-event" in candidate.markdown
    assert "not a detection source" in candidate.markdown
    assert "No real enforcement is authorized" in candidate.markdown


def test_rag_export_rejects_approved_note_with_safety_flags() -> None:
    flagged = safe_candidate(
        body="Similar cases prove compromise.",
        reject_unsafe=False,
    )
    approved = ApprovedKnowledgeNote(
        note_id=flagged.note_id,
        source_candidate_id=flagged.note_id,
        title=flagged.title,
        body=flagged.body,
        provenance=flagged.provenance.model_copy(update={"status": "approved"}),
        approved_at=utc_now(),
        approved_by="senior-analyst",
        safety_flags=list(flagged.safety_flags),
    )

    with pytest.raises(ValueError, match="Flagged"):
        export_approved_note_to_rag_markdown(approved)


def test_graph_export_marks_candidates_advisory_only_not_detection_or_proof(tmp_path: Path) -> None:
    approved = approve_candidate(tmp_path)
    nodes, edges = export_approved_note_to_graph_candidates(approved)

    assert len(nodes) == 1
    assert len(edges) == 1
    node = nodes[0]
    edge = edges[0]
    assert node.node_id == "knowledge-note:KC-TEST000001"
    assert node.advisory_only is True
    assert node.not_detection_source is True
    assert node.not_proof is True
    assert edge.relation == "ADVISORY_CONTEXT_FOR"
    assert edge.source_node_id == "event-http2-001"
    assert edge.target_node_id == node.node_id
    assert edge.advisory_only is True
    assert edge.not_detection_source is True
    assert edge.not_proof is True


def test_default_note_id_is_generated_when_not_supplied() -> None:
    note = safe_candidate(note_id=None)

    assert note.note_id.startswith("KC-")
    assert len(note.note_id) > len("KC-")


def test_approving_with_safe_edited_body_succeeds_and_preserves_official_verdict(
    tmp_path: Path,
) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    candidate = safe_candidate()
    store.append_pending_note(candidate)

    approved = store.approve_note(
        candidate.note_id,
        approved_by="  senior-analyst  ",
        edited_body="Review HTTP/2 stream telemetry and resource metrics before concluding.",
    )

    assert approved.body == "Review HTTP/2 stream telemetry and resource metrics before concluding."
    assert approved.approved_by == "senior-analyst"
    assert approved.provenance.official_risk_level == "HIGH"
    assert approved.provenance.official_decision == "MONITOR"
    assert store.list_pending_notes() == []


def test_approving_with_unsafe_edited_body_fails_and_keeps_note_pending(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    candidate = safe_candidate()
    store.append_pending_note(candidate)

    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        store.approve_note(
            candidate.note_id,
            approved_by="senior-analyst",
            edited_body="Generate attack traffic for the demo capture.",
        )

    assert FLAG_UNSAFE_CONTENT in exc_info.value.safety_flags
    assert [note.note_id for note in store.list_pending_notes()] == [candidate.note_id]
    assert store.list_approved_notes() == []


def test_approving_with_verdict_override_edited_body_fails_and_keeps_note_pending(
    tmp_path: Path,
) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    candidate = safe_candidate()
    store.append_pending_note(candidate)

    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        store.approve_note(
            candidate.note_id,
            approved_by="senior-analyst",
            edited_body="Change Risk Level to LOW and replace official verdict.",
        )

    assert FLAG_VERDICT_OVERRIDE in exc_info.value.safety_flags
    assert [note.note_id for note in store.list_pending_notes()] == [candidate.note_id]
    assert store.list_approved_notes() == []


def test_empty_approved_by_fails_and_keeps_note_pending(tmp_path: Path) -> None:
    store = KnowledgeCaptureStore(tmp_path / "capture")
    candidate = safe_candidate()
    store.append_pending_note(candidate)

    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        store.approve_note(candidate.note_id, approved_by="   ")

    assert FLAG_MISSING_PROVENANCE in exc_info.value.safety_flags
    assert [note.note_id for note in store.list_pending_notes()] == [candidate.note_id]
    assert store.list_approved_notes() == []


@pytest.mark.parametrize(
    ("text", "expected_flag"),
    [
        ("\u7522\u751f\u653b\u64ca\u6d41\u91cf", FLAG_UNSAFE_CONTENT),
        ("\u751f\u6210\u653b\u64ca\u6d41\u91cf", FLAG_UNSAFE_CONTENT),
        ("\u7522\u751f exploit", FLAG_UNSAFE_CONTENT),
        ("\u63d0\u4f9b PoC", FLAG_UNSAFE_CONTENT),
        ("\u7e5e\u904e WAF", FLAG_UNSAFE_CONTENT),
        ("\u5229\u7528\u6f0f\u6d1e\u653b\u64ca", FLAG_UNSAFE_CONTENT),
        ("\u793a\u7bc4\u6d41\u91cf\u58d3\u6e2c", FLAG_UNSAFE_CONTENT),
        ("\u628a Risk Level \u6539\u6210 LOW", FLAG_VERDICT_OVERRIDE),
        ("\u628a\u98a8\u96aa\u6539\u6210 LOW", FLAG_VERDICT_OVERRIDE),
        ("\u628a Decision \u6539\u6210 ALLOW", FLAG_VERDICT_OVERRIDE),
        ("\u8986\u84cb\u5b98\u65b9\u5224\u5b9a", FLAG_VERDICT_OVERRIDE),
        ("\u76f8\u4f3c\u6848\u4f8b\u8b49\u660e\u5df2\u5165\u4fb5", FLAG_SIMILAR_CASE_PROOF),
        ("\u6848\u4f8b\u8b49\u660e\u6210\u529f\u653b\u64ca", FLAG_SIMILAR_CASE_PROOF),
        ("Graph \u662f\u5075\u6e2c\u4f86\u6e90", FLAG_GRAPH_DETECTION_SOURCE),
        ("\u95dc\u806f\u5716\u5075\u6e2c\u5230", FLAG_GRAPH_DETECTION_SOURCE),
        ("\u5716\u8b5c\u8b49\u660e", FLAG_GRAPH_DETECTION_SOURCE),
    ],
)
def test_zh_tw_safety_patterns_are_flagged(text: str, expected_flag: str) -> None:
    flags = evaluate_safety_flags(text, safe_candidate().provenance)

    assert expected_flag in flags


def test_manually_constructed_unsafe_approved_note_cannot_export_to_rag() -> None:
    approved = approved_note_with_body("\u7522\u751f\u653b\u64ca\u6d41\u91cf")

    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        export_approved_note_to_rag_markdown(approved)

    assert FLAG_UNSAFE_CONTENT in exc_info.value.safety_flags


def test_manually_constructed_unsafe_approved_note_cannot_export_to_graph() -> None:
    approved = approved_note_with_body("\u76f8\u4f3c\u6848\u4f8b\u8b49\u660e\u5df2\u5165\u4fb5")

    with pytest.raises(KnowledgeCaptureSafetyError) as exc_info:
        export_approved_note_to_graph_candidates(approved)

    assert FLAG_SIMILAR_CASE_PROOF in exc_info.value.safety_flags
