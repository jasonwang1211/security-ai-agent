from __future__ import annotations

from typing import Any

import streamlit as st

from modules.agent import SecurityAgent
from modules.controller.orchestrator import build_default_v2_5_orchestrator
from modules.controller.skill_catalog import RETRIEVE_APPROVED_SIMILAR_CASE_SKILL
from modules.detector import RuleBasedDetector
from modules.followup_handler import FollowupHandler
from modules.llm_assist import LLMAssist
from modules.rag_qa import RAGQA
from modules.responder import Responder
from modules.triage_policy import TriagePolicy
from modules.ui.case_draft_view import (
    CASE_DRAFT_APPROVE_COMMAND,
    CASE_DRAFT_CANCEL_COMMAND,
    CASE_DRAFT_REQUEST_COMMAND,
    build_case_draft_display,
)
from modules.ui.case_memory_view import build_case_memory_display, case_memory_table_rows
from modules.ui.console_state import (
    SIMILAR_CASE_COMMAND,
    STATE_AGENT,
    STATE_CLI_STATE,
    STATE_LAST_INPUT,
    STATE_LAST_OUTPUT,
    STATE_LAST_SELECTED_ACTION,
    STATE_ORCHESTRATOR,
    bind_runtime,
    clear_active_context,
    combined_display_output,
    record_analysis_output,
    record_output,
    record_similar_case_output,
    summarize_active_context,
)
from modules.ui.report_sections import (
    DEFAULT_SAFETY_BOUNDARY_TEXT,
    build_safety_boundary_text,
    parse_report_sections,
)
from modules.ui.route_policy_view import build_route_policy_display

PAGE_TITLE = "Security AI Agent Console"
TEXT_AREA_KEY = "sentinel_console_input"


def build_agent() -> SecurityAgent:
    """Build the same local runtime components used by the CLI entrypoint."""

    rag_qa = RAGQA()
    followup_handler = FollowupHandler()
    detector = RuleBasedDetector()
    responder = Responder()
    triage_policy = TriagePolicy()
    llm_assist = LLMAssist()
    return SecurityAgent(
        followup_handler=followup_handler,
        detector=detector,
        rag_qa=rag_qa,
        responder=responder,
        triage_policy=triage_policy,
        llm_assist=llm_assist,
    )


def get_runtime() -> tuple[SecurityAgent, Any]:
    """Initialize once per Streamlit session, then reuse the agent/orchestrator."""

    if STATE_AGENT not in st.session_state:
        agent = build_agent()
        orchestrator = build_default_v2_5_orchestrator(agent)
        bind_runtime(st.session_state, agent=agent, orchestrator=orchestrator)

    agent = st.session_state[STATE_AGENT]
    orchestrator = st.session_state[STATE_ORCHESTRATOR]
    bind_runtime(st.session_state, agent=agent, orchestrator=orchestrator)
    return agent, orchestrator


def run_direct_input(user_input: str) -> None:
    """Pass user text into the existing direct-input orchestrator."""

    _, orchestrator = get_runtime()
    output = orchestrator.handle_input(user_input)
    record_output(
        st.session_state,
        user_input=user_input,
        response_text=output.response_text,
        selected_action=output.selected_tool,
    )
    if output.selected_tool == RETRIEVE_APPROVED_SIMILAR_CASE_SKILL:
        record_similar_case_output(st.session_state, output.response_text)
    else:
        record_analysis_output(st.session_state, output.response_text)


def run_similar_case_lookup() -> None:
    """Issue the existing exact similar-case command against session context."""

    _, orchestrator = get_runtime()
    output = orchestrator.handle_input(SIMILAR_CASE_COMMAND)
    record_output(
        st.session_state,
        user_input=SIMILAR_CASE_COMMAND,
        response_text=output.response_text,
        selected_action=output.selected_tool,
    )
    record_similar_case_output(st.session_state, output.response_text)


