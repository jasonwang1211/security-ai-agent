import json
import sys

from modules.event_aggregator import aggregate_events
from modules.event_normalizer import normalize_event
from modules.log_parser import parse_log_line


USAGE = "python demo_log_ingestion.py demo_logs/auth_bruteforce.log"


def _print_section(title, data):
    print(title)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _read_log_lines(file_path):
    # Keep line parsing simple and skip blank lines from demo files.
    with open(file_path, "r", encoding="utf-8") as log_file:
        return [line.rstrip("\n") for line in log_file if line.strip()]


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return 1

    file_path = sys.argv[1]

    try:
        lines = _read_log_lines(file_path)
    except OSError as exc:
        print(f"Failed to read log file: {exc}")
        return 1

    parsed_logs = [parse_log_line(line) for line in lines]
    normalized_events = [normalize_event(parsed) for parsed in parsed_logs]
    aggregated_events = aggregate_events(normalized_events)

    _print_section("Parsed Logs", parsed_logs)
    _print_section("Normalized Events", normalized_events)
    _print_section("Aggregated Events", aggregated_events)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
