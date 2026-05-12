import re
import shlex
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit

FIELDS = (
    "raw",
    "timestamp",
    "src_ip",
    "event",
    "user",
    "method",
    "path",
    "query",
    "endpoint",
    "status",
)

KNOWN_KEY_VALUE_FIELDS = ("timestamp", "src_ip", "event", "user", "endpoint", "status")
ISO_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\S+$")
WEB_REQUEST_RE = re.compile(r"^(?P<method>[A-Z]+)\s+(?P<target>.+)\s+HTTP/\S+$")
WEB_ACCESS_RE = re.compile(
    r'^(?P<src_ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<request>[^"]+)"\s+'
    r"(?P<status>\d{3})(?:\s|$)"
)

SUSPICIOUS_MARKERS = (
    "<script",
    "alert(",
    "onerror=",
    "../",
    "..\\",
    "/etc/passwd",
    "' or '1'='1",
    "'--",
    "union select",
    "drop table",
)

AUTH_FAILURE_STATUSES = ("401", "403")
NORMALIZED_EVENT_FIELDS = (
    "event_type",
    "source_ip",
    "target",
    "user",
    "timestamp",
    "method",
    "status",
    "payload",
    "raw",
)
BRUTE_FORCE_THRESHOLD = 10


@dataclass(frozen=True)
class LogInputTranslation:
    detected_input_type: str
    normalized_event_type: str
    agent_input: str
    normalized_event: dict


def _empty_result(raw):
    return {field: (raw if field == "raw" else None) for field in FIELDS}


def _parse_key_values(parts):
    values = {}

    for part in parts:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        if key:
            values[key] = value

    return values


def _apply_known_values(result, values):
    # Copy only fields used by the normalized parser output.
    for field in KNOWN_KEY_VALUE_FIELDS:
        if field in values:
            result[field] = values[field]

    return result


def _parse_key_value_log(line):
    parts = shlex.split(line)
    values = _parse_key_values(parts)

    if not values or "timestamp" not in values:
        return None

    return _apply_known_values(_empty_result(line), values)


def _parse_simple_auth_log(line):
    parts = shlex.split(line)

    if len(parts) < 2 or "=" in parts[0] or "=" in parts[1]:
        return None
    if not ISO_TIMESTAMP_RE.match(parts[0]):
        return None

    values = _parse_key_values(parts[2:])
    result = _empty_result(line)
    result["timestamp"] = parts[0]
    result["event"] = parts[1]

    return _apply_known_values(result, values)


def _parse_web_request(request):
    # Capture the target lazily so spaces inside suspicious URLs are preserved.
    match = WEB_REQUEST_RE.match(request)

    if not match:
        return None, None

    return match.group("method"), match.group("target")


def _parse_web_access_log(line):
    match = WEB_ACCESS_RE.match(line)

    if not match:
        return None

    method, target = _parse_web_request(match.group("request"))
    if not method or not target:
        return None

    parsed_target = urlsplit(target)
    path = parsed_target.path or None
    query = parsed_target.query or None

    result = _empty_result(line)
    result["timestamp"] = match.group("timestamp")
    result["src_ip"] = match.group("src_ip")
    result["event"] = "web_access"
    result["method"] = method
    result["path"] = path
    result["query"] = query
    result["endpoint"] = path
    result["status"] = match.group("status")

    return result


def parse_log_line(line: str) -> dict:
    """Parse a supported log line into a normalized dictionary."""
    raw = "" if line is None else str(line)

    try:
        stripped = raw.strip()
        if not stripped:
            return _empty_result(raw)

        # Try the most specific structured formats before falling back.
        for parser in PARSERS:
            parsed = parser(stripped)
            if parsed is not None:
                parsed["raw"] = raw
                return parsed
    except Exception:
        pass

    return _empty_result(raw)


def _blank_event(raw):
    event = {field: None for field in NORMALIZED_EVENT_FIELDS}
    event["event_type"] = "generic_event"
    event["raw"] = raw
    return event


def _first_present(*values):
    for value in values:
        if value not in (None, ""):
            return value

    return None


def _is_auth_status(status):
    return str(status) in AUTH_FAILURE_STATUSES


def _contains_login(target):
    return "/login" in str(target or "").lower()


def _looks_suspicious(value):
    text = str(value or "").lower()
    return any(marker in text for marker in SUSPICIOUS_MARKERS)


def normalize_event(parsed_log: dict) -> dict:
    """Convert a parsed log dictionary into a normalized event."""
    if not isinstance(parsed_log, dict):
        return _blank_event(None)

    raw = parsed_log.get("raw")
    target = _first_present(parsed_log.get("endpoint"), parsed_log.get("path"))
    path = parsed_log.get("path")
    query = parsed_log.get("query")

    event = _blank_event(raw)
    event.update(
        {
            "source_ip": parsed_log.get("src_ip"),
            "target": target,
            "user": parsed_log.get("user"),
            "timestamp": parsed_log.get("timestamp"),
            "method": parsed_log.get("method"),
            "status": parsed_log.get("status"),
        }
    )

    # Prefer query payloads, then preserve suspicious paths as payloads.
    if query not in (None, ""):
        event["payload"] = query
    elif _looks_suspicious(path):
        event["payload"] = path

    # Auth failures take precedence over generic web request classification.
    if parsed_log.get("event") == "login_failed":
        event["event_type"] = "auth_failure"
    elif parsed_log.get("event") in ("login_success", "auth_success"):
        event["event_type"] = "auth_success"
    elif _is_auth_status(event["status"]) and _contains_login(target):
        event["event_type"] = "auth_failure"
    elif event["method"] and path:
        event["event_type"] = "web_request"

    return event


