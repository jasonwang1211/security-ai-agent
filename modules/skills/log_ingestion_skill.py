import json
from collections import Counter

from demo_log_ingestion import SECTION_TITLES, _process_lines, _read_log_lines


def _format_section(title, data):
    return f"{title}\n{json.dumps(data, ensure_ascii=False, indent=2)}"


def _format_event_type_counts(normalized_events):
    counts = Counter(
        event.get("event_type", "unknown")
        for event in normalized_events
        if isinstance(event, dict)
    )
    if not counts:
        return ["Detected Event Types:", "- None"]

    lines = ["Detected Event Types:"]
    lines.extend(f"- {event_type}: {count}" for event_type, count in counts.items())
    return lines


def _format_aggregated_findings(aggregated_events):
    findings = [
        event
        for event in aggregated_events
        if isinstance(event, dict) and event.get("event_type") == "brute_force_candidate"
    ]
    if not findings:
        return []

    lines = ["Aggregated Findings:"]
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


def _format_preserved_payloads(normalized_events):
    payloads = [
        event.get("payload")
        for event in normalized_events
        if (
            isinstance(event, dict)
            and event.get("event_type") == "web_request"
            and event.get("payload")
        )
    ]
    if not payloads:
        return []

    lines = ["Preserved Payloads:"]
    lines.extend(f"{index}. {payload}" for index, payload in enumerate(payloads, start=1))
    return lines


def _format_summary(log_path, lines, parsed_logs, normalized_events, aggregated_events):
    summary = [
        "[Log Ingestion Summary]",
        "",
        f"File: {log_path}",
        f"Total Lines: {len(lines)}",
        f"Parsed Logs: {len(parsed_logs)}",
        f"Normalized Events: {len(normalized_events)}",
        f"Aggregated Events: {len(aggregated_events)}",
        "",
    ]
    summary.extend(_format_event_type_counts(normalized_events))

    aggregated_findings = _format_aggregated_findings(aggregated_events)
    if aggregated_findings:
        summary.extend(["", *aggregated_findings])

    preserved_payloads = _format_preserved_payloads(normalized_events)
    if preserved_payloads:
        summary.extend(["", *preserved_payloads])

    summary.extend(
        [
            "",
            "Current Stage:",
            "Log ingestion only. Events are not sent into SecurityAgent yet.",
        ]
    )
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


def run_log_ingestion(log_path: str, include_json: bool = False) -> str:
    # Thin wrapper around the existing log ingestion demo pipeline.
    try:
        lines = _read_log_lines(log_path)
    except OSError as exc:
        return f"\n讀取 log 檔案失敗: {exc}\n"

    parsed_logs, normalized_events, aggregated_events = _process_lines(lines)
    output = _format_summary(
        log_path,
        lines,
        parsed_logs,
        normalized_events,
        aggregated_events,
    )

    if include_json:
        output = "\n\n".join(
            [
                output,
                _format_detailed_json(parsed_logs, normalized_events, aggregated_events),
            ]
        )

    return output
