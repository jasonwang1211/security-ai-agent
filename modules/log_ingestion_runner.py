from modules.log_pipeline import aggregate_events, normalize_event, parse_log_line

SECTION_TITLES = ("Parsed Logs", "Normalized Events", "Aggregated Events")


def read_log_lines(file_path):
    # Keep line parsing simple and skip blank lines from demo files.
    with open(file_path, "r", encoding="utf-8") as log_file:
        return [line.rstrip("\n") for line in log_file if line.strip()]


def process_lines(lines):
    parsed_logs = [parse_log_line(line) for line in lines]
    normalized_events = [normalize_event(parsed) for parsed in parsed_logs]
    aggregated_events = aggregate_events(normalized_events)

    return parsed_logs, normalized_events, aggregated_events


_read_log_lines = read_log_lines
_process_lines = process_lines
