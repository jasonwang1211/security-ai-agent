"""Focused tests for the v2.7-B Evidence Gap UI panel helper.

The panel is deterministic, advisory-only, and LLM-free. These tests assert the
empty state, per-scenario content (match != execution / exfiltration / confirmed
compromise), the always-present advisory boundary and llm_status metadata, that
no authoritative final verdict is exposed, and that importing the helper pulls in
no Ollama / RAGQA / Chroma / Torch runtime.
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from modules.ai_advisory import EvidenceGapAnalysis
from modules.event_followup import ActiveEventContext
from modules.ui.ai_advisory_view import (
    build_advisory_input,
    render_evidence_gap_panel_html,
)
from modules.ui.console_state import (
    ACTIVE_CONTEXT_KIND_KEY,
    ACTIVE_EVENT_CONTEXT_KEY,
    ACTIVE_INCIDENT_CONTEXT_KEY,
)

VIEW_PATH = Path(__file__).resolve().parents[1] / "modules" / "ui" / "ai_advisory_view.py"

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


# --------------------------------------------------------------------------- #
# Active-context fixtures
# --------------------------------------------------------------------------- #
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
    context = SimpleNamespace(incident=incident)
    return {
        ACTIVE_CONTEXT_KIND_KEY: "incident",
        ACTIVE_INCIDENT_CONTEXT_KEY: context,
        ACTIVE_EVENT_CONTEXT_KEY: None,
    }


# --------------------------------------------------------------------------- #
# Empty state
# --------------------------------------------------------------------------- #
def test_no_active_context_returns_empty_state() -> None:
    assert build_advisory_input({}) is None
    assert build_advisory_input(None) is None

    empty = render_evidence_gap_panel_html({}, language="en")
    assert "Run an analysis first to generate evidence-gap advisory context." in empty
    assert "sentinel-empty-card" in empty

    blank_kind = render_evidence_gap_panel_html(
        {ACTIVE_CONTEXT_KIND_KEY: "", ACTIVE_EVENT_CONTEXT_KEY: None}, language="en"
    )
    assert "Run an analysis first" in blank_kind


# --------------------------------------------------------------------------- #
# Scenario content
# --------------------------------------------------------------------------- #
def test_command_injection_panel_says_match_does_not_prove_execution() -> None:
    panel = render_evidence_gap_panel_html(command_injection_state(), language="en")
    low = panel.lower()

    assert "does not prove" in low
    assert "command execution" in low or "command was executed" in low
    assert "cmd-001" in low

    # All four sections render with translated (English) headings.
    assert "Confirmed facts" in panel
    assert "Missing evidence" in panel
    assert "Recommended checks" in panel
    assert "Unsafe assumptions" in panel

    # Missing / recommended cover the required command-injection sources.
    assert "process execution" in low
    assert "edr" in low
    assert "outbound" in low


def test_sql_injection_panel_does_not_claim_exfiltration() -> None:
    panel = render_evidence_gap_panel_html(sql_injection_state(), language="en")
    low = panel.lower()

    assert "sqli-001" in low
    # Explicit warning against claiming exfiltration.
    assert "do not claim data exfiltration" in low
    assert "database audit" in low


def test_authentication_panel_does_not_claim_confirmed_compromise() -> None:
    panel = render_evidence_gap_panel_html(auth_incident_state(), language="en")
    low = panel.lower()

    assert "confirmed account compromise" in low
    assert "do not claim" in low
    assert "mfa" in low
    # The observed failed-then-success sequence is confirmed (evidence labels present).
    assert "failed login" in low and "successful login" in low


# --------------------------------------------------------------------------- #
# Invariants
# --------------------------------------------------------------------------- #
def test_panel_includes_advisory_boundary_for_each_scenario() -> None:
    for state in (command_injection_state(), sql_injection_state(), auth_incident_state()):
        panel = render_evidence_gap_panel_html(state, language="en")
        low = panel.lower()
        assert "sentinel-gap-boundary" in panel
        assert "advisory" in low
        assert "does not" in low and "override" in low and "risk level" in low


def test_panel_includes_llm_status_not_used_and_source() -> None:
    panel = render_evidence_gap_panel_html(command_injection_state(), language="en")
    assert "llm_status: not_used" in panel
    assert "deterministic_ai_advisory" in panel


def test_panel_does_not_expose_advisory_as_final_risk_or_decision() -> None:
    # The advisory result type exposes no authoritative verdict fields.
    fields = set(EvidenceGapAnalysis.model_fields)
    assert "risk_level" not in fields
    assert "decision" not in fields

    panel = render_evidence_gap_panel_html(command_injection_state(), language="en")
    low = panel.lower()
    # The panel must frame itself as advisory and explicitly non-overriding.
    assert "override" in low and "risk level" in low
    assert "deterministic advisory" in low


# --------------------------------------------------------------------------- #
# Data mapping
# --------------------------------------------------------------------------- #
def test_event_context_maps_structured_facts() -> None:
    advisory_input = build_advisory_input(command_injection_state())
    assert advisory_input is not None
    assert advisory_input.event_kind == "payload_or_event"
    assert advisory_input.attack_type == "Command Injection"
    assert advisory_input.risk_label == "HIGH"
    assert advisory_input.decision_label == "BLOCK"
    assert advisory_input.matched_rule_ids == ["CMD-001"]
    assert advisory_input.matched_signatures == ["; rm -rf"]
    assert advisory_input.source_label == "active_event_context"


def test_incident_context_maps_structured_facts_without_inventing_ids() -> None:
    advisory_input = build_advisory_input(auth_incident_state())
    assert advisory_input is not None
    assert advisory_input.event_kind == "authentication_incident"
    assert advisory_input.finding_type == "Possible Account Compromise"
    assert advisory_input.risk_label == "HIGH"
    assert advisory_input.decision_label == "MONITOR"
    assert advisory_input.incident_id == "INC-001"
    assert advisory_input.finding_ids == ["F-001"]
    assert advisory_input.evidence_ids == ["EV-001", "EV-002"]
    assert advisory_input.evidence_labels == [
        "failed_login_attempts",
        "successful_login_after_failures",
    ]
    assert advisory_input.source_label == "active_incident_context"


def test_render_does_not_mutate_cli_state() -> None:
    state = command_injection_state()
    context_before = state[ACTIVE_EVENT_CONTEXT_KEY]
    render_evidence_gap_panel_html(state, language="en")
    # The frozen context object and the state mapping are untouched.
    assert state[ACTIVE_EVENT_CONTEXT_KEY] is context_before
    assert state[ACTIVE_EVENT_CONTEXT_KEY].rule_ids == ("CMD-001",)
    assert set(state) == {
        ACTIVE_CONTEXT_KIND_KEY,
        ACTIVE_EVENT_CONTEXT_KEY,
        ACTIVE_INCIDENT_CONTEXT_KEY,
    }


# --------------------------------------------------------------------------- #
# Framework / runtime isolation
# --------------------------------------------------------------------------- #
def test_view_module_does_not_import_streamlit() -> None:
    source = VIEW_PATH.read_text(encoding="utf-8")
    assert "streamlit" not in source.lower()


def test_view_import_stays_lightweight() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module("modules.ui.ai_advisory_view")

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
