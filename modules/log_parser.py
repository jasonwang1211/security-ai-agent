import re
import shlex
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

ISO_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\S+$")

WEB_ACCESS_RE = re.compile(
    r'^(?P<src_ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<request>[^"]+)"\s+'
    r"(?P<status>\d{3})(?:\s|$)"
)


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
    for field in ("timestamp", "src_ip", "event", "user", "endpoint", "status"):
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
    match = re.match(r"^(?P<method>[A-Z]+)\s+(?P<target>.+)\s+HTTP/\S+$", request)

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
        for parser in (
            _parse_web_access_log,
            _parse_key_value_log,
            _parse_simple_auth_log,
        ):
            parsed = parser(stripped)
            if parsed is not None:
                parsed["raw"] = raw
                return parsed
    except Exception:
        pass

    return _empty_result(raw)
