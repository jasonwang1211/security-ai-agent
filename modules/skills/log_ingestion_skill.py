import json

from demo_log_ingestion import SECTION_TITLES, _process_lines, _read_log_lines


def _format_section(title, data):
    return f"{title}\n{json.dumps(data, ensure_ascii=False, indent=2)}"


def run_log_ingestion(log_path: str) -> str:
    # Thin wrapper around the existing log ingestion demo pipeline.
    try:
        lines = _read_log_lines(log_path)
    except OSError as exc:
        return f"\n讀取 log 檔案失敗: {exc}\n"

    sections = [
        _format_section(title, data)
        for title, data in zip(SECTION_TITLES, _process_lines(lines))
    ]
    return "\n".join(sections)
