from modules.log_pipeline import (
    BRUTE_FORCE_THRESHOLD,
    aggregate_events,
    normalize_event,
    parse_log_line,
)


def _auth_failure_event(index: int = 0) -> dict:
    return {
        "event_type": "auth_failure",
        "source_ip": "10.0.0.5",
        "target": "/login",
        "user": f"user{index}",
        "method": None,
        "status": "401",
        "payload": None,
        "raw": f"login_failed user=user{index}",
    }


def test_blank_line_parsing_does_not_crash():
    parsed = parse_log_line("")

    assert isinstance(parsed, dict)
    assert parsed["raw"] == ""


def test_malformed_line_parsing_does_not_crash_or_normalize_as_auth_failure():
    parsed = parse_log_line("this is not a valid auth log")
    normalized = normalize_event(parsed)

    assert isinstance(parsed, dict)
    assert isinstance(normalized, dict)
    assert normalized["event_type"] != "auth_failure"


def test_simple_auth_failure_log_is_parsed_and_normalized():
    line = (
        "2026-05-01T10:00:00Z login_failed "
        "src_ip=10.0.0.5 user=admin endpoint=/login status=401"
    )

    parsed = parse_log_line(line)
    normalized = normalize_event(parsed)

    assert normalized["event_type"] == "auth_failure"
    assert normalized["source_ip"] == "10.0.0.5"
    assert normalized["user"] == "admin"
    assert normalized["target"] == "/login"
    assert normalized["status"] == "401"


def test_below_brute_force_threshold_does_not_create_candidate():
    events = [_auth_failure_event(index) for index in range(BRUTE_FORCE_THRESHOLD - 1)]

    aggregated = aggregate_events(events)

    assert all(event.get("event_type") != "brute_force_candidate" for event in aggregated)


def test_threshold_failures_create_brute_force_candidate():
    events = [_auth_failure_event(index) for index in range(BRUTE_FORCE_THRESHOLD)]

    aggregated = aggregate_events(events)

    candidates = [
        event for event in aggregated if event.get("event_type") == "brute_force_candidate"
    ]
    assert len(candidates) == 1
    assert candidates[0]["failed_count"] == BRUTE_FORCE_THRESHOLD
    assert candidates[0]["source_ip"] == "10.0.0.5"
    assert candidates[0]["target"] == "/login"


def test_web_access_log_with_suspicious_query_becomes_web_request_with_payload():
    line = (
        "10.0.0.5 - - [01/May/2026:10:00:00 +0800] "
        "\"GET /search?q=' OR '1'='1 HTTP/1.1\" 200"
    )

    parsed = parse_log_line(line)
    normalized = normalize_event(parsed)

    assert normalized["event_type"] == "web_request"
    assert normalized["source_ip"] == "10.0.0.5"
    assert normalized["target"] == "/search"
    assert normalized["payload"] == "q=' OR '1'='1"