def _group_key(event):
    return (event.get("source_ip"), event.get("target"))


def _build_brute_force_event(source_ip, target, related_events):
    failed_count = len(related_events)

    return {
        "event_type": "brute_force_candidate",
        "source_ip": source_ip,
        "target": target,
        "failed_count": failed_count,
        "evidence": [
            f"{failed_count} failed login events from same source_ip against same target"
        ],
        "related_events": related_events,
    }


def aggregate_events(events: list[dict]) -> list[dict]:
    """Aggregate normalized events into higher-level detection candidates."""
    if not isinstance(events, list):
        return []

    output = []
    auth_failures = defaultdict(list)

    for event in events:
        if not isinstance(event, dict):
            continue

        # Preserve non-aggregated web requests for downstream analysis.
        if event.get("event_type") == "web_request":
            output.append(event)

        if event.get("event_type") != "auth_failure":
            continue

        source_ip, target = _group_key(event)
        if not source_ip or not target:
            continue

        auth_failures[(source_ip, target)].append(event)

    for (source_ip, target), related_events in auth_failures.items():
        # Promote repeated failures from the same source against the same target.
        if len(related_events) >= BRUTE_FORCE_THRESHOLD:
            output.append(_build_brute_force_event(source_ip, target, related_events))

    return output


def _as_text(value, default="unknown"):
    text = str(value or "").strip()
    return text if text else default


def _join_evidence(evidence):
    if isinstance(evidence, str):
        return evidence.strip() or "none"

    try:
        items = [str(item).strip() for item in evidence or [] if str(item).strip()]
    except TypeError:
        items = [str(evidence).strip()]

    return ", ".join(items) if items else "none"


def _describe_auth_failure(event):
    source_ip = _as_text(event.get("source_ip"))
    target = _as_text(event.get("target"))
    user = str(event.get("user") or "").strip()

    description = f"login failed from source_ip {source_ip} against {target}"
    if user:
        description += f" for user {user}"
    return description


def event_to_agent_input(event: dict) -> str:
    # Adapter bridge: turn normalized/aggregated log events into existing agent text inputs.
    if not event:
        return ""

    if not isinstance(event, dict):
        return str(event).strip()

    event_type = str(event.get("event_type") or "unknown").strip()

    if event_type == "brute_force_candidate":
        return (
            f"login failed {_as_text(event.get('failed_count'))} times "
            f"from source_ip {_as_text(event.get('source_ip'))} "
            f"against {_as_text(event.get('target'))}. "
            f"Evidence: {_join_evidence(event.get('evidence'))}"
        )

    if event_type == "web_request":
        payload = str(event.get("payload") or "").strip()
        if payload:
            return payload

        raw = str(event.get("raw") or "").strip()
        if raw:
            return raw

        return (
            f"web request method {_as_text(event.get('method'))} "
            f"against {_as_text(event.get('target'))}"
        )

    if event_type == "auth_failure":
        return _describe_auth_failure(event)

    raw = str(event.get("raw") or "").strip()
    if raw:
        return raw

    return (
        f"{_as_text(event_type, 'unknown event')} event "
        f"from source_ip {_as_text(event.get('source_ip'))} "
        f"against {_as_text(event.get('target'))}"
    )


def events_to_agent_inputs(events: list[dict]) -> list[str]:
    if not isinstance(events, list):
        return []

    inputs = [event_to_agent_input(event) for event in events]
    return [item for item in inputs if item]


def _is_single_line(value: str) -> bool:
    lines = [line for line in str(value or "").splitlines() if line.strip()]
    return len(lines) == 1


def _has_meaningful_parsed_fields(parsed_log: dict, normalized_event: dict) -> bool:
    if not isinstance(parsed_log, dict) or not isinstance(normalized_event, dict):
        return False

    if parsed_log.get("method") and parsed_log.get("path"):
        return True

    if parsed_log.get("event") in ("login_failed", "login_success", "auth_success"):
        return True

    if parsed_log.get("src_ip") and parsed_log.get("status"):
        return True

    return normalized_event.get("event_type") != "generic_event"


def try_translate_raw_log_input(user_input: str) -> Optional[LogInputTranslation]:
    if not _is_single_line(user_input):
        return None

    parsed_log = parse_log_line(user_input)
    normalized_event = normalize_event(parsed_log)

    if not _has_meaningful_parsed_fields(parsed_log, normalized_event):
        return None

    agent_input = event_to_agent_input(normalized_event)
    if not agent_input:
        return None

    return LogInputTranslation(
        detected_input_type="raw_log",
        normalized_event_type=normalized_event.get("event_type") or "unknown",
        agent_input=agent_input,
        normalized_event=normalized_event,
    )


def format_input_translation(translation: LogInputTranslation) -> str:
    return "\n".join(
        [
            "[Input Translation]",
            f"Detected Input Type: {translation.detected_input_type}",
            f"Normalized Event Type: {translation.normalized_event_type}",
            "Converted SecurityAgent Input:",
            translation.agent_input,
        ]
    )


PARSERS = (
    _parse_web_access_log,
    _parse_key_value_log,
    _parse_simple_auth_log,
)
