from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from modules.log_pipeline import BRUTE_FORCE_THRESHOLD
from modules.types import EvidenceBundle, EvidenceItem, Finding, Incident, SecurityEventModel


def parse_event_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def correlate_auth_sequence(
    events: list[SecurityEventModel] | list[dict],
    *,
    failure_threshold: int = BRUTE_FORCE_THRESHOLD,
    window_minutes: int = 5,
) -> Incident | None:
    normalized_events = _normalize_events(events)
    grouped_events = _group_auth_events(normalized_events)

    for group_events in grouped_events.values():
        incident = _find_incident_for_group(
            group_events,
            failure_threshold=failure_threshold,
            window_minutes=window_minutes,
        )
        if incident is not None:
            return incident

    return None


def _normalize_events(events: list[SecurityEventModel] | list[dict]) -> list[dict[str, Any]]:
    if not isinstance(events, list):
        return []

    normalized_events = []
    for index, event in enumerate(events, start=1):
        if isinstance(event, SecurityEventModel):
            event_data = event.model_dump()
        elif isinstance(event, dict):
            event_data = dict(event)
        else:
            continue

        timestamp = parse_event_timestamp(event_data.get("timestamp"))
        if timestamp is None:
            continue

        event_data["_correlation_timestamp"] = timestamp
        event_data["_correlation_event_id"] = f"event-{index}"
        normalized_events.append(event_data)

    return normalized_events


def _group_auth_events(events: list[dict[str, Any]]) -> dict[tuple[str, str, str | None], list[dict[str, Any]]]:
    grouped_events: dict[tuple[str, str, str | None], list[dict[str, Any]]] = {}

    for event in events:
        if event.get("event_type") not in ("auth_failure", "auth_success"):
            continue

        source_ip = _present_text(event.get("source_ip"))
        target = _present_text(event.get("target"))
        user = _present_text(event.get("user"))
        if not source_ip or not target:
            continue

        key = (source_ip, target, user)
        grouped_events.setdefault(key, []).append(event)

    return grouped_events


def _find_incident_for_group(
    events: list[dict[str, Any]],
    *,
    failure_threshold: int,
    window_minutes: int,
) -> Incident | None:
    sorted_events = sorted(events, key=lambda event: event["_correlation_timestamp"])
    failures = [event for event in sorted_events if event.get("event_type") == "auth_failure"]
    successes = [event for event in sorted_events if event.get("event_type") == "auth_success"]
    window = timedelta(minutes=window_minutes)

    for start_index, first_failure in enumerate(failures):
        window_start = first_failure["_correlation_timestamp"]
        window_end = window_start + window
        window_failures = [
            failure
            for failure in failures[start_index:]
            if window_start <= failure["_correlation_timestamp"] <= window_end
        ]

        if len(window_failures) < failure_threshold:
            continue

        last_failure_at = window_failures[failure_threshold - 1]["_correlation_timestamp"]
        matching_success = next(
            (
                success
                for success in successes
                if last_failure_at < success["_correlation_timestamp"] <= window_end
            ),
            None,
        )
        if matching_success is None:
            continue

        correlated_failures = window_failures[:failure_threshold]
        return _build_possible_account_compromise_incident(
            correlated_failures,
            matching_success,
            window_minutes=window_minutes,
        )

    return None


def _build_possible_account_compromise_incident(
    failures: list[dict[str, Any]],
    success: dict[str, Any],
    *,
    window_minutes: int,
) -> Incident:
    source_ip = _present_text(success.get("source_ip")) or "unknown"
    target = _present_text(success.get("target")) or "unknown"
    user = _present_text(success.get("user"))
    failure_count = len(failures)
    event_ids = [event["_correlation_event_id"] for event in [*failures, success]]

    evidence_items = [
        EvidenceItem(
            id="EV-001",
            type="failed_count",
            description=f"{failure_count} authentication failures were observed.",
            value=failure_count,
            source_event_ids=[event["_correlation_event_id"] for event in failures],
            confidence="high",
        ),
        EvidenceItem(
            id="EV-002",
            type="time_window",
            description=f"Failures occurred within a {window_minutes}-minute window.",
            value={"window_minutes": window_minutes},
            source_event_ids=[event["_correlation_event_id"] for event in failures],
            confidence="high",
        ),
        EvidenceItem(
            id="EV-003",
            type="success_after_failures",
            description="A successful authentication followed repeated failures.",
            value={"success_timestamp": success.get("timestamp")},
            source_event_ids=[success["_correlation_event_id"]],
            confidence="high",
        ),
        EvidenceItem(
            id="EV-004",
            type="same_source_ip",
            description=f"All correlated events came from source_ip {source_ip}.",
            value=source_ip,
            source_event_ids=event_ids,
            confidence="high",
        ),
    ]

    if user:
        evidence_items.append(
            EvidenceItem(
                id="EV-005",
                type="same_user",
                description=f"All correlated events involved user {user}.",
                value=user,
                source_event_ids=event_ids,
                confidence="high",
            )
        )

    evidence_items.append(
        EvidenceItem(
            id="EV-006",
            type="same_target",
            description=f"All correlated events targeted {target}.",
            value=target,
            source_event_ids=event_ids,
            confidence="high",
        )
    )

    evidence_bundle = EvidenceBundle(items=evidence_items)
    finding = Finding(
        id="F-001",
        finding_type="possible_account_compromise",
        title="Possible Account Compromise",
        status="SUSPICIOUS",
        risk_level="HIGH",
        decision="MONITOR",
        attack_type="Possible Account Compromise",
        evidence_ids=[item.id for item in evidence_items],
        explain_topics=[
            "risk_level_decision",
            "behavior_attack_triage",
            "investigation_checklist",
            "ai_assist_limitations",
        ],
        mitre_techniques=["T1110", "T1078"],
        summary="Repeated authentication failures were followed by a successful login.",
    )

    incident_id = _incident_id_from_timestamp(success["_correlation_timestamp"])
    evidence_bundle.incident_id = incident_id

    return Incident(
        id=incident_id,
        title="Possible Account Compromise",
        status="SUSPICIOUS",
        risk_level="HIGH",
        decision="MONITOR",
        attack_type="Possible Account Compromise",
        findings=[finding],
        evidence_bundle=evidence_bundle,
        timeline=_build_timeline([*failures, success]),
        recommended_response=[
            "Review the successful login session after repeated failures.",
            "Check whether the same source attempted other users.",
            "Consider session revocation or password reset after analyst review.",
        ],
    )


def _build_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "event_id": event["_correlation_event_id"],
            "event_type": event.get("event_type"),
            "timestamp": event.get("timestamp"),
            "source_ip": event.get("source_ip"),
            "user": event.get("user"),
            "target": event.get("target"),
        }
        for event in sorted(events, key=lambda item: item["_correlation_timestamp"])
    ]


def _incident_id_from_timestamp(timestamp: datetime) -> str:
    return f"INC-{timestamp.strftime('%Y%m%d')}-001"


def _present_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text else None
