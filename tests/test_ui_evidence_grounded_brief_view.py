"""Focused tests for v2.9 Evidence-Grounded AI Brief UI helper."""

import subprocess
import sys
from pathlib import Path

from modules.event_followup import ActiveEventContext
from modules.ui.console_state import (
    ACTIVE_CONTEXT_KIND_KEY,
    ACTIVE_EVENT_CONTEXT_KEY,
    ACTIVE_INCIDENT_CONTEXT_KEY,
)
from modules.ui.evidence_grounded_brief_view import (
    build_evidence_grounded_brief_from_cli_state,
    render_evidence_grounded_brief_panel_html,
)

VIEW_PATH = Path(__file__).resolve().parents[1] / "modules" / "ui" / "evidence_grounded_brief_view.py"


def command_state() -> dict:
    context = ActiveEventContext(
        original_input="test; rm -rf /tmp/test",
        attack_types=("Command Injection",),
        matched_signatures={"Command Injection": ("; rm -rf",)},
        rule_ids=("CMD-001",),
        rule_sources=("detections/sample.yml",),
        risk_level="HIGH",
        decision="BLOCK",
        simulation_notice="Simulated BLOCK; no real enforcement.",
        rendered_report="[report]",
    )
    return {
        ACTIVE_CONTEXT_KIND_KEY: "event",
        ACTIVE_EVENT_CONTEXT_KEY: context,
        ACTIVE_INCIDENT_CONTEXT_KEY: None,
    }


def test_no_active_context_returns_empty_state() -> None:
    assert build_evidence_grounded_brief_from_cli_state({}) is None

    html = render_evidence_grounded_brief_panel_html({})

    assert "Run an analysis first" in html
    assert "sentinel-empty-card" in html


def test_panel_renders_official_verdict_advisory_context_and_citations() -> None:
    html = render_evidence_grounded_brief_panel_html(command_state())
    low = html.lower()

    assert "evidence-grounded advisory" in low
    assert "official verdict" in low
    assert "risk level: high" in low
    assert "decision: block" in low
    assert "supporting evidence" in low
    assert "citations" in low
    assert "rule-001" in low
    assert "ev-001" in low
    assert "human review is required" in low


def test_panel_includes_existing_knowledge_qa_answer_as_advisory_context() -> None:
    html = render_evidence_grounded_brief_panel_html(
        command_state(),
        rag_answer_text="Defensive RAG answer about HTTP/2 Resource Exhaustion telemetry.",
    ).lower()

    assert "knowledge q&amp;a / rag context is advisory only" in html
    assert "rag-001" in html


def test_panel_preserves_safety_boundary_wording() -> None:
    html = render_evidence_grounded_brief_panel_html(command_state()).lower()

    assert "simulated decisions only" in html
    assert "llm output must not override" in html
    assert "no exploit" in html
    assert "no real firewall" in html


def test_ui_helper_does_not_import_streamlit_or_heavy_runtime_dependencies() -> None:
    source = VIEW_PATH.read_text(encoding="utf-8").casefold()
    assert "import streamlit" not in source
    assert "modules.rag_qa" not in source
    assert "chromadb" not in source
    assert "ollama" not in source

    code = """
import importlib
import json
import sys

forbidden = [
    "streamlit", "ollama", "modules.rag", "modules.rag_qa", "chromadb",
    "torch", "sentence_transformers", "requests", "httpx", "openai", "langchain",
]
importlib.import_module("modules.ui.evidence_grounded_brief_view")
loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]
print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True, check=False)

    assert result.returncode == 0, result.stdout + result.stderr
