"""Focused tests for the v3.2 Full AI-assisted UI helper."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from modules.event_followup import ActiveEventContext
from modules.ui.console_state import (
    ACTIVE_CONTEXT_KIND_KEY,
    ACTIVE_EVENT_CONTEXT_KEY,
    ACTIVE_INCIDENT_CONTEXT_KEY,
)
from modules.ui.i18n import t
from modules.ui.full_ai_assisted_view import (
    build_full_ai_assisted_result_from_cli_state,
    render_full_ai_assisted_panel_html,
)

VIEW_PATH = Path(__file__).resolve().parents[1] / "modules" / "ui" / "full_ai_assisted_view.py"


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


def similar_case_result() -> SimpleNamespace:
    return SimpleNamespace(
        matches=[
            SimpleNamespace(
                seed=SimpleNamespace(
                    case_id="CASE-SEED-001",
                    title="Command Injection Payload",
                    outcome="Blocked in demo.",
                    analyst_conclusion="Payload suspicious.",
                ),
                score=120,
                reasons=("matched rule_ids: CMD-001",),
                differences=("Check execution telemetry.",),
            )
        ]
    )


def graph_snapshot() -> SimpleNamespace:
    return SimpleNamespace(
        nodes=[
            SimpleNamespace(id="current", label="Current Event"),
            SimpleNamespace(id="CASE-SEED-001", label="CASE-SEED-001"),
        ],
        edges=[
            SimpleNamespace(
                source_node_id="current",
                target_node_id="CASE-SEED-001",
                kind="RELATED_TO",
            )
        ],
    )


def test_no_active_context_returns_empty_state() -> None:
    assert build_full_ai_assisted_result_from_cli_state({}) is None

    html = render_full_ai_assisted_panel_html({}, language="en")

    assert "Run an analysis first" in html
    assert "sentinel-empty-card" in html


def test_disabled_provider_renders_deterministic_fallback_status() -> None:
    result = build_full_ai_assisted_result_from_cli_state(command_state(), language="en")
    html = render_full_ai_assisted_panel_html(command_state(), language="en").lower()

    assert result is not None
    assert result.provider_mode == "disabled"
    assert result.provider_status == "disabled"
    assert result.llm_status == "not_used_deterministic_fallback"
    assert result.guardrail_status == "not_run"
    assert "provider_mode: disabled" in html
    assert "provider_status: disabled" in html
    assert "llm_status: not_used_deterministic_fallback" in html
    assert "guardrail_status: not_run" in html


def test_official_verdict_appears_before_advisory_text() -> None:
    html = render_full_ai_assisted_panel_html(command_state(), language="en").lower()

    assert "official deterministic verdict" in html
    assert "advisory summary" in html
    assert html.index("official deterministic verdict") < html.index("advisory summary")
    assert "risk level: high" in html
    assert "decision: block" in html
    assert "authority:" in html


def test_optional_context_is_rendered_as_advisory_not_authority() -> None:
    html = render_full_ai_assisted_panel_html(
        command_state(),
        language="en",
        rag_answer_text="Defensive RAG answer about telemetry.",
        similar_case_result=similar_case_result(),
        graph_snapshot=graph_snapshot(),
    ).lower()

    assert "rag sources (advisory only)" in html
    assert "similar case context (advisory; not proof)" in html
    assert "not_proof=true" in html
    assert "graph context (advisory; not a detection source)" in html
    assert "not_detection_source=true" in html
    assert "case-seed-001" in html


def test_zh_tw_full_ai_labels_are_localized_and_keep_official_verdict() -> None:
    html = render_full_ai_assisted_panel_html(command_state(), language="zh-TW")

    assert "\u5b98\u65b9\u78ba\u5b9a\u6027\u5224\u5b9a" in html
    assert "\u5efa\u8b70\u6458\u8981" in html
    assert "\u8abf\u67e5\u5efa\u8b70" in html
    assert "\u8b49\u64da\u7f3a\u53e3" in html
    assert "\u4e0d\u5b89\u5168\u5047\u8a2d" in html
    assert "\u5f15\u7528\u4f9d\u64da" in html
    assert "\u5b89\u5168 / \u4eba\u5de5\u8907\u6838\u908a\u754c" in html
    assert "Risk Level: HIGH" in html
    assert "Decision: BLOCK" in html
    assert "??" not in html


def test_full_ai_streamlit_i18n_keys_have_zh_tw_values() -> None:
    assert t("full_ai_assisted_panel_title", "zh-TW") == "\u5b8c\u6574 AI \u8f14\u52a9\u5efa\u8b70\u7d50\u679c"
    assert "deterministic fallback" in t("full_ai_assisted_panel_caption", "zh-TW")
    assert "Risk Level / Decision" in t("full_ai_assisted_panel_caption", "zh-TW")


def test_full_ai_panel_preserves_safety_boundary() -> None:
    html = render_full_ai_assisted_panel_html(command_state(), language="en").lower()

    assert "simulated decisions only" in html
    assert "llm output must not override" in html
    assert "no exploit" in html
    assert "no real firewall" in html
    assert "human review" in html


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
importlib.import_module("modules.ui.full_ai_assisted_view")
loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]
print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True, check=False)

    assert result.returncode == 0, result.stdout + result.stderr
