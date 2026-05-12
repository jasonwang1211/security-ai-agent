import json

from modules.evidence_correlator import correlate_auth_sequence
from modules.incident_exporter import (
    incident_summary_for_export,
    incident_to_json_dict,
    incident_to_json_string,
    validate_incident_json_dict,
    write_incident_json,
)
from modules.types import Incident


def make_auth_event(event_type: str, timestamp: str) -> dict:
    return {
        "event_type": event_type,
        "source_ip": "10.0.0.5",
        "target": "/login",
        "user": "admin",
        "timestamp": timestamp,
        "raw": f"{timestamp} {event_type} src_ip=10.0.0.5 user=admin endpoint=/login",
    }


def make_incident() -> Incident:
    events = [
        make_auth_event("auth_failure", "2026-05-01T10:00:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:01:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:02:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:03:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:04:00Z"),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z"),
    ]
    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)
    assert incident is not None
    return incident


def test_incident_to_json_dict_returns_dict():
    incident = make_incident()

    exported = incident_to_json_dict(incident)

    assert isinstance(exported, dict)
    assert exported["id"].startswith("INC-")
    assert exported["findings"]
    assert exported["evidence_bundle"]
    assert exported["generated_with"]


def test_incident_to_json_string_returns_valid_json_with_unicode():
    incident = make_incident()
    incident.title = "可能的帳號入侵"
    incident.metadata["note"] = "測試匯出"

    output = incident_to_json_string(incident)
    loaded = json.loads(output)

    assert loaded["id"] == incident.id
    assert loaded["title"] == "可能的帳號入侵"
    assert loaded["metadata"]["note"] == "測試匯出"
    assert "可能的帳號入侵" in output


def test_write_incident_json_writes_file(tmp_path):
    incident = make_incident()
    export_path = tmp_path / "incident.json"

    written_path = write_incident_json(incident, export_path)

    assert written_path == export_path
    assert export_path.exists()
    loaded = json.loads(export_path.read_text(encoding="utf-8"))
    assert loaded["id"] == incident.id


def test_write_incident_json_creates_parent_directories(tmp_path):
    incident = make_incident()
    export_path = tmp_path / "nested" / "reports" / "incident.json"

    written_path = write_incident_json(incident, export_path)

    assert written_path == export_path
    assert export_path.exists()


def test_incident_summary_for_export_returns_compact_summary():
    incident = make_incident()

    summary = incident_summary_for_export(incident)

    assert summary["id"] == incident.id
    assert summary["finding_count"] == 1
    assert summary["evidence_count"] >= 3
    assert "T1110" in summary["mitre_techniques"]
    assert "T1078" in summary["mitre_techniques"]
    assert summary["generated_at"]
    assert summary["simulation_notice"] == incident.simulation_notice


def test_validate_incident_json_dict_returns_true_for_valid_export():
    exported = incident_to_json_dict(make_incident())

    assert validate_incident_json_dict(exported) is True


def test_validate_incident_json_dict_returns_false_when_required_key_is_missing():
    exported = incident_to_json_dict(make_incident())
    exported.pop("generated_with")

    assert validate_incident_json_dict(exported) is False


def test_export_does_not_mutate_incident():
    incident = make_incident()
    before = incident.to_json_dict()

    incident_to_json_dict(incident)
    incident_to_json_string(incident)
    after = incident.to_json_dict()

    assert after == before
