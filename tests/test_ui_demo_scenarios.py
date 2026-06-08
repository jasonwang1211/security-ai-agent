import dataclasses
import sys
from pathlib import Path

import pytest

from modules.ui.demo_scenarios import (
    DemoScenario,
    find_demo_scenario,
    list_demo_scenarios,
    scenario_titles,
)


def _by_id(scenario_id: str) -> DemoScenario:
    scenario = find_demo_scenario(scenario_id)
    assert scenario is not None
    return scenario


def test_list_demo_scenarios_returns_exactly_four_required_scenarios() -> None:
    scenarios = list_demo_scenarios()

    assert len(scenarios) == 4
    assert {scenario.scenario_id for scenario in scenarios} == {
        "command_injection",
        "sql_injection",
        "authentication_incident",
        "benign_input",
    }


def test_scenario_ids_are_unique() -> None:
    ids = [scenario.scenario_id for scenario in list_demo_scenarios()]

    assert len(ids) == len(set(ids))


def test_command_injection_scenario_input() -> None:
    assert _by_id("command_injection").input_text == "test; rm -rf /tmp/test"


def test_sql_injection_scenario_contains_or() -> None:
    assert "OR" in _by_id("sql_injection").input_text


def test_authentication_scenario_input() -> None:
    assert _by_id("authentication_incident").input_text == "demo_logs\\scenario_a_mixed_auth.log"


def test_benign_scenario_input() -> None:
    assert _by_id("benign_input").input_text == "hello world"


def test_benign_scenario_uses_no_attack_hints_not_low_allow() -> None:
    benign = _by_id("benign_input")

    assert benign.expected_attack == "No attack detected"
    assert benign.expected_risk == "N/A"
    assert benign.expected_decision == "No simulated decision"
    # the launcher must not promise a LOW/ALLOW verdict the backend may not produce.
    assert benign.expected_risk != "LOW"
    assert benign.expected_decision != "ALLOW"
    assert benign.suggested_next_action == "none"
    assert benign.expected_case_id is None


def test_expected_case_ids() -> None:
    assert _by_id("command_injection").expected_case_id == "CASE-SEED-001"
    assert _by_id("authentication_incident").expected_case_id == "CASE-SEED-002"
    assert _by_id("sql_injection").expected_case_id == "CASE-SEED-003"
    assert _by_id("benign_input").expected_case_id is None


def test_find_demo_scenario_returns_scenario_by_id() -> None:
    scenario = find_demo_scenario("command_injection")

    assert scenario is not None
    assert scenario.scenario_id == "command_injection"
    assert scenario.expected_attack == "Command Injection"


def test_unknown_scenario_id_returns_none() -> None:
    assert find_demo_scenario("does-not-exist") is None
    assert find_demo_scenario("") is None


def test_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/demo_scenarios.py").read_text(encoding="utf-8")

    assert "streamlit" not in source.lower()
    assert "streamlit" not in sys.modules


def test_scenario_titles_are_language_aware() -> None:
    zh = scenario_titles("zh-TW")
    en = scenario_titles("en")
    bilingual = scenario_titles("bilingual")

    assert "命令注入示範" in zh
    assert "SQL 注入示範" in zh
    assert "Command Injection Demo" in en
    assert "Authentication Incident Demo" in en
    assert "命令注入示範 / Command Injection Demo" in bilingual
    # titles are never the raw i18n key (i.e. translation resolved for each mode)
    for titles in (zh, en, bilingual):
        assert all(not title.startswith("scenario_") for title in titles)


def test_scenario_data_is_immutable() -> None:
    scenario = list_demo_scenarios()[0]

    with pytest.raises(dataclasses.FrozenInstanceError):
        scenario.input_text = "mutated"  # type: ignore[misc]
