"""Focused tests for the v2.7-H AI Analyst Brief UI helper."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from modules.event_followup import ActiveEventContext
from modules.ui.ai_analyst_brief_view import (
    build_ai_analyst_brief_from_cli_state,
    render_ai_analyst_brief_panel_html,
)
from modules.ui.console_state import (
    ACTIVE_CONTEXT_KIND_KEY,
    ACTIVE_EVENT_CONTEXT_KEY,
    ACTIVE_INCIDENT_CONTEXT_KEY,
)

VIEW_PATH = Path(__file__).resolve().parents[1] / "modules" / "ui" / "ai_analyst_brief_view.py"
FORBIDDEN_RUNTIME_MODULES = [
    "streamlit",
    "ollama",
    "modules.rag",
    "modules.rag_qa",
    "chromadb",
    "torch",
    "sentence_transformers",
    "requests",
    "httpx",
    "openai",
    "langchain",
]


def _event_state(attack_type: str, rule_id: str, signature: str) -> dict:
    context = ActiveEventContext(
        original_input="test; rm -rf /tmp/test",
        attack_types=(attack_type,),
        matched_signatures={attack_type: (signature,)},
        rule_ids=(rule_id,),
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


def command_injection_state() -> dict:
    return _event_state("Command Injection", "CMD-001", "; rm -rf")


def sql_injection_state() -> dict:
    return _event_state("SQL Injection", "SQLI-001", "' OR '1'='1")


def auth_incident_state() -> dict:
    incident = SimpleNamespace(
        id="INC-001",
        title="Authentication Incident",
        attack_type="Possible Account Compromise",
        risk_level="HIGH",
        decision="MONITOR",
        findings=[SimpleNamespace(id="F-001", finding_type="Possible Account Compromise")],
        evidence_bundle=SimpleNamespace(
            items=[
                SimpleNamespace(id="EV-001", type="failed_login_attempts"),
                SimpleNamespace(id="EV-002", type="successful_login_after_failures"),
            ],
            available_ids={"EV-001", "EV-002"},
        ),
    )
    return {
        ACTIVE_CONTEXT_KIND_KEY: "incident",
        ACTIVE_INCIDENT_CONTEXT_KEY: SimpleNamespace(incident=incident),
        ACTIVE_EVENT_CONTEXT_KEY: None,
    }


def test_no_active_context_returns_empty_state() -> None:
    assert build_ai_analyst_brief_from_cli_state({}) is None

    html = render_ai_analyst_brief_panel_html({}, language="en")

    assert "Run an analysis first to generate an AI Analyst Brief." in html
    assert "sentinel-empty-card" in html


def test_command_injection_active_context_renders_brief() -> None:
    html = render_ai_analyst_brief_panel_html(command_injection_state(), language="en")
    low = html.casefold()

    assert "ai analyst brief is deterministic advisory context only" in low
    assert "cmd-001" in low
    assert "command injection" in low
    assert "high" in low and "block" in low
    assert "successful command execution is not proven" in low or "does not prove command execution" in low
    assert "llm_status: not_used" in html
    assert "deterministic_ai_analyst_brief" in html


def test_command_injection_active_context_renders_zh_tw_brief() -> None:
    html = render_ai_analyst_brief_panel_html(command_injection_state(), language="zh-TW")
    low = html.casefold()

    assert "規則式偵測命中 command injection" in low
    assert "不代表命令已成功執行" in low
    assert "llm_status: not_used" in html
    assert "不執行真實 firewall" in low


def test_command_injection_active_context_renders_bilingual_brief() -> None:
    html = render_ai_analyst_brief_panel_html(command_injection_state(), language="bilingual")
    low = html.casefold()

    assert "規則式偵測命中 command injection" in low
    assert "rule-based detection matched command injection" in low
    assert "no real enforcement" in low


def test_sql_injection_active_context_does_not_claim_confirmed_exfiltration() -> None:
    html = render_ai_analyst_brief_panel_html(sql_injection_state(), language="en")
    low = html.casefold()

    assert "sqli-001" in low
    assert "sql injection" in low
    assert "exfiltration" in low
    assert "not proven" in low or "do not claim data exfiltration" in low
    assert "confirmed exfiltration" not in low
    assert "exfiltration confirmed" not in low


def test_authentication_incident_context_does_not_claim_confirmed_compromise() -> None:
    html = render_ai_analyst_brief_panel_html(auth_incident_state(), language="en")
    low = html.casefold()

    assert "possible account compromise" in low
    assert "confirmed account compromise" in low
    assert "do not claim" in low or "before claiming" in low
    assert "mfa" in low
    assert "device" in low and "session" in low


def test_rendered_output_includes_safety_boundary_and_no_override_wording() -> None:
    html = render_ai_analyst_brief_panel_html(command_injection_state(), language="en")
    low = html.casefold()

    assert "sentinel-brief-boundary" in html
    assert "detection is rule-based" in low
    assert "risk level and decision are deterministic" in low
    assert "block / monitor / allow are simulated" in low
    assert "does not override" in low
    assert "human review is required" in low


def test_rendered_output_does_not_expose_final_field_names() -> None:
    html = render_ai_analyst_brief_panel_html(command_injection_state(), language="en")
    low = html.casefold()

    assert "risk_level:" not in low
    assert "decision:" not in low
    assert "final_decision" not in low
    assert "final_risk" not in low


def test_render_does_not_mutate_cli_state_or_active_context() -> None:
    state = command_injection_state()
    context_before = state[ACTIVE_EVENT_CONTEXT_KEY]

    render_ai_analyst_brief_panel_html(state, language="en")

    assert state[ACTIVE_EVENT_CONTEXT_KEY] is context_before
    assert state[ACTIVE_EVENT_CONTEXT_KEY].rule_ids == ("CMD-001",)
    assert set(state) == {
        ACTIVE_CONTEXT_KIND_KEY,
        ACTIVE_EVENT_CONTEXT_KEY,
        ACTIVE_INCIDENT_CONTEXT_KEY,
    }


def test_view_module_does_not_import_streamlit() -> None:
    source = VIEW_PATH.read_text(encoding="utf-8")

    assert "import streamlit" not in source.casefold()
    assert "streamlit" not in sys.modules


def test_view_import_stays_lightweight() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}
importlib.import_module("modules.ui.ai_analyst_brief_view")
loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]
print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