def run_case_draft_command(command: str) -> None:
    """Issue an existing exact case-draft command through the orchestrator."""

    _, orchestrator = get_runtime()
    output = orchestrator.handle_input(command)
    record_output(
        st.session_state,
        user_input=command,
        response_text=output.response_text,
        selected_action=output.selected_tool,
    )
    record_analysis_output(st.session_state, output.response_text)


def render_active_context() -> None:
    summary = summarize_active_context(st.session_state.get(STATE_CLI_STATE))
    with st.container(border=True):
        st.subheader("Active Context")
        if not summary.has_context:
            st.write("No active context")
            return

        first, second, third = st.columns(3)
        first.metric("Kind", summary.title)
        second.metric("Risk Level", summary.risk_level or "N/A")
        third.metric("Decision", summary.decision or "N/A")
        for detail in summary.details:
            st.write(detail)


def render_text_block(text: str, empty_text: str) -> None:
    if text.strip():
        st.code(text.strip(), language="text")
    else:
        st.write(empty_text)


def render_case_memory_panel() -> None:
    display = build_case_memory_display()

    first, second, third = st.columns(3)
    first.metric("Approved Seeds", display.approved_seed_count)
    second.metric("Approved For Retrieval", display.approved_for_retrieval_count)
    third.metric("Source Directory", display.source_directory)

    st.write("Boundary Notes:")
    for note in display.boundary_notes:
        st.write(f"- {note}")

    rows = case_memory_table_rows(display.seeds)
    if rows:
        st.table(rows)
    else:
        st.write("No approved case seeds loaded.")
        return

    for seed in display.seeds:
        with st.expander(f"{seed.case_id} - {seed.title}"):
            st.write("Metadata")
            st.json(
                {
                    "case_id": seed.case_id,
                    "title": seed.title,
                    "case_type": seed.case_type,
                    "review_status": seed.review_status,
                    "approved_for_retrieval": seed.approved_for_retrieval,
                    "risk_level": seed.risk_level,
                    "decision": seed.decision,
                    "simulated_decision": seed.simulated_decision,
                    "source_provenance": seed.source_provenance,
                    "current_event_authority": seed.current_event_authority,
                    "source_path": seed.source_path,
                }
            )
            st.write("Matched Fields")
            st.json(
                {
                    "attack_types": seed.attack_types,
                    "rule_ids": seed.rule_ids,
                    "finding_types": seed.finding_types,
                    "evidence_types": seed.evidence_types,
                }
            )
            st.write("Summary")
            st.write(seed.summary)
            st.write("Key Facts")
            for item in seed.key_facts:
                st.write(f"- {item}")
            st.write("Investigation Notes")
            for item in seed.investigation_notes:
                st.write(f"- {item}")
            st.write("Differences To Check")
            for item in seed.differences_to_check:
                st.write(f"- {item}")
            st.write(f"Analyst Conclusion: {seed.analyst_conclusion}")
            st.write(f"Outcome: {seed.outcome}")
            st.write("Safety Boundary")
            for note in display.boundary_notes:
                st.write(f"- {note}")


def render_case_draft_panel() -> None:
    request_col, approve_col, cancel_col = st.columns(3)
    with request_col:
        if st.button("Request Draft", use_container_width=True):
            run_case_draft_command(CASE_DRAFT_REQUEST_COMMAND)
    with approve_col:
        if st.button("Approve Draft", use_container_width=True):
            run_case_draft_command(CASE_DRAFT_APPROVE_COMMAND)
    with cancel_col:
        if st.button("Cancel Draft", use_container_width=True):
            run_case_draft_command(CASE_DRAFT_CANCEL_COMMAND)

    display = build_case_draft_display(
        str(st.session_state.get(STATE_LAST_OUTPUT) or ""),
        st.session_state.get(STATE_CLI_STATE),
    )

    first, second, third = st.columns(3)
    first.metric("Status", display.status)
    second.metric("Pending Approval", "yes" if display.has_pending_request else "no")
    third.metric("Active Context", "yes" if display.has_active_context else "no")

    st.write(display.message)
    if display.draft_path:
        st.write("Draft Path")
        st.code(display.draft_path, language="text")
    else:
        st.write("No draft file path.")

    st.write("Safety Boundary:")
    for note in display.safety_notes:
        st.write(f"- {note}")


