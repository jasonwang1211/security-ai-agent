from __future__ import annotations

import html
from datetime import datetime
from time import perf_counter
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from modules.agent import SecurityAgent
from modules.controller.fast_analysis import run_fast_payload_analysis
from modules.controller.orchestrator import build_default_v2_5_orchestrator
from modules.controller.skill_catalog import (
    DRAFT_CASE_CAPTURE_SKILL,
    RETRIEVE_APPROVED_SIMILAR_CASE_SKILL,
)
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
from modules.ui.analysis_mode import (
    ANALYSIS_MODE_OPTIONS,
    DEFAULT_ANALYSIS_MODE,
    FAST_DETERMINISTIC_MODE,
    FAST_MODE_NOTE,
    FULL_AI_ASSISTED_MODE,
    FULL_MODE_NOTE,
    SHARED_MODE_BOUNDARY_NOTE,
    STATE_ANALYSIS_MODE,
    analysis_mode_notes,
    normalize_analysis_mode,
    should_use_fast_payload_analysis,
)
from modules.ui.demo_scenarios import (
    SUGGESTED_NEXT_FIND_SIMILAR,
    list_demo_scenarios,
)
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
    record_draft_action_output,
    record_output,
    record_similar_case_output,
    summarize_active_context,
)
from modules.ui.i18n import (
    LANGUAGE_OPTIONS,
    STATE_LANGUAGE,
    language_display_name,
    normalize_language,
    t,
)
from modules.ui.layout_sections import (
    ANALYSIS_REPORT_PANEL,
    APPROVED_SIMILAR_CASES_PANEL,
    CASE_DRAFT_PANEL,
    CASE_MEMORY_PANEL,
    EXPORT_REPORT_PANEL,
    GRAPH_RELATIONS_PANEL,
    PERFORMANCE_PANEL,
    RAW_OUTPUT_PANEL,
    ROUTE_POLICY_PANEL,
    SAFETY_BOUNDARY_PANEL,
    workspace_group_names,
)
from modules.ui.report_sections import (
    DEFAULT_SAFETY_BOUNDARY_TEXT,
    build_safety_boundary_text,
    parse_report_sections,
)
from modules.ui.report_export_view import build_markdown_report_export
from modules.ui.interactive_relationship_graph_view import (
    build_interactive_relationship_graph_display,
)
from modules.ui.performance_view import (
    OUTPUT_KIND_ANALYSIS,
    OUTPUT_KIND_DRAFT,
    OUTPUT_KIND_SIMILAR_CASE,
    build_runtime_timing_display,
    record_runtime_timing,
)
from modules.ui.route_policy_view import build_route_policy_display
from modules.ui.visual_style import (
    DETERMINISTIC_COLOR,
    apply_console_css,
    badge_html,
    decision_color,
    severity_color,
    severity_left_class,
)

PAGE_TITLE = "Security AI Agent Console"
TEXT_AREA_KEY = "sentinel_console_input"
STATE_SCENARIO_NOTE = "sentinel_scenario_note"

_LABEL_KEYS = {
    "Analysis": "analysis_group",
    "Case Intelligence": "case_intelligence_group",
    "Draft / Export": "draft_export_group",
    "System / Debug": "system_debug_group",
    ANALYSIS_REPORT_PANEL: "analysis_report",
    SAFETY_BOUNDARY_PANEL: "safety_boundary",
    RAW_OUTPUT_PANEL: "raw_output",
    APPROVED_SIMILAR_CASES_PANEL: "approved_similar_cases",
    GRAPH_RELATIONS_PANEL: "graph_relations",
    CASE_MEMORY_PANEL: "case_memory",
    CASE_DRAFT_PANEL: "case_draft",
    EXPORT_REPORT_PANEL: "export_report",
    PERFORMANCE_PANEL: "performance",
    ROUTE_POLICY_PANEL: "route_policy",
}

_ANALYSIS_MODE_LABEL_KEYS = {
    FAST_DETERMINISTIC_MODE: "fast_deterministic_mode",
    FULL_AI_ASSISTED_MODE: "full_ai_assisted_mode",
}

_ANALYSIS_MODE_NOTE_KEYS = {
    FAST_MODE_NOTE: "fast_mode_note",
    FULL_MODE_NOTE: "full_mode_note",
    SHARED_MODE_BOUNDARY_NOTE: "shared_mode_boundary_note",
}


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


