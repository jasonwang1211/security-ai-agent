import json
import sys

from modules.log_ingestion_runner import SECTION_TITLES, process_lines, read_log_lines


USAGE = "python demo_log_ingestion.py demo_logs/auth_bruteforce.log"


def _print_section(title, data):
    print(title)
    print(json.dumps(data, ensure_ascii=False, indent=2))


_read_log_lines = read_log_lines
_process_lines = process_lines


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return 1

    file_path = sys.argv[1]

    try:
        lines = read_log_lines(file_path)
    except OSError as exc:
        print(f"Failed to read log file: {exc}")
        return 1

    for title, data in zip(SECTION_TITLES, process_lines(lines)):
        _print_section(title, data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
