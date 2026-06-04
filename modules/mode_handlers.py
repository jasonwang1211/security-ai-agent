import json
import threading
import time
from collections import Counter

from modules.evidence_correlator import correlate_auth_sequence
from modules.incident_followup import (
    ActiveAuthIncidentContext,
    build_active_auth_incident_context,
    format_active_auth_incident_summary,
)
from modules.log_ingestion_runner import SECTION_TITLES, process_lines, read_log_lines
from modules.log_pipeline import (
    events_to_agent_inputs,
    format_input_translation,
    try_translate_raw_log_input,
)

SUMMARY_TITLE = "[Log Ingestion Summary]"
DETECTED_EVENT_TYPES_TITLE = "Detected Event Types:"
AGGREGATED_FINDINGS_TITLE = "Aggregated Findings:"
PRESERVED_PAYLOADS_TITLE = "Preserved Payloads:"
CURRENT_STAGE_LINES = [
    "Current Stage:",
    "Log ingestion only. Events are not sent into SecurityAgent yet.",
]
AGENT_STAGE_LINES = [
    "Current Stage:",
    "Log ingestion and deterministic authentication-incident correlation completed.",
    "Structured incident follow-up is available when an incident is detected.",
    "Optional SecurityAgent analysis of aggregated events has not been run unless requested below.",
]
BRUTE_FORCE_EVENT_TYPE = "brute_force_candidate"
WEB_REQUEST_EVENT_TYPE = "web_request"
LOG_AGENT_ANALYSIS_EMPTY_MESSAGE = "No analyzable log events were produced."
PROGRESS_INTERVAL_SECONDS = 5


def get_agent_state(agent):
    # CLI mode handlers are thin wrappers, so shared conversation state stays on the agent.
    if not hasattr(agent, "cli_state"):
        agent.cli_state = {
            "last_question": "",
            "last_answer": "",
            "last_points": [],
            "last_focus": "",
            "active_event_context": None,
            "active_incident_context": None,
            "active_context_kind": "",
            "pending_case_draft_request": None,
        }

    return agent.cli_state


def run_payload_analysis(agent, user_input: str) -> str:
    # Thin wrapper around the existing Mode 1 agent analysis flow.
    translation = try_translate_raw_log_input(user_input)
    if translation:
        if translation.normalized_event_type == "auth_failure":
            answer = agent.responder.build_auth_failure_triage_report(
                translation.normalized_event,
                translation.agent_input,
            )
        else:
            answer = agent.handle_query(translation.agent_input, get_agent_state(agent))
        return f"\n{format_input_translation(translation)}\n\nAI: {answer}\n"

    answer = agent.handle_query(user_input, get_agent_state(agent))
    return f"\nAI: {answer}\n"


def run_knowledge_qa(agent, question: str) -> str:
    # Mode 3 is dedicated knowledge Q&A, so it bypasses follow-up and detection flows.
    answer = agent.handle_knowledge_query(question, get_agent_state(agent))
    return f"\nAI: {answer}\n"


def run_followup(agent, question: str) -> str:
    # Thin wrapper around the existing Mode 4 follow-up flow with shared state.
    answer = agent.handle_query(question, get_agent_state(agent))
    return f"\nAI: {answer}\n"


def run_with_progress(target, label):
    result = {}
    error = {}

    def worker():
        try:
            result["value"] = target()
        except Exception as exc:
            error["exception"] = exc
            error["traceback"] = exc.__traceback__

    thread = threading.Thread(target=worker)
    thread.start()

    started_at = time.monotonic()
    print(f"{label} started...", flush=True)

    while thread.is_alive():
        thread.join(timeout=PROGRESS_INTERVAL_SECONDS)
        if thread.is_alive():
            elapsed = int(time.monotonic() - started_at)
            print(f"{label} still running... elapsed {elapsed}s", flush=True)

    print(f"{label} complete.", flush=True)

    if "exception" in error:
        raise error["exception"].with_traceback(error["traceback"])

    return result.get("value")


def _format_section(title, data):
    return f"{title}\n{json.dumps(data, ensure_ascii=False, indent=2)}"


def count_event_types(normalized_events):
    return Counter(
        event.get("event_type", "unknown")
        for event in normalized_events
        if isinstance(event, dict)
    )


def _format_event_type_counts(normalized_events):
    counts = count_event_types(normalized_events)
    if not counts:
        return [DETECTED_EVENT_TYPES_TITLE, "- None"]

    lines = [DETECTED_EVENT_TYPES_TITLE]
    lines.extend(f"- {event_type}: {count}" for event_type, count in counts.items())
    return lines


def _is_brute_force_finding(event):
    return isinstance(event, dict) and event.get("event_type") == BRUTE_FORCE_EVENT_TYPE


def _format_aggregated_findings(aggregated_events):
    findings = [event for event in aggregated_events if _is_brute_force_finding(event)]
    if not findings:
        return []

    lines = [AGGREGATED_FINDINGS_TITLE]
    for finding in findings:
        lines.extend(
            [
                f"- Event Type: {finding.get('event_type')}",
                f"  Source IP: {finding.get('source_ip')}",
                f"  Target: {finding.get('target')}",
                f"  Failed Count: {finding.get('failed_count')}",
                f"  Evidence: {', '.join(finding.get('evidence') or [])}",
            ]
        )
    return lines


