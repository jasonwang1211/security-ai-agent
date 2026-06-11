import dataclasses
import sys
from pathlib import Path

import pytest

from modules.ui.demo_scenarios import (
    DemoScenario,
    find_demo_scenario,
    list_demo_scenarios,
    scenario_preview_text,
    scenario_titles,
)


def _by_id(scenario_id: str) -> DemoScenario:
    scenario = find_demo_scenario(scenario_id)
    assert scenario is not None
    return scenario


def test_list_demo_scenarios_returns_required_scenarios() -> None:
    scenarios = list_demo_scenarios()

    assert len(scenarios) == 4
    assert {scenario.scenario_id for scenario in scenarios} == {
        "command_injection",
        "sql_injection",
        "authentication_incident",
        "http2_resource_exhaustion",
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


def test_benign_scenario_is_not_listed() -> None:
    # The benign / no-attack demo was removed from the launcher; users can still
    # type "hello world" manually. It must not reappear as a scenario.
    assert find_demo_scenario("benign_input") is None
    assert "benign_input" not in {s.scenario_id for s in list_demo_scenarios()}


def test_expected_case_ids() -> None:
    assert _by_id("command_injection").expected_case_id == "CASE-SEED-001"
    assert _by_id("authentication_incident").expected_case_id == "CASE-SEED-002"
    assert _by_id("sql_injection").expected_case_id == "CASE-SEED-003"


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


def test_http2_resource_exhaustion_scenario_is_safe_synthetic_demo() -> None:
    scenario = _by_id("http2_resource_exhaustion")
    text = scenario.input_text.casefold()

    assert "synthetic incident summary" in text
    assert "http/2" in text
    assert "resource exhaustion" in text
    assert "low inbound request volume" in text
    assert "worker saturation" in text
    assert "concurrent stream" in text
    assert "memory pressure" in text
    assert scenario.expected_attack == "HTTP/2 Resource Exhaustion Suspicion"
    assert scenario.expected_risk == "MEDIUM"
    assert scenario.expected_decision == "MONITOR"
    assert scenario.suggested_next_action == "none"
    assert scenario.expected_case_id is None


def test_http2_resource_exhaustion_scenario_has_safety_notes() -> None:
    text = _by_id("http2_resource_exhaustion").input_text.casefold()

    assert "synthetic demo only" in text
    assert "no traffic generated" in text
    assert "no real enforcement" in text
    assert "cve context is not proof" in text
    assert "human review required" in text


def test_http2_resource_exhaustion_preview_is_shorter_than_full_input() -> None:
    scenario = _by_id("http2_resource_exhaustion")
    preview = scenario_preview_text(scenario, "en")

    assert len(preview) < len(scenario.input_text)
    assert "synthetic http/2 resource exhaustion suspicion" in preview.casefold()
    assert "no traffic generated" in preview.casefold()
    assert "no real enforcement" in preview.casefold()
    assert "human review required" in preview.casefold()
    assert "[synthetic incident summary]" not in preview.casefold()
    assert "event_type=http2_resource_exhaustion_suspicion" not in preview.casefold()


def test_http2_resource_exhaustion_preview_is_language_aware() -> None:
    scenario = _by_id("http2_resource_exhaustion")

    zh = scenario_preview_text(scenario, "zh-TW")
    en = scenario_preview_text(scenario, "en")
    bilingual = scenario_preview_text(scenario, "bilingual")

    assert "合成 HTTP/2 資源耗盡疑似事件" in zh
    assert "Synthetic HTTP/2 resource exhaustion suspicion" in en
    assert "合成 HTTP/2 資源耗盡疑似事件" in bilingual
    assert "synthetic HTTP/2 resource exhaustion suspicion" in bilingual


def test_non_http2_scenarios_keep_input_as_preview() -> None:
    scenario = _by_id("command_injection")

    assert scenario_preview_text(scenario, "en") == scenario.input_text


def test_streamlit_launcher_loads_full_input_text_not_preview() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "scenario_preview_text(scenario, language)" in source
    assert "st.session_state[TEXT_AREA_KEY] = scenario.input_text" in source
    assert "st.session_state[TEXT_AREA_KEY] = preview_text" not in source


def test_http2_resource_exhaustion_scenario_avoids_offensive_preview_language() -> None:
    text = _by_id("http2_resource_exhaustion").input_text.casefold()

    forbidden_phrases = (
        "exploit",
        "poc",
        "attack a real server",
        "send traffic",
        "flood",
        "amplify",
        "requests per second",
        "rps",
    )
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_http2_resource_exhaustion_titles_are_language_aware() -> None:
    zh_title = "HTTP/2 資源耗盡疑似事件"
    zh = scenario_titles("zh-TW")
    en = scenario_titles("en")
    bilingual = scenario_titles("bilingual")

    assert zh_title in zh
    assert "HTTP/2 Resource Exhaustion Suspicion" in en
    bilingual_title = f"{zh_title} / HTTP/2 Resource Exhaustion Suspicion"
    assert bilingual_title in bilingual


def test_http2_preview_is_structured_summary_rows() -> None:
    scenario = _by_id("http2_resource_exhaustion")

    en = scenario_preview_text(scenario, "en")
    en_lines = [line for line in en.splitlines() if line.strip()]
    assert len(en_lines) >= 4  # readable rows, not one long code/log line
    assert "Summary:" in en
    assert "Signals:" in en
    assert "Telemetry:" in en
    assert "Boundary:" in en

    zh = scenario_preview_text(scenario, "zh-TW")
    zh_lines = [line for line in zh.splitlines() if line.strip()]
    assert len(zh_lines) >= 4
    assert "摘要：" in zh
    assert "邊界：" in zh
    # The structured preview must not embed the raw synthetic incident block.
    assert "event_type=http2_resource_exhaustion_suspicion" not in zh
    assert "[synthetic incident summary]" not in zh


def test_streamlit_launcher_renders_structured_preview_as_rows_not_code() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    # Structured (preview_key) scenarios render as readable rows; only short
    # one-line payload previews fall back to a <code> block.
    assert "scenario.preview_key" in source
    assert "sentinel-demo-preview-row" in source
    assert 'preview_block = f\'<code class="sentinel-code">{html.escape(preview_text)}</code>\'' in source


def test_streamlit_launcher_clears_stale_active_context_before_loading_input() -> None:
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    # Within the Load Scenario handler, the stale active context (and its run
    # mode) is cleared before the new pending input is written to the textarea,
    # so a loaded scenario is not displayed next to the previous run's context.
    idx_button = source.index('key=f"load_scenario_{scenario.scenario_id}"')
    idx_clear = source.index("clear_active_context(st.session_state)", idx_button)
    idx_run_mode = source.index("st.session_state.pop(STATE_ANALYSIS_RUN_MODE, None)", idx_button)
    idx_textarea = source.index(
        "st.session_state[TEXT_AREA_KEY] = scenario.input_text", idx_button
    )

    assert idx_button < idx_clear < idx_textarea
    assert idx_button < idx_run_mode < idx_textarea
    # The load handler must not trigger analysis.
    load_block = source[idx_button:idx_textarea]
    assert "run_direct_input(" not in load_block