def render_route_policy_panel() -> None:
    display = build_route_policy_display(
        st.session_state.get(STATE_LAST_SELECTED_ACTION),
        str(st.session_state.get(STATE_LAST_INPUT) or ""),
    )

    st.write(f"Latest Input: {st.session_state.get(STATE_LAST_INPUT) or 'None'}")
    first, second, third = st.columns(3)
    first.metric("Selected Skill", display.selected_skill)
    second.metric("Permission", display.permission)
    third.metric("Execution Mode", display.execution_mode)

    st.write(f"Route Reason: {display.route_reason}")
    st.write(f"Human Approval Required: {str(display.human_approval_required).lower()}")
    st.write(f"Write Behavior: {display.write_behavior}")
    st.write("Safety Notes:")
    for note in display.safety_notes:
        st.write(f"- {note}")


def render_report_sections() -> None:
    combined_output = combined_display_output(st.session_state)
    sections = parse_report_sections(combined_output)

    tabs = st.tabs(
        [
            "Analysis Report",
            "Approved Similar Cases",
            "Graph Relations",
            "Case Memory",
            "Case Draft",
            "Safety Boundary",
            "Route / Policy",
            "Raw Output",
        ]
    )

    with tabs[0]:
        render_text_block(sections.analysis_report, "No analysis report yet.")

    with tabs[1]:
        render_text_block(sections.approved_similar_cases, "No approved similar cases yet.")

    with tabs[2]:
        render_text_block(
            sections.graph_relationship_explanation,
            "No graph-grounded relationship explanation yet.",
        )

    with tabs[3]:
        render_case_memory_panel()

    with tabs[4]:
        render_case_draft_panel()

    with tabs[5]:
        safety_text = (
            build_safety_boundary_text(combined_output)
            if combined_output
            else DEFAULT_SAFETY_BOUNDARY_TEXT
        )
        render_text_block(safety_text, DEFAULT_SAFETY_BOUNDARY_TEXT)

    with tabs[6]:
        render_route_policy_panel()

    with tabs[7]:
        render_text_block(str(st.session_state.get(STATE_LAST_OUTPUT) or ""), "No output yet.")


def render_controls() -> None:
    user_input = st.text_area(
        "Input",
        key=TEXT_AREA_KEY,
        height=150,
        placeholder="test; rm -rf /tmp/test",
    )

    run_col, similar_col, clear_col = st.columns([1, 1, 1])
    with run_col:
        run_clicked = st.button("Run input", type="primary", use_container_width=True)
    with similar_col:
        similar_clicked = st.button("Find Similar Cases", use_container_width=True)
    with clear_col:
        clear_clicked = st.button("Clear Context", use_container_width=True)

    if run_clicked:
        text = str(user_input or "").strip()
        if text:
            run_direct_input(text)
        else:
            st.session_state[STATE_LAST_OUTPUT] = "Input is blank."
            st.session_state[STATE_LAST_SELECTED_ACTION] = "clarification_required"

    if similar_clicked:
        run_similar_case_lookup()

    if clear_clicked:
        clear_active_context(st.session_state)


def render_last_action() -> None:
    selected = st.session_state.get(STATE_LAST_SELECTED_ACTION) or "None"
    last_input = st.session_state.get(STATE_LAST_INPUT) or "None"
    col1, col2 = st.columns(2)
    col1.caption(f"Last action: {selected}")
    col2.caption(f"Last input: {last_input}")


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    get_runtime()

    st.title(PAGE_TITLE)
    render_controls()
    render_last_action()
    render_active_context()
    render_report_sections()


if __name__ == "__main__":
    main()

