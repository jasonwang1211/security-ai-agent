"""Pure demo-scenario catalog for the analyst console launcher.

This module only describes ready-to-load demo inputs and their *display hints*.
It does not run analysis, change detection / risk / decision logic, or alter any
backend behavior. The expected attack / risk / decision / case fields are
presentation hints for the demo launcher and are intentionally not enforced on
the deterministic backend. This helper must not import any UI framework.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.ui.i18n import DEFAULT_LANGUAGE, normalize_language, t

# Stable token for "no further action suggested" (mapped to an i18n label by UI).
SUGGESTED_NEXT_NONE = "none"
SUGGESTED_NEXT_FIND_SIMILAR = "find_similar_cases"


@dataclass(frozen=True)
class DemoScenario:
    """Immutable description of a loadable demo scenario (display hints only)."""

    scenario_id: str
    title_key: str
    description_key: str
    input_text: str
    expected_attack: str
    expected_risk: str
    expected_decision: str
    suggested_next_action: str
    expected_case_id: str | None = None
    preview_key: str | None = None


_DEMO_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario(
        scenario_id="command_injection",
        title_key="scenario_command_injection_title",
        description_key="scenario_command_injection_desc",
        input_text="test; rm -rf /tmp/test",
        expected_attack="Command Injection",
        expected_risk="HIGH",
        expected_decision="BLOCK",
        suggested_next_action=SUGGESTED_NEXT_FIND_SIMILAR,
        expected_case_id="CASE-SEED-001",
    ),
    DemoScenario(
        scenario_id="sql_injection",
        title_key="scenario_sql_injection_title",
        description_key="scenario_sql_injection_desc",
        input_text="?id=1' OR '1'='1",
        expected_attack="SQL Injection",
        expected_risk="HIGH",
        expected_decision="BLOCK",
        suggested_next_action=SUGGESTED_NEXT_FIND_SIMILAR,
        expected_case_id="CASE-SEED-003",
    ),
    DemoScenario(
        scenario_id="http2_resource_exhaustion",
        title_key="scenario_http2_resource_exhaustion_title",
        description_key="scenario_http2_resource_exhaustion_desc",
        input_text='[synthetic incident summary]\nevent_type=http2_resource_exhaustion_suspicion\nasset=edge-proxy-01\nprotocol=HTTP/2\nscenario=Resource Exhaustion Suspicion\nobservation_window=10m\nsignals:\n- low inbound request volume compared with elevated worker saturation\n- elevated concurrent stream count observed by reverse proxy metrics\n- repeated stream reset / long-lived connection pattern observed in telemetry\n- increased memory pressure and request queue delay\n- CVE context is not proof of successful abuse\nnotes:\n- synthetic demo only\n- no traffic generated\n- no vulnerability reproduction material\n- no real enforcement\n- human review required',
        expected_attack="HTTP/2 Resource Exhaustion Suspicion",
        expected_risk="MEDIUM",
        expected_decision="MONITOR",
        suggested_next_action=SUGGESTED_NEXT_NONE,
        expected_case_id=None,
        preview_key="scenario_http2_resource_exhaustion_preview",
    ),
    DemoScenario(
        scenario_id="authentication_incident",
        title_key="scenario_auth_incident_title",
        description_key="scenario_auth_incident_desc",
        input_text="demo_logs\\scenario_a_mixed_auth.log",
        expected_attack="Possible Account Compromise",
        expected_risk="HIGH",
        expected_decision="MONITOR",
        suggested_next_action=SUGGESTED_NEXT_FIND_SIMILAR,
        expected_case_id="CASE-SEED-002",
    ),
)


def list_demo_scenarios() -> tuple[DemoScenario, ...]:
    """Return the ordered tuple of available demo scenarios."""

    return _DEMO_SCENARIOS


def find_demo_scenario(scenario_id: str) -> DemoScenario | None:
    """Return the scenario with the given ID, or None when it is absent."""

    target = str(scenario_id or "")
    for scenario in _DEMO_SCENARIOS:
        if scenario.scenario_id == target:
            return scenario
    return None


def scenario_titles(language: str = DEFAULT_LANGUAGE) -> tuple[str, ...]:
    """Return the language-aware display titles for all demo scenarios."""

    selected = normalize_language(language)
    return tuple(t(scenario.title_key, selected) for scenario in _DEMO_SCENARIOS)


def scenario_preview_text(
    scenario: DemoScenario, language: str = DEFAULT_LANGUAGE
) -> str:
    """Return compact launcher preview text without changing loadable input."""

    selected = normalize_language(language)
    if scenario.preview_key:
        return t(scenario.preview_key, selected)
    return scenario.input_text
