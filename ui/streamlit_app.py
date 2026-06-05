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


def render_report_sections() -> None:
    combined_output = combined_display_output(st.session_state)
    sections = parse_report_sections(combined_output)

    tabs = st.tabs(
        [
            "Analysis Report",
            "Approved Similar Cases",
            "Graph Relations",
            "Safety Boundary",
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
        safety_text = build_safety_boundary_text(combined_output) if combined_output else DEFAULT_SAFETY_BOUNDARY_TEXT
        render_text_block(safety_text, DEFAULT_SAFETY_BOUNDARY_TEXT)

    with tabs[4]:
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

