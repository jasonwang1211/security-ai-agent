"""Regression tests for Markdown Export state preservation across draft actions.

A draft action (request / approve / cancel) must update the Case Draft panel,
latest action, and raw output, but must not erase or replace the preserved
analysis report or similar-case output used by the Export Report.
"""

from modules.ui.case_draft_view import STATUS_PENDING_APPROVAL, build_case_draft_display
from modules.ui.case_memory_view import build_case_memory_display
from modules.ui.console_state import (
    STATE_ANALYSIS_OUTPUT,
    STATE_FOLLOWUP_OUTPUT,
    STATE_FOLLOWUP_SKILL,
    STATE_KNOWLEDGE_OUTPUT,
    STATE_KNOWLEDGE_SKILL,
    STATE_LAST_OUTPUT,
    STATE_SIMILAR_CASE_OUTPUT,
    combined_display_output,
    record_analysis_output,
    record_draft_action_output,
    record_followup_output,
    record_knowledge_output,
    record_similar_case_output,
    summarize_active_context,
)
from modules.ui.performance_view import build_runtime_timing_display
from modules.ui.report_export_view import (
    MISSING_ANALYSIS_REPORT,
    MISSING_SIMILAR_CASES,
    build_markdown_report_export,
)
from modules.ui.report_sections import parse_report_sections
from modules.ui.route_policy_view import build_route_policy_display

GENERATED_AT = "2026-06-08T10:11:12+08:00"

ANALYSIS_TEXT = "\n".join(
    [
        "AI: [Security Triage Report]",
        "",
        "0. Quick Verdict",
        "Risk Level: HIGH",
        "Decision: BLOCK",
    ]
)
SIMILAR_TEXT = "\n".join(
    [
        "[Approved Similar Cases]",
        "Current context kind: active_event",
        "1. CASE-SEED-001 - Command Injection Payload",
        "   Graph-Grounded Relationship Explanation:",
        "      - Current context shares rule ID CMD-001 with CASE-SEED-001.",
    ]
)
DRAFT_REQUEST_TEXT = (
    "AI: Case draft request prepared; explicit approval is required before a markdown file is written."
)
DRAFT_APPROVED_TEXT = (
    "AI: Case draft created for human review:\n`workbench/case_drafts/example.md`"
)


def _session_after_analysis_and_similar() -> dict[str, str]:
    session_state: dict[str, str] = {}
    record_analysis_output(session_state, ANALYSIS_TEXT)
    record_similar_case_output(session_state, SIMILAR_TEXT)
    return session_state


def test_analysis_output_remains_available_after_draft_request() -> None:
    session_state = _session_after_analysis_and_similar()

    record_draft_action_output(
        session_state,
        command="save this case as a draft",
        response_text=DRAFT_REQUEST_TEXT,
        selected_action="DraftCaseCaptureSkill",
    )

    assert session_state[STATE_ANALYSIS_OUTPUT] == ANALYSIS_TEXT
    assert "Risk Level: HIGH" in combined_display_output(session_state)


def test_similar_case_output_remains_available_after_draft_request_and_approve() -> None:
    session_state = _session_after_analysis_and_similar()

    record_draft_action_output(
        session_state,
        command="save this case as a draft",
        response_text=DRAFT_REQUEST_TEXT,
        selected_action="DraftCaseCaptureSkill",
    )
    record_draft_action_output(
        session_state,
        command="approve draft case",
        response_text=DRAFT_APPROVED_TEXT,
        selected_action="DraftCaseCaptureSkill",
    )

    assert session_state[STATE_SIMILAR_CASE_OUTPUT] == SIMILAR_TEXT
    assert "CASE-SEED-001" in combined_display_output(session_state)


def test_export_after_draft_action_still_includes_analysis_and_similar_sections() -> None:
    session_state = _session_after_analysis_and_similar()
    record_draft_action_output(
        session_state,
        command="approve draft case",
        response_text=DRAFT_APPROVED_TEXT,
        selected_action="DraftCaseCaptureSkill",
    )

    sections = parse_report_sections(combined_display_output(session_state))
    export = build_markdown_report_export(
        active_context_summary=summarize_active_context(None),
        report_sections=sections,
        case_memory_display=build_case_memory_display(),
        case_draft_display=build_case_draft_display(
            str(session_state.get(STATE_LAST_OUTPUT) or ""), None
        ),
        runtime_timing_display=build_runtime_timing_display(session_state),
        route_policy_display=build_route_policy_display("DraftCaseCaptureSkill", "approve draft case"),
        raw_output=str(session_state.get(STATE_LAST_OUTPUT) or ""),
        generated_at=GENERATED_AT,
    )

    assert "Risk Level: HIGH" in export.markdown
    assert "CASE-SEED-001" in export.markdown
    assert "Current context shares rule ID CMD-001 with CASE-SEED-001." in export.markdown
    assert MISSING_ANALYSIS_REPORT not in export.markdown
    assert MISSING_SIMILAR_CASES not in export.markdown


def test_case_draft_display_reads_latest_draft_status_after_draft_action() -> None:
    session_state = _session_after_analysis_and_similar()
    record_draft_action_output(
        session_state,
        command="save this case as a draft",
        response_text=DRAFT_REQUEST_TEXT,
        selected_action="DraftCaseCaptureSkill",
    )

    display = build_case_draft_display(str(session_state.get(STATE_LAST_OUTPUT) or ""), None)

    assert display.status == STATUS_PENDING_APPROVAL
    assert session_state[STATE_LAST_OUTPUT] == DRAFT_REQUEST_TEXT


