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


# --- v2.6-S language-aware route/policy safety notes ------------------------


def test_english_safety_notes_remain_existing_wording() -> None:
    display = build_route_policy_display(ANALYZE_PAYLOAD_SKILL, "test; rm -rf /tmp/test", "en")

    assert any("simulated decisions" in note for note in display.safety_notes)
    assert any(
        "No firewall, WAF, EDR, account, password reset, or monitoring deployment was executed."
        == note
        for note in display.safety_notes
    )


def test_default_language_safety_notes_match_explicit_english() -> None:
    default = build_route_policy_display(DRAFT_CASE_CAPTURE_SKILL, "save this case as a draft")
    english = build_route_policy_display(DRAFT_CASE_CAPTURE_SKILL, "save this case as a draft", "en")

    assert default.safety_notes == english.safety_notes


def test_zh_tw_safety_notes_are_chinese() -> None:
    display = build_route_policy_display(
        RETRIEVE_APPROVED_SIMILAR_CASE_SKILL, "find similar cases", "zh-TW"
    )
    joined = "\n".join(display.safety_notes)

    assert "歷史核准案例僅供參考。" in joined
    assert "相似案例不會覆蓋目前的 Risk Level 或 Decision。" in joined
    assert "未執行任何防火牆、WAF、EDR、帳號、密碼重設或監控部署。" in joined
    assert "advisory references only" not in joined
    # route_reason is a dynamic backend value and remains unchanged.
    assert display.route_reason == 'exact command matched "find similar cases"'


def test_bilingual_safety_notes_are_compact() -> None:
    display = build_route_policy_display(DRAFT_CASE_CAPTURE_SKILL, "save this case as a draft", "bilingual")
    joined = "\n".join(display.safety_notes)

    assert "草稿擷取只會在明確核准後寫入隔離的 workbench 草稿。 / " in joined
    assert "Draft capture writes only an isolated workbench draft after explicit approval." in joined


def test_unsupported_route_policy_language_falls_back_to_english() -> None:
    fr = build_route_policy_display(ANALYZE_PAYLOAD_SKILL, "test; rm -rf /tmp/test", "fr")
    english = build_route_policy_display(ANALYZE_PAYLOAD_SKILL, "test; rm -rf /tmp/test", "en")

    assert fr.safety_notes == english.safety_notes


def test_zh_tw_keeps_tool_policy_reason_untranslated() -> None:
    # The deterministic ToolPolicy reason is a backend value and is not translated.
    display = build_route_policy_display("FutureUnknownSkill", "run future thing", "zh-TW")

    assert any("Unknown tools default to FORBIDDEN" in note for note in display.safety_notes)