def current_language() -> str:
    return normalize_language(st.session_state.get(STATE_LANGUAGE))


def ui_text(key: str) -> str:
    return t(key, current_language())


def translated_label(label: str, language: str | None = None) -> str:
    selected_language = normalize_language(language or current_language())
    key = _LABEL_KEYS.get(label)
    return t(key, selected_language) if key else label


def translated_analysis_mode_label(mode: str, language: str | None = None) -> str:
    selected_language = normalize_language(language or current_language())
    return t(_ANALYSIS_MODE_LABEL_KEYS.get(mode, mode), selected_language)


def translated_analysis_mode_notes(mode: str, language: str) -> tuple[str, ...]:
    return tuple(t(_ANALYSIS_MODE_NOTE_KEYS.get(note, note), language) for note in analysis_mode_notes(mode))


def _current_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _output_kind_for_tool(selected_tool: str | None, fallback: str) -> str:
    if selected_tool == RETRIEVE_APPROVED_SIMILAR_CASE_SKILL:
        return OUTPUT_KIND_SIMILAR_CASE
    if selected_tool == DRAFT_CASE_CAPTURE_SKILL:
        return OUTPUT_KIND_DRAFT
    return fallback


def _run_orchestrator_with_timing(
    action_label: str,
    command: str,
    output_kind: str,
    analysis_mode: str = "",
) -> Any:
    _, orchestrator = get_runtime()
    started_at = _current_timestamp()
    start_counter = perf_counter()
    output = orchestrator.handle_input(command)
    elapsed_seconds = perf_counter() - start_counter
    ended_at = _current_timestamp()
    record_runtime_timing(
        st.session_state,
        action_label=action_label,
        selected_skill=output.selected_tool,
        input_text=command,
        status=output.status,
        output_kind=_output_kind_for_tool(output.selected_tool, output_kind),
        started_at=started_at,
        ended_at=ended_at,
        elapsed_seconds=elapsed_seconds,
        analysis_mode=analysis_mode,
    )
    return output


def _run_fast_payload_analysis_with_timing(
    action_label: str,
    user_input: str,
    analysis_mode: str,
) -> Any:
    agent, _ = get_runtime()
    started_at = _current_timestamp()
    start_counter = perf_counter()
    output = run_fast_payload_analysis(agent, user_input, language=current_language())
    elapsed_seconds = perf_counter() - start_counter
    ended_at = _current_timestamp()
    record_runtime_timing(
        st.session_state,
        action_label=action_label,
        selected_skill=output.selected_tool,
        input_text=user_input,
        status=output.status,
        output_kind=OUTPUT_KIND_ANALYSIS,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_seconds=elapsed_seconds,
        analysis_mode=analysis_mode,
    )
    return output


def _record_blank_run_timing(analysis_mode: str = "") -> None:
    started_at = _current_timestamp()
    start_counter = perf_counter()
    elapsed_seconds = perf_counter() - start_counter
    ended_at = _current_timestamp()
    record_runtime_timing(
        st.session_state,
        action_label="Run input",
        selected_skill="clarification_required",
        input_text="",
        status="clarification_required",
        output_kind=OUTPUT_KIND_ANALYSIS,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_seconds=elapsed_seconds,
        analysis_mode=analysis_mode,
    )


def run_direct_input(user_input: str, analysis_mode: str = DEFAULT_ANALYSIS_MODE) -> None:
    """Pass user text into the existing direct-input orchestrator or fast path."""

    mode = normalize_analysis_mode(analysis_mode)
    if should_use_fast_payload_analysis(user_input, mode):
        output = _run_fast_payload_analysis_with_timing("Run input", user_input, mode)
    else:
        output = _run_orchestrator_with_timing(
            "Run input",
            user_input,
            OUTPUT_KIND_ANALYSIS,
            analysis_mode=mode,
        )
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

    output = _run_orchestrator_with_timing(
        "Find Similar Cases",
        SIMILAR_CASE_COMMAND,
        OUTPUT_KIND_SIMILAR_CASE,
    )
    record_output(
        st.session_state,
        user_input=SIMILAR_CASE_COMMAND,
        response_text=output.response_text,
        selected_action=output.selected_tool,
    )
    record_similar_case_output(st.session_state, output.response_text)


