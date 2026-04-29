BRUTE_FORCE_THRESHOLD = 10


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
    auth_failures = {}

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

        auth_failures.setdefault((source_ip, target), []).append(event)

    for (source_ip, target), related_events in auth_failures.items():
        # Promote repeated failures from the same source against the same target.
        if len(related_events) >= BRUTE_FORCE_THRESHOLD:
            output.append(_build_brute_force_event(source_ip, target, related_events))

    return output