def _is_web_request_with_payload(event):
    return (
        isinstance(event, dict)
        and event.get("event_type") == WEB_REQUEST_EVENT_TYPE
        and event.get("payload")
    )


def _format_preserved_payloads(normalized_events):
    payloads = [
        event.get("payload")
        for event in normalized_events
        if _is_web_request_with_payload(event)
    ]
    if not payloads:
        return []

    lines = [PRESERVED_PAYLOADS_TITLE]
    lines.extend(f"{index}. {payload}" for index, payload in enumerate(payloads, start=1))
    return lines


def _extend_optional_section(lines, section):
    if section:
        lines.extend(["", *section])


def _format_summary(
    log_path,
    lines,
    parsed_logs,
    normalized_events,
    aggregated_events,
    stage_lines=None,
):
    summary = [
        SUMMARY_TITLE,
        "",
        f"File: {log_path}",
        f"Total Lines: {len(lines)}",
        f"Parsed Logs: {len(parsed_logs)}",
        f"Normalized Events: {len(normalized_events)}",
        f"Aggregated Events: {len(aggregated_events)}",
        "",
    ]
    summary.extend(_format_event_type_counts(normalized_events))

    _extend_optional_section(summary, _format_aggregated_findings(aggregated_events))
    _extend_optional_section(summary, _format_preserved_payloads(normalized_events))
    summary.extend(["", *(stage_lines or CURRENT_STAGE_LINES)])
    return "\n".join(summary)


def _format_detailed_json(parsed_logs, normalized_events, aggregated_events):
    sections = [
        _format_section(title, data)
        for title, data in zip(
            SECTION_TITLES,
            (parsed_logs, normalized_events, aggregated_events),
        )
    ]
    return "\n".join(sections)


def _read_and_process_log(log_path):
    try:
        lines = read_log_lines(log_path)
    except OSError as exc:
        return f"\n讀取 log 檔案失敗: {exc}\n", None

    parsed_logs, normalized_events, aggregated_events = process_lines(lines)
    return None, (lines, parsed_logs, normalized_events, aggregated_events)


def _clear_structured_followup_context(agent) -> None:
    if agent is None:
        return

    state = get_agent_state(agent)
    state["active_incident_context"] = None
    state["active_event_context"] = None
    state["active_context_kind"] = ""


def _store_active_auth_incident_context(
    agent,
    normalized_events,
    rendered_summary: str,
) -> ActiveAuthIncidentContext | None:
    if agent is None:
        return None

    incident = correlate_auth_sequence(
        normalized_events,
        failure_threshold=5,
        window_minutes=5,
    )
    if incident is None:
        _clear_structured_followup_context(agent)
        return None

    state = get_agent_state(agent)
    context = build_active_auth_incident_context(
        incident,
        rendered_summary=rendered_summary,
    )
    state["active_incident_context"] = context
    state["active_context_kind"] = "incident"
    return context


def run_log_ingestion(
    log_path: str,
    include_json: bool = False,
    include_summary: bool = True,
    agent=None,
) -> str:
    # Thin wrapper around the existing log ingestion demo pipeline.
    error, result = _read_and_process_log(log_path)
    if error:
        return error

    lines, parsed_logs, normalized_events, aggregated_events = result
    output_parts = []
    if include_summary:
        output_parts.append(
            _format_summary(
                log_path,
                lines,
                parsed_logs,
                normalized_events,
                aggregated_events,
                AGENT_STAGE_LINES if agent is not None else CURRENT_STAGE_LINES,
            )
        )

    if include_json:
        output_parts.append(_format_detailed_json(parsed_logs, normalized_events, aggregated_events))

    output = "\n\n".join(output_parts)
    context = _store_active_auth_incident_context(agent, normalized_events, output)
    if context is not None:
        output_parts.append(format_active_auth_incident_summary(context))
        output = "\n\n".join(output_parts)
    return output


def _select_agent_inputs(agent_inputs, scope):
    if scope == "first":
        return agent_inputs[:1]
    return agent_inputs


def _format_agent_analysis_section(index, analysis):
    return "\n".join(
        [
            f"[SecurityAgent Analysis for Log Event {index}]",
            analysis,
        ]
    )


def _format_progress(index, total, agent_input):
    return "\n".join(
        [
            f"[Analyzing Log Event {index}/{total}]",
            f"Input: {agent_input}",
        ]
    )


def run_log_agent_analysis(agent, log_path: str, scope="all", progress_callback=None, result_callback=None) -> str:
    # Adapter bridge: aggregated log events are converted, then analyzed by the existing agent flow.
    error, result = _read_and_process_log(log_path)
    if error:
        return error

    _, _, _, aggregated_events = result
    all_agent_inputs = events_to_agent_inputs(aggregated_events)
    agent_inputs = _select_agent_inputs(all_agent_inputs, scope)
    if not all_agent_inputs:
        return LOG_AGENT_ANALYSIS_EMPTY_MESSAGE

    state = get_agent_state(agent)
    sections = []
    total = len(all_agent_inputs)
    for index, agent_input in enumerate(agent_inputs, start=1):
        if progress_callback:
            progress_callback(_format_progress(index, total, agent_input))

        analysis = run_with_progress(
            lambda: agent.handle_query(agent_input, state),
            f"Processing Log Event {index}/{total}",
        )
        section = _format_agent_analysis_section(index, analysis)
        if result_callback:
            result_callback(section)
        else:
            sections.append(section)

    return "\n\n".join(sections)