def run_case_draft_command(command: str, action_label: str) -> None:
    """Issue an existing exact case-draft command through the orchestrator.

    Draft actions update the Case Draft panel, latest action, and raw output,
    but must preserve the analysis report and similar-case output that the
    Export Report still relies on.
    """

    output = _run_orchestrator_with_timing(action_label, command, OUTPUT_KIND_DRAFT)
    record_draft_action_output(
        st.session_state,
        command=command,
        response_text=output.response_text,
        selected_action=output.selected_tool,
    )


def _detail_value(details: tuple[str, ...], label: str) -> str:
    prefix = f"{label}:"
    for detail in details:
        if detail.startswith(prefix):
            return detail.removeprefix(prefix).strip() or "N/A"
    return "N/A"


def inject_console_css() -> None:
    """Inject the console CSS block once near app startup."""

    st.markdown(f"<style>{apply_console_css()}</style>", unsafe_allow_html=True)


def _status_chip(text: str) -> str:
    return f'<span class="sentinel-chip">\U0001f7e2 {text}</span>'


def render_status_bar() -> None:
    """Render a SOC-style status bar from existing session data only."""

    summary = summarize_active_context(st.session_state.get(STATE_CLI_STATE))
    mode = normalize_analysis_mode(st.session_state.get(STATE_ANALYSIS_MODE))
    mode_badge = badge_html(
        translated_analysis_mode_label(mode),
        DETERMINISTIC_COLOR,
        title=ui_text("console_mode_label"),
    )

    if summary.has_context:
        active_parts = [badge_html(summary.title, DETERMINISTIC_COLOR)]
        if summary.risk_level:
            active_parts.append(
                badge_html(summary.risk_level, severity_color(summary.risk_level), title=ui_text("risk_level"))
            )
        if summary.decision:
            active_parts.append(
                badge_html(summary.decision, decision_color(summary.decision), title=ui_text("decision"))
            )
    else:
        active_parts = [badge_html(ui_text("no_active_short"), severity_color(None))]
    active_html = " ".join(active_parts)

    health_chips = (
        f"{_status_chip(ui_text('status_detector_ok'))}"
        f"{_status_chip(ui_text('status_similar_case_ready'))}"
        f"{_status_chip(ui_text('status_draft_gated'))}"
    )

    status_html = (
        '<div class="sentinel-status-bar">'
        '<div class="sentinel-status-row">'
        f'<span class="sentinel-status-title">\U0001f6e1 {ui_text("header_title")}</span>'
        f"{health_chips}"
        "</div>"
        '<div class="sentinel-status-row">'
        f'<span class="sentinel-muted">{ui_text("console_mode_label")}</span>{mode_badge}'
        f'<span class="sentinel-muted">{ui_text("console_active_label")}</span>{active_html}'
        "</div>"
        "</div>"
    )
    st.markdown(status_html, unsafe_allow_html=True)

    timing = build_runtime_timing_display(st.session_state)
    st.caption(
        f"{ui_text('console_latest_label')}: {timing.action_label}"
        f"  ·  {ui_text('elapsed')} {timing.elapsed_display}"
    )
    st.caption(ui_text("simulated_boundary_caption"))


def _kv_html(label: str, value: str, *, code: bool = False) -> str:
    value_class = "sentinel-kv-value sentinel-code" if code else "sentinel-kv-value"
    return (
        '<span class="sentinel-kv">'
        f'<span class="sentinel-kv-label">{html.escape(label)}</span>'
        f'<span class="{value_class}">{html.escape(value)}</span>'
        "</span>"
    )


