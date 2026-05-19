import ast
import subprocess
import sys
from pathlib import Path

from modules.log_ingestion_runner import (
    SECTION_TITLES,
    process_lines,
    read_log_lines,
)


def _imports_from(path: str) -> list[ast.ImportFrom]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    return [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]


def test_mode_handlers_does_not_import_demo_log_ingestion():
    imported_modules = {node.module for node in _imports_from("modules/mode_handlers.py")}

    assert "demo_log_ingestion" not in imported_modules


def test_log_ingestion_runner_import_is_runtime_safe():
    code = (
        "import sys; "
        "import modules.log_ingestion_runner; "
        "forbidden={'app','modules.rag_qa','chromadb','ollama','langchain','torch'}; "
        "present=forbidden.intersection(sys.modules); "
        "raise SystemExit(1 if present else 0)"
    )

    result = subprocess.run([sys.executable, "-c", code], check=False)

    assert result.returncode == 0


def test_demo_log_ingestion_imports_reusable_helpers_from_runner():
    imports = _imports_from("demo_log_ingestion.py")

    assert any(
        node.module == "modules.log_ingestion_runner"
        and {"SECTION_TITLES", "process_lines", "read_log_lines"}.issubset(
            {alias.name for alias in node.names}
        )
        for node in imports
    )


def test_read_log_lines_skips_blank_lines(tmp_path):
    log_path = tmp_path / "sample.log"
    log_path.write_text("line one\n\n  \nline two\n", encoding="utf-8")

    assert read_log_lines(log_path) == ["line one", "line two"]


def test_process_lines_preserves_demo_output_shape():
    parsed_logs, normalized_events, aggregated_events = process_lines(
        ["Jan 10 10:00:01 host sshd[1]: Failed password for invalid user admin from 203.0.113.9 port 2222 ssh2"]
    )

    assert SECTION_TITLES == ("Parsed Logs", "Normalized Events", "Aggregated Events")
    assert len(parsed_logs) == 1
    assert len(normalized_events) == 1
    assert isinstance(aggregated_events, list)
