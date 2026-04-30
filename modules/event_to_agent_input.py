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