def render_active_context() -> None:
    summary = summarize_active_context(st.session_state.get(STATE_CLI_STATE))
    st.subheader(ui_text("active_context"))

    if not summary.has_context:
        st.markdown(
            f'<div class="sentinel-empty-card">{html.escape(ui_text("no_active_context"))}</div>',
            unsafe_allow_html=True,
        )
        return

    attack_or_incident = _detail_value(summary.details, "Attack Type")
    rule_or_evidence_label = ui_text("rules_evidence")
    rule_or_evidence = (
        _detail_value(summary.details, "Rule IDs")
        if summary.kind == "event"
        else _detail_value(summary.details, "Evidence IDs")
    )
    hero_title = (
        attack_or_incident
        if attack_or_incident not in ("", "N/A", "None")
        else summary.title
    )

    badges: list[str] = []
    if summary.risk_level:
        badges.append(
            badge_html(summary.risk_level, severity_color(summary.risk_level), title=ui_text("risk_level"))
        )
    if summary.decision:
        badges.append(
            badge_html(summary.decision, decision_color(summary.decision), title=ui_text("decision"))
        )
    badges_html = " ".join(badges)

    card_class = f"sentinel-hero-card {severity_left_class(summary.risk_level)}".strip()
    sub_line = html.escape(summary.title)
    if summary.decision:
        sub_line = f"{sub_line}  ·  {html.escape(ui_text('simulated_decision'))}"

    hero_html = (
        f'<div class="{card_class}">'
        f'<div class="sentinel-hero-title">{html.escape(hero_title)}</div>'
        f'<div class="sentinel-hero-sub">{sub_line}</div>'
        f'<div class="sentinel-status-row">{badges_html}</div>'
        '<div class="sentinel-status-row">'
        f'{_kv_html(ui_text("context"), summary.title)}'
        f'{_kv_html(ui_text("attack_incident"), attack_or_incident)}'
        f'{_kv_html(rule_or_evidence_label, rule_or_evidence, code=True)}'
        "</div>"
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    with st.expander(ui_text("context_details"), expanded=False):
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
    first.metric(ui_text("approved_seeds"), display.approved_seed_count)
    second.metric(ui_text("approved_for_retrieval"), display.approved_for_retrieval_count)
    third.metric(ui_text("source_directory"), display.source_directory)

    st.write(f"{ui_text('boundary_notes')}:")
    for note in display.boundary_notes:
        st.write(f"- {note}")

    rows = case_memory_table_rows(display.seeds)
    if rows:
        st.table(rows)
    else:
        st.write(ui_text("no_approved_case_seeds"))
        return

    for seed in display.seeds:
        with st.expander(f"{seed.case_id} - {seed.title}"):
            st.write(ui_text("metadata"))
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
            st.write(ui_text("matched_fields"))
            st.json(
                {
                    "attack_types": seed.attack_types,
                    "rule_ids": seed.rule_ids,
                    "finding_types": seed.finding_types,
                    "evidence_types": seed.evidence_types,
                }
            )
            st.write(ui_text("summary"))
            st.write(seed.summary)
            st.write(ui_text("key_facts"))
            for item in seed.key_facts:
                st.write(f"- {item}")
            st.write(ui_text("investigation_notes"))
            for item in seed.investigation_notes:
                st.write(f"- {item}")
            st.write(ui_text("differences_to_check"))
            for item in seed.differences_to_check:
                st.write(f"- {item}")
            st.write(f"{ui_text('analyst_conclusion')}: {seed.analyst_conclusion}")
            st.write(f"{ui_text('outcome')}: {seed.outcome}")
            st.write(ui_text("safety_boundary"))
            for note in display.boundary_notes:
                st.write(f"- {note}")


def render_case_draft_panel() -> None:
    request_col, approve_col, cancel_col = st.columns(3)
    with request_col:
        if st.button(ui_text("request_draft"), use_container_width=True):
            run_case_draft_command(CASE_DRAFT_REQUEST_COMMAND, "Request Draft")
    with approve_col:
        if st.button(ui_text("approve_draft"), use_container_width=True):
            run_case_draft_command(CASE_DRAFT_APPROVE_COMMAND, "Approve Draft")
    with cancel_col:
        if st.button(ui_text("cancel_draft"), use_container_width=True):
            run_case_draft_command(CASE_DRAFT_CANCEL_COMMAND, "Cancel Draft")

    display = build_case_draft_display(
        str(st.session_state.get(STATE_LAST_OUTPUT) or ""),
        st.session_state.get(STATE_CLI_STATE),
    )

    first, second, third = st.columns(3)
    first.metric(ui_text("status"), display.status)
    second.metric(ui_text("pending_approval"), "yes" if display.has_pending_request else "no")
    third.metric(ui_text("active_context"), "yes" if display.has_active_context else "no")

    st.write(display.message)
    if display.draft_path:
        st.write(ui_text("draft_path"))
        st.code(display.draft_path, language="text")
    else:
        st.write(ui_text("no_draft_file_path"))

    st.write(f"{ui_text('safety_boundary')}:")
    for note in display.safety_notes:
        st.write(f"- {note}")


def render_performance_panel() -> None:
    display = build_runtime_timing_display(st.session_state)

    first, second, third = st.columns(3)
    first.metric(ui_text("latest_action"), display.action_label)
    second.metric(ui_text("selected_skill"), display.selected_skill)
    third.metric(ui_text("elapsed"), display.elapsed_display)
    st.metric(ui_text("analysis_mode"), translated_analysis_mode_label(display.analysis_mode))

    status_col, kind_col, timestamp_col = st.columns(3)
    status_col.metric(ui_text("status"), display.status or "N/A")
    kind_col.metric(ui_text("output_kind"), display.output_kind)
    timestamp_col.metric(ui_text("timestamp"), display.timestamp or "N/A")

    st.write(f"{ui_text('started_at')}: {display.started_at or 'N/A'}")
    st.write(f"{ui_text('ended_at')}: {display.ended_at or 'N/A'}")
    if display.input_text:
        st.write(ui_text("latest_input"))
        st.code(display.input_text, language="text")
    else:
        st.write(ui_text("no_input_recorded"))

    st.write(f"{ui_text('notes')}:")
    for note in display.notes:
        st.write(f"- {note}")


def build_current_markdown_export(sections: Any, combined_output: str) -> Any:
    safety_text = (
        build_safety_boundary_text(combined_output)
        if combined_output
        else DEFAULT_SAFETY_BOUNDARY_TEXT
    )
    return build_markdown_report_export(
        active_context_summary=summarize_active_context(st.session_state.get(STATE_CLI_STATE)),
        report_sections=sections,
        case_memory_display=build_case_memory_display(),
        case_draft_display=build_case_draft_display(
            str(st.session_state.get(STATE_LAST_OUTPUT) or ""),
            st.session_state.get(STATE_CLI_STATE),
        ),
        runtime_timing_display=build_runtime_timing_display(st.session_state),
        route_policy_display=build_route_policy_display(
            st.session_state.get(STATE_LAST_SELECTED_ACTION),
            str(st.session_state.get(STATE_LAST_INPUT) or ""),
        ),
        raw_output=str(st.session_state.get(STATE_LAST_OUTPUT) or ""),
        generated_at=_current_timestamp(),
        safety_boundary_text=safety_text,
    )


def render_export_report_panel(sections: Any, combined_output: str) -> None:
    export = build_current_markdown_export(sections, combined_output)

    st.write(f"{ui_text('safety_notes')}:")
    for note in export.safety_notes:
        st.write(f"- {note}")

    st.download_button(
        ui_text("download_markdown_report"),
        data=export.markdown,
        file_name=export.filename,
        mime="text/markdown",
        use_container_width=True,
    )

    st.write(ui_text("markdown_preview"))
    st.code(export.markdown, language="markdown")


def render_relationship_graph_panel(sections: Any) -> None:
    language = current_language()
    display = build_interactive_relationship_graph_display(
        active_context_summary=summarize_active_context(st.session_state.get(STATE_CLI_STATE)),
        approved_similar_cases_text=sections.approved_similar_cases,
        graph_relationship_text=sections.graph_relationship_explanation,
        language=language,
    )

    st.markdown(f"##### {ui_text('visual_relationship_graph')}")
    if display.has_graph:
        try:
            components.html(display.html, height=620, scrolling=True)
        except Exception as exc:  # pragma: no cover - defensive UI fallback
            st.warning("Interactive graph renderer unavailable; DOT source shown instead.")
            st.caption(f"Renderer detail: {exc}")
            render_text_block(display.fallback_dot, ui_text("no_dot_source"))
    else:
        st.info(display.empty_message)

    st.markdown(f"##### {ui_text('graph_legend')}")
    for item in display.legend:
        st.write(f"- {item}")

    st.markdown(f"##### {ui_text('key_relationship_summary')}")
    if display.summary:
        for item in display.summary:
            st.write(f"- {item}")
    else:
        st.write(ui_text("no_relationship_summary"))

    st.write(f"{ui_text('graph_notes')}:")
    for note in display.notes:
        st.write(f"- {note}")

    with st.expander(ui_text("fallback_dot_graphviz"), expanded=False):
        if display.fallback_dot.strip():
            try:
                st.graphviz_chart(display.fallback_dot)
            except Exception as exc:  # pragma: no cover - defensive UI fallback
                st.warning("Visual graph renderer unavailable; DOT source shown instead.")
                st.caption(f"Renderer detail: {exc}")
        else:
            st.write(ui_text("no_dot_source"))

    with st.expander(ui_text("dot_source"), expanded=False):
        render_text_block(display.fallback_dot, ui_text("no_dot_source"))

    with st.expander(ui_text("text_relationship_explanation"), expanded=False):
        render_text_block(
            sections.graph_relationship_explanation,
            ui_text("no_graph_relationship"),
        )


def render_route_policy_panel() -> None:
    display = build_route_policy_display(
        st.session_state.get(STATE_LAST_SELECTED_ACTION),
        str(st.session_state.get(STATE_LAST_INPUT) or ""),
    )

    st.write(f"{ui_text('latest_input')}: {st.session_state.get(STATE_LAST_INPUT) or 'None'}")
    first, second, third = st.columns(3)
    first.metric(ui_text("selected_skill"), display.selected_skill)
    second.metric(ui_text("permission"), display.permission)
    third.metric(ui_text("execution_mode"), display.execution_mode)

    st.write(f"{ui_text('route_reason')}: {display.route_reason}")
    st.write(f"{ui_text('human_approval_required')}: {str(display.human_approval_required).lower()}")
    st.write(f"{ui_text('write_behavior')}: {display.write_behavior}")
    st.write(f"{ui_text('safety_notes')}:")
    for note in display.safety_notes:
        st.write(f"- {note}")


def render_panel_heading(title: str, caption: str = "") -> None:
    st.markdown(f"#### {title}")
    if caption:
        st.caption(caption)


def render_report_sections() -> None:
    combined_output = combined_display_output(st.session_state)
    sections = parse_report_sections(combined_output)
    safety_text = (
        build_safety_boundary_text(combined_output)
        if combined_output
        else DEFAULT_SAFETY_BOUNDARY_TEXT
    )

    language = current_language()
    analysis_tab, case_intelligence_tab, draft_export_tab, system_debug_tab = st.tabs(
        [translated_label(name, language) for name in workspace_group_names()]
    )

    with analysis_tab:
        st.caption(t("analysis_group_caption", language))
        with st.container(border=True):
            render_panel_heading(translated_label(ANALYSIS_REPORT_PANEL, language))
            render_text_block(sections.analysis_report, t("no_analysis_report", language))

        with st.container(border=True):
            render_panel_heading(
                translated_label(SAFETY_BOUNDARY_PANEL, language),
                t("safety_boundary_caption", language),
            )
            render_text_block(safety_text, DEFAULT_SAFETY_BOUNDARY_TEXT)

        with st.expander(translated_label(RAW_OUTPUT_PANEL, language), expanded=False):
            render_text_block(str(st.session_state.get(STATE_LAST_OUTPUT) or ""), t("no_output", language))

    with case_intelligence_tab:
        st.caption(t("case_intelligence_caption", language))
        with st.container(border=True):
            render_panel_heading(translated_label(APPROVED_SIMILAR_CASES_PANEL, language))
            render_text_block(sections.approved_similar_cases, t("no_approved_similar_cases", language))

        with st.container(border=True):
            render_panel_heading(translated_label(GRAPH_RELATIONS_PANEL, language))
            render_relationship_graph_panel(sections)

        with st.container(border=True):
            render_panel_heading(translated_label(CASE_MEMORY_PANEL, language))
            render_case_memory_panel()

    with draft_export_tab:
        st.caption(t("draft_export_caption", language))
        with st.container(border=True):
            render_panel_heading(translated_label(CASE_DRAFT_PANEL, language))
            render_case_draft_panel()

        with st.container(border=True):
            render_panel_heading(translated_label(EXPORT_REPORT_PANEL, language))
            render_export_report_panel(sections, combined_output)

    with system_debug_tab:
        st.caption(t("system_debug_caption", language))
        with st.container(border=True):
            render_panel_heading(translated_label(PERFORMANCE_PANEL, language))
            render_performance_panel()

        with st.container(border=True):
            render_panel_heading(translated_label(ROUTE_POLICY_PANEL, language))
            render_route_policy_panel()


def _scenario_suggested_label(suggested_next_action: str, language: str) -> str:
    if suggested_next_action == SUGGESTED_NEXT_FIND_SIMILAR:
        return t("find_similar_cases", language)
    return t("suggested_next_none", language)


def render_demo_scenario_launcher(language: str) -> None:
    """Render compact demo scenario cards that load input into the textarea.

    Loading a scenario only writes the scenario input into the existing input
    session state and records a status note. It does not run analysis, clear
    active context, or change any backend behavior.
    """

    st.markdown(f"##### {t('demo_scenario_launcher', language)}")
    scenarios = list_demo_scenarios()
    columns = st.columns(len(scenarios))
    for column, scenario in zip(columns, scenarios, strict=True):
        with column, st.container(border=True):
            st.markdown(f"**{t(scenario.title_key, language)}**")
            st.caption(t(scenario.description_key, language))
            st.caption(f"{t('input_preview', language)}:")
            st.code(scenario.input_text, language="text")
            expected = " · ".join(
                part
                for part in (
                    scenario.expected_attack,
                    scenario.expected_risk,
                    scenario.expected_decision,
                )
                if part
            )
            st.caption(f"{t('expected', language)}: {expected}")
            if scenario.expected_case_id:
                st.caption(scenario.expected_case_id)
            st.caption(
                f"{t('suggested_next', language)}: "
                f"{_scenario_suggested_label(scenario.suggested_next_action, language)}"
            )
            if st.button(
                t("load_scenario", language),
                key=f"load_scenario_{scenario.scenario_id}",
                use_container_width=True,
            ):
                st.session_state[TEXT_AREA_KEY] = scenario.input_text
                st.session_state[STATE_SCENARIO_NOTE] = t(scenario.title_key, language)

    note = st.session_state.get(STATE_SCENARIO_NOTE)
    if note:
        st.caption(f"{t('loaded_scenario', language)}: {note}")


def render_controls() -> None:
    with st.container(border=True):
        language = current_language()
        st.subheader(t("control_panel", language))
        language = normalize_language(
            st.selectbox(
                t("language_selector", language),
                LANGUAGE_OPTIONS,
                index=LANGUAGE_OPTIONS.index(language),
                key=STATE_LANGUAGE,
                format_func=language_display_name,
            )
        )
        selected_mode = normalize_analysis_mode(
            st.radio(
                t("analysis_mode", language),
                ANALYSIS_MODE_OPTIONS,
                index=ANALYSIS_MODE_OPTIONS.index(DEFAULT_ANALYSIS_MODE),
                key=STATE_ANALYSIS_MODE,
                horizontal=True,
                format_func=lambda mode: translated_analysis_mode_label(str(mode), language),
            )
        )
        for note in translated_analysis_mode_notes(selected_mode, language):
            st.caption(note)

        render_demo_scenario_launcher(language)

        user_input = st.text_area(
            t("input", language),
            key=TEXT_AREA_KEY,
            height=150,
            placeholder="test; rm -rf /tmp/test",
        )

        run_col, similar_col, clear_col = st.columns([1.4, 1, 1])
        with run_col:
            run_clicked = st.button(t("run_input", language), type="primary", use_container_width=True)
        with similar_col:
            similar_clicked = st.button(t("find_similar_cases", language), use_container_width=True)
        with clear_col:
            clear_clicked = st.button(t("clear_context", language), use_container_width=True)

    if run_clicked:
        text = str(user_input or "").strip()
        if text:
            run_direct_input(text, selected_mode)
        else:
            st.session_state[STATE_LAST_OUTPUT] = "Input is blank."
            st.session_state[STATE_LAST_SELECTED_ACTION] = "clarification_required"
            _record_blank_run_timing(selected_mode)

    if similar_clicked:
        run_similar_case_lookup()

    if clear_clicked:
        clear_active_context(st.session_state)


def render_last_action() -> None:
    selected = st.session_state.get(STATE_LAST_SELECTED_ACTION) or "None"
    last_input = st.session_state.get(STATE_LAST_INPUT) or "None"
    col1, col2 = st.columns(2)
    col1.caption(f"{ui_text('latest_action')}: {selected}")
    col2.caption(f"{ui_text('latest_input')}: {last_input}")


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    inject_console_css()
    get_runtime()

    render_status_bar()
    st.divider()
    render_controls()
    render_last_action()
    render_active_context()
    render_report_sections()


if __name__ == "__main__":
    main()
