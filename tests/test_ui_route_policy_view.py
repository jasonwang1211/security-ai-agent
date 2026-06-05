import sys
from pathlib import Path

from modules.controller.skill_catalog import (
    ANALYZE_PAYLOAD_SKILL,
    DRAFT_CASE_CAPTURE_SKILL,
    RETRIEVE_APPROVED_SIMILAR_CASE_SKILL,
)
from modules.ui.route_policy_view import (
    CLARIFICATION_SELECTED_SKILL,
    build_route_policy_display,
)


def test_payload_skill_displays_read_only_analysis_policy() -> None:
    display = build_route_policy_display(ANALYZE_PAYLOAD_SKILL, "test; rm -rf /tmp/test")

    assert display.selected_skill == ANALYZE_PAYLOAD_SKILL
    assert display.permission == "READ_ONLY"
    assert display.execution_mode == "DIRECT_ALLOWED"
    assert display.human_approval_required is False
    assert display.write_behavior == "none"
    assert "payload-style input" in display.route_reason
    assert any("simulated decisions" in note for note in display.safety_notes)
    assert any("no real enforcement" in note.lower() for note in display.safety_notes)


def test_similar_case_skill_displays_read_only_advisory_policy() -> None:
    display = build_route_policy_display(
        RETRIEVE_APPROVED_SIMILAR_CASE_SKILL,
        "find similar cases",
    )

    assert display.selected_skill == RETRIEVE_APPROVED_SIMILAR_CASE_SKILL
    assert display.permission == "READ_ONLY"
    assert display.execution_mode == "DIRECT_ALLOWED"
    assert display.human_approval_required is False
    assert display.write_behavior == "none"
    assert display.route_reason == 'exact command matched "find similar cases"'
    assert any("advisory references only" in note for note in display.safety_notes)
    assert any("do not override" in note for note in display.safety_notes)


def test_draft_case_capture_displays_write_draft_human_approval_policy() -> None:
    display = build_route_policy_display(DRAFT_CASE_CAPTURE_SKILL, "save this case as a draft")

    assert display.selected_skill == DRAFT_CASE_CAPTURE_SKILL
    assert display.permission == "WRITE_DRAFT"
    assert display.execution_mode == "HUMAN_APPROVAL_REQUIRED"
    assert display.human_approval_required is True
    assert display.write_behavior == "isolated workbench draft only after explicit approval"
    assert "approval-gated draft capture" in display.route_reason
    assert any("No live KB write" in note for note in display.safety_notes)


def test_clarification_route_displays_no_execution_or_write_behavior() -> None:
    display = build_route_policy_display("clarification_required", "please find similar cases later")

    assert display.selected_skill == CLARIFICATION_SELECTED_SKILL
    assert display.route_reason == "no deterministic route matched the latest input"
    assert display.permission == "none"
    assert display.execution_mode == "not executed"
    assert display.human_approval_required is False
    assert display.write_behavior == "none"
    assert any("No deterministic route" in note for note in display.safety_notes)


def test_unknown_selected_skill_defaults_to_forbidden_policy_display() -> None:
    display = build_route_policy_display("FutureUnknownSkill", "run future thing")

    assert display.selected_skill == "FutureUnknownSkill"
    assert display.permission == "FORBIDDEN"
    assert display.execution_mode == "BLOCKED"
    assert display.human_approval_required is False
    assert display.write_behavior == "none"
    assert any("Unknown tools default to FORBIDDEN" in note for note in display.safety_notes)


def test_route_policy_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/route_policy_view.py").read_text(encoding="utf-8")

    assert "streamlit" not in source
    assert "streamlit" not in sys.modules
