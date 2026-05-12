from modules.evidence_correlator import correlate_auth_sequence
from modules.log_pipeline import normalize_event, parse_log_line
from modules.types import Incident


def make_auth_event(
    event_type: str,
    timestamp: str,
    *,
    source_ip: str = "10.0.0.5",
    user: str | None = "admin",
    target: str = "/login",
) -> dict:
    return {
        "event_type": event_type,
        "source_ip": source_ip,
        "target": target,
        "user": user,
        "timestamp": timestamp,
        "raw": f"{timestamp} {event_type} src_ip={source_ip} user={user} endpoint={target}",
    }


def make_failure_events(count: int, *, start_minute: int = 0, step_minutes: int = 1) -> list[dict]:
    return [
        make_auth_event(
            "auth_failure",
            f"2026-05-01T10:{start_minute + (index * step_minutes):02d}:00Z",
        )
        for index in range(count)
    ]


def test_auth_success_log_is_parsed_and_normalized():
    line = (
        "2026-05-01T10:04:30Z login_success "
        "src_ip=10.0.0.5 user=admin endpoint=/login status=200"
    )

    parsed = parse_log_line(line)
    normalized = normalize_event(parsed)

    assert normalized["event_type"] == "auth_success"
    assert normalized["source_ip"] == "10.0.0.5"
    assert normalized["user"] == "admin"
    assert normalized["target"] == "/login"
    assert normalized["status"] == "200"
    assert normalized["timestamp"] == "2026-05-01T10:04:30Z"
    assert normalized["raw"] == line


def test_below_threshold_does_not_create_incident():
    events = [
        *make_failure_events(4),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z"),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert incident is None


def test_threshold_failures_without_success_does_not_create_incident():
    incident = correlate_auth_sequence(
        make_failure_events(5),
        failure_threshold=5,
        window_minutes=5,
    )

    assert incident is None


def test_failures_followed_by_success_creates_incident():
    events = [
        *make_failure_events(5),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z"),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert isinstance(incident, Incident)
    assert incident.status == "SUSPICIOUS"
    assert incident.risk_level == "HIGH"
    assert incident.decision == "MONITOR"
    assert incident.attack_type == "Possible Account Compromise"
    assert incident.findings[0].finding_type == "possible_account_compromise"
    assert {"EV-001", "EV-002", "EV-003"}.issubset(incident.evidence_bundle.available_ids)
    assert set(incident.findings[0].evidence_ids).issubset(incident.evidence_bundle.available_ids)


def test_success_before_failures_does_not_create_incident():
    events = [
        make_auth_event("auth_success", "2026-05-01T10:00:00Z"),
        *make_failure_events(5, start_minute=1),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert incident is None


def test_different_user_does_not_correlate():
    events = [
        *make_failure_events(5),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z", user="alice"),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert incident is None


def test_different_target_does_not_correlate():
    events = [
        *make_failure_events(5),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z", target="/admin"),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert incident is None


def test_outside_time_window_does_not_correlate():
    events = [
        *make_failure_events(5, step_minutes=2),
        make_auth_event("auth_success", "2026-05-01T10:09:00Z"),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert incident is None


def test_invalid_timestamp_does_not_crash():
    events = [
        make_auth_event("auth_failure", "not-a-timestamp"),
        make_auth_event("auth_success", "also-invalid"),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=1, window_minutes=5)

    assert incident is None


def test_user_missing_fallback_grouping_creates_incident():
    events = [
        *[
            make_auth_event(
                "auth_failure",
                f"2026-05-01T10:0{index}:00Z",
                user=None,
            )
            for index in range(5)
        ],
        make_auth_event("auth_success", "2026-05-01T10:04:30Z", user=None),
    ]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert isinstance(incident, Incident)
    assert incident.evidence_bundle.get("EV-005") is None
    assert incident.evidence_bundle.get("EV-006") is not None


def test_incident_json_serialization_works():
    events = [
        *make_failure_events(5),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z"),
    ]
    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert incident is not None
    dumped = incident.to_json_dict()

    assert dumped["id"].startswith("INC-")
    assert dumped["findings"]
    assert dumped["evidence_bundle"]
    assert "generated_with" in dumped
