from dataclasses import dataclass
from typing import Optional

from modules.event_normalizer import normalize_event
from modules.event_to_agent_input import event_to_agent_input
from modules.log_parser import parse_log_line


@dataclass(frozen=True)
class LogInputTranslation:
    detected_input_type: str
    normalized_event_type: str
    agent_input: str
    normalized_event: dict


def _is_single_line(value: str) -> bool:
    lines = [line for line in str(value or "").splitlines() if line.strip()]
    return len(lines) == 1


def _has_meaningful_parsed_fields(parsed_log: dict, normalized_event: dict) -> bool:
    if not isinstance(parsed_log, dict) or not isinstance(normalized_event, dict):
        return False

    if parsed_log.get("method") and parsed_log.get("path"):
        return True

    if parsed_log.get("event") == "login_failed":
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
