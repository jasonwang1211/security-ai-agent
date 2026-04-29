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
    "method",
    "status",
    "payload",
    "raw",
)


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
    elif _is_auth_status(event["status"]) and _contains_login(target):
        event["event_type"] = "auth_failure"
    elif event["method"] and path:
        event["event_type"] = "web_request"

    return event