def test_new_analysis_after_draft_still_clears_stale_similar_case_output() -> None:
    session_state = _session_after_analysis_and_similar()
    record_draft_action_output(
        session_state,
        command="approve draft case",
        response_text=DRAFT_APPROVED_TEXT,
        selected_action="DraftCaseCaptureSkill",
    )

    # A new, real analysis must still clear stale similar-case output.
    record_analysis_output(session_state, "[Log Ingestion Summary]\nnew auth analysis")

    assert session_state[STATE_SIMILAR_CASE_OUTPUT] == ""
    assert "CASE-SEED-001" not in combined_display_output(session_state)
    assert "new auth analysis" in combined_display_output(session_state)


# --- v2.6-Y AI follow-up state preservation ---------------------------------

FOLLOWUP_RESPONSE_TEXT = (
    "AI: Repeated login failures followed by success are suspicious but do not "
    "prove account compromise by themselves."
)


def test_followup_question_does_not_clear_analysis_or_similar_output() -> None:
    session_state = _session_after_analysis_and_similar()

    record_followup_output(
        session_state,
        question="這代表命令真的執行了嗎？",
        response_text=FOLLOWUP_RESPONSE_TEXT,
        selected_action="ExplainActiveEventSkill",
    )

    # preserved report sections survive the follow-up.
    assert session_state[STATE_ANALYSIS_OUTPUT] == ANALYSIS_TEXT
    assert session_state[STATE_SIMILAR_CASE_OUTPUT] == SIMILAR_TEXT
    assert "Risk Level: HIGH" in combined_display_output(session_state)
    assert "CASE-SEED-001" in combined_display_output(session_state)
    # the follow-up answer is recorded for the AI Analyst panel.
    assert session_state[STATE_FOLLOWUP_OUTPUT] == FOLLOWUP_RESPONSE_TEXT
    assert session_state[STATE_LAST_OUTPUT] == FOLLOWUP_RESPONSE_TEXT


def test_knowledge_question_does_not_clear_analysis_or_similar_output() -> None:
    session_state = _session_after_analysis_and_similar()

    record_knowledge_output(
        session_state,
        question="什麼是 Command Injection？",
        response_text="AI: Command Injection is ...",
        selected_action="KnowledgeQASkill",
    )

    assert session_state[STATE_ANALYSIS_OUTPUT] == ANALYSIS_TEXT
    assert session_state[STATE_SIMILAR_CASE_OUTPUT] == SIMILAR_TEXT


def test_followup_and_knowledge_use_distinct_state_slots() -> None:
    session_state = _session_after_analysis_and_similar()

    record_followup_output(
        session_state,
        question="為什麼 Decision 是 BLOCK？",
        response_text="AI: deterministic explanation",
        selected_action="ExplainActiveEventSkill",
    )
    record_knowledge_output(
        session_state,
        question="什麼是 Command Injection？",
        response_text="AI: Command Injection is ...",
        selected_action="KnowledgeQASkill",
    )

    # follow-up and knowledge answers/skills are kept in separate slots so each
    # panel renders its own response with the correct route badge.
    assert session_state[STATE_FOLLOWUP_OUTPUT] == "AI: deterministic explanation"
    assert session_state[STATE_FOLLOWUP_SKILL] == "ExplainActiveEventSkill"
    assert session_state[STATE_KNOWLEDGE_OUTPUT] == "AI: Command Injection is ..."
    assert session_state[STATE_KNOWLEDGE_SKILL] == "KnowledgeQASkill"
    # report sections still preserved after both AI calls.
    assert session_state[STATE_ANALYSIS_OUTPUT] == ANALYSIS_TEXT
    assert session_state[STATE_SIMILAR_CASE_OUTPUT] == SIMILAR_TEXT


def test_export_after_followup_still_includes_analysis_and_similar_sections() -> None:
    session_state = _session_after_analysis_and_similar()
    record_followup_output(
        session_state,
        question="為什麼 Decision 是 BLOCK？",
        response_text=FOLLOWUP_RESPONSE_TEXT,
        selected_action="ExplainActiveEventSkill",
    )

    sections = parse_report_sections(combined_display_output(session_state))
    export = build_markdown_report_export(
        active_context_summary=summarize_active_context(None),
        report_sections=sections,
        case_memory_display=build_case_memory_display(),
        case_draft_display=build_case_draft_display(
            str(session_state.get(STATE_LAST_OUTPUT) or ""), None
        ),
        runtime_timing_display=build_runtime_timing_display(session_state),
        route_policy_display=build_route_policy_display("ExplainActiveEventSkill", "為什麼 Decision 是 BLOCK？"),
        raw_output=str(session_state.get(STATE_LAST_OUTPUT) or ""),
        generated_at=GENERATED_AT,
    )

    assert "Risk Level: HIGH" in export.markdown
    assert "CASE-SEED-001" in export.markdown
    assert MISSING_ANALYSIS_REPORT not in export.markdown
    assert MISSING_SIMILAR_CASES not in export.markdown
