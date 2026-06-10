from typing import Any

from modules.controller.case_capture import PENDING_CASE_DRAFT_KEY
from modules.controller.fast_analysis import run_fast_payload_analysis
from modules.controller.skill_wrappers import (
    run_draft_case_capture_skill,
    run_retrieve_approved_similar_case_skill,
)
from modules.controller.types import CaseDraftInput, SimilarCaseInput
from modules.detector import RuleBasedDetector
from modules.event_followup import ActiveEventContext
from modules.followup_handler import FollowupHandler
from modules.responder import Responder
from modules.triage_policy import TriagePolicy

COMMAND_PAYLOAD = "test; rm -rf /tmp/test"


class FastModeAgent:
    def __init__(self) -> None:
        self.detector = RuleBasedDetector()
        self.triage_policy = TriagePolicy()
        self.responder = Responder()
        self.followup_handler = FollowupHandler()
        self.cli_state: dict[str, Any] = {
            "last_question": "",
            "last_answer": "",
            "last_points": [],
            "last_focus": "",
            "active_event_context": None,
            "active_incident_context": None,
            "active_context_kind": "",
            PENDING_CASE_DRAFT_KEY: None,
        }


def test_fast_payload_analysis_skips_ai_and_rag_note_in_output() -> None:
    result = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD)

    assert result.status == "ok"
    assert "Fast Deterministic Mode" in result.response_text
    assert "LLM Assist and expensive RAG explanation were skipped." in result.response_text
    assert "LLM Assist is not used in fast mode." in result.response_text


def test_fast_command_injection_payload_produces_deterministic_facts() -> None:
    result = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD)

    context = result.active_context
    assert isinstance(context, ActiveEventContext)
    assert context.attack_types == ("Command Injection",)
    assert context.rule_ids == ("CMD-001",)
    assert context.risk_level == "HIGH"
    assert context.decision == "BLOCK"
    assert "; rm" in context.matched_signatures["Command Injection"]
    assert "; rm -rf" in context.matched_signatures["Command Injection"]
    assert "Command Injection" in result.response_text
    assert "CMD-001" in result.response_text
    assert "HIGH" in result.response_text
    assert "BLOCK" in result.response_text


def test_fast_payload_analysis_output_contains_boundary() -> None:
    result = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD)

    assert "[Security Triage Report]" in result.response_text
    assert "Fast Deterministic Mode" in result.response_text
    assert "BLOCK / MONITOR / ALLOW are simulated project decisions." in result.response_text
    assert "No real firewall" in result.response_text
    assert "Skipped in Fast Deterministic Mode." in result.response_text


def test_fast_payload_analysis_preserves_active_event_context() -> None:
    agent = FastModeAgent()

    result = run_fast_payload_analysis(agent, COMMAND_PAYLOAD)

    assert agent.cli_state["active_context_kind"] == "event"
    assert agent.cli_state["active_event_context"] is result.active_context
    assert agent.cli_state["last_question"] == COMMAND_PAYLOAD
    assert agent.cli_state["last_answer"] == result.active_context.rendered_report


def test_fast_payload_analysis_supports_similar_case_retrieval() -> None:
    agent = FastModeAgent()
    run_fast_payload_analysis(agent, COMMAND_PAYLOAD)

    similar = run_retrieve_approved_similar_case_skill(
        SimilarCaseInput(command="find similar cases"),
        agent,
    )

    assert similar.status == "ok"
    assert similar.output["matches"][0]["case_id"] == "CASE-SEED-001"
    assert "CASE-SEED-001" in similar.output["text"]


def test_fast_payload_analysis_supports_case_draft_pending_request() -> None:
    agent = FastModeAgent()
    run_fast_payload_analysis(agent, COMMAND_PAYLOAD)

    draft = run_draft_case_capture_skill(
        CaseDraftInput(action="request", user_text="save this case as a draft"),
        agent,
    )

    assert draft.status == "clarification_required"
    assert "Explicit approval is required" in draft.output["text"]
    assert agent.cli_state[PENDING_CASE_DRAFT_KEY] is not None


def test_fast_analysis_helper_has_no_rag_or_llm_runtime_imports() -> None:
    source = "modules/controller/fast_analysis.py"
    text = __import__("pathlib").Path(source).read_text(encoding="utf-8")

    assert "modules.rag" not in text
    assert "modules.rag_qa" not in text
    assert "llm_assist" not in text


# --- v2.6-P language-aware Fast deterministic report ------------------------


def test_english_fast_report_matches_existing_behavior() -> None:
    report = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD, language="en").response_text

    assert "[Security Triage Report]" in report
    assert "Fast Deterministic Mode" in report
    assert "Risk Level: HIGH" in report
    assert "Decision: BLOCK" in report
    assert "Attack Type: Command Injection" in report
    assert "CMD-001" in report


def test_zh_tw_fast_report_uses_chinese_labels_and_keeps_dynamic_values() -> None:
    report = run_fast_payload_analysis(
        FastModeAgent(), COMMAND_PAYLOAD, language="zh-TW"
    ).response_text

    assert "[資安分流報告]" in report
    assert "快速確定性模式" in report
    assert "風險等級：HIGH" in report
    assert "決策：BLOCK" in report
    assert "攻擊類型：Command Injection" in report
    # dynamic values are not translated.
    assert "CMD-001" in report
    assert "HIGH" in report
    assert "BLOCK" in report
    # english report title bracket should not appear in zh-TW mode.
    assert "[Security Triage Report]" not in report


def test_bilingual_fast_report_uses_compact_bilingual_labels() -> None:
    report = run_fast_payload_analysis(
        FastModeAgent(), COMMAND_PAYLOAD, language="bilingual"
    ).response_text

    assert "[資安分流報告 / Security Triage Report]" in report
    assert "模式 / Mode" in report
    assert "風險等級 / Risk Level" in report
    assert "決策 / Decision" in report
    # dynamic values remain unchanged.
    assert "Command Injection" in report
    assert "HIGH" in report
    assert "BLOCK" in report
    assert "CMD-001" in report


def test_unsupported_language_falls_back_to_english() -> None:
    fallback = run_fast_payload_analysis(
        FastModeAgent(), COMMAND_PAYLOAD, language="fr"
    ).response_text
    english = run_fast_payload_analysis(
        FastModeAgent(), COMMAND_PAYLOAD, language="en"
    ).response_text

    assert fallback == english
    assert "[Security Triage Report]" in fallback


def test_default_language_preserves_english_report() -> None:
    default = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD).response_text
    english = run_fast_payload_analysis(
        FastModeAgent(), COMMAND_PAYLOAD, language="en"
    ).response_text

    assert default == english


def test_active_context_unchanged_across_languages() -> None:
    english = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD, language="en")
    chinese = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD, language="zh-TW")

    for context in (english.active_context, chinese.active_context):
        assert context.attack_types == ("Command Injection",)
        assert context.rule_ids == ("CMD-001",)
        assert context.risk_level == "HIGH"
        assert context.decision == "BLOCK"


def test_zh_tw_similar_case_lookup_still_works_after_fast_analysis() -> None:
    agent = FastModeAgent()
    run_fast_payload_analysis(agent, COMMAND_PAYLOAD, language="zh-TW")

    similar = run_retrieve_approved_similar_case_skill(
        SimilarCaseInput(command="find similar cases"),
        agent,
    )

    assert similar.status == "ok"
    assert similar.output["matches"][0]["case_id"] == "CASE-SEED-001"


def test_report_language_helper_has_no_streamlit_import() -> None:
    text = __import__("pathlib").Path(
        "modules/controller/report_language.py"
    ).read_text(encoding="utf-8")

    assert "streamlit" not in text.lower()


# --- v2.6-S correction: language-aware simulated decision note --------------

_ZH_SIMULATED_DECISION_NOTE = "已模擬封鎖這次可疑請求，未實際修改任何系統或防火牆設定。"
_EN_SIMULATED_DECISION_NOTE = (
    "Simulated BLOCK for this suspicious request; no system or firewall "
    "configuration was actually changed."
)


def test_english_fast_report_has_no_chinese_simulated_decision_note() -> None:
    report = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD, language="en").response_text

    assert _ZH_SIMULATED_DECISION_NOTE not in report


def test_english_fast_report_contains_english_simulated_decision_note() -> None:
    report = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD, language="en").response_text

    assert f"Simulated Decision Note: {_EN_SIMULATED_DECISION_NOTE}" in report
    # the dynamic decision token is preserved.
    assert "Simulated BLOCK" in report


def test_zh_tw_fast_report_keeps_chinese_simulated_decision_note() -> None:
    report = run_fast_payload_analysis(
        FastModeAgent(), COMMAND_PAYLOAD, language="zh-TW"
    ).response_text

    assert f"模擬決策說明：{_ZH_SIMULATED_DECISION_NOTE}" in report
    assert _EN_SIMULATED_DECISION_NOTE not in report


def test_bilingual_fast_report_contains_both_simulated_decision_notes() -> None:
    report = run_fast_payload_analysis(
        FastModeAgent(), COMMAND_PAYLOAD, language="bilingual"
    ).response_text

    expected = (
        f"模擬決策說明 / Simulated Decision Note：{_ZH_SIMULATED_DECISION_NOTE} / "
        f"{_EN_SIMULATED_DECISION_NOTE}"
    )
    assert expected in report


def test_simulated_decision_note_fix_keeps_active_context_decision_unchanged() -> None:
    english = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD, language="en")
    chinese = run_fast_payload_analysis(FastModeAgent(), COMMAND_PAYLOAD, language="zh-TW")

    for result in (english, chinese):
        assert result.active_context.risk_level == "HIGH"
        assert result.active_context.decision == "BLOCK"
        # the canonical defense summary (stored/decision side) is unchanged.
        assert result.active_context.attack_types == ("Command Injection",)


def test_similar_case_retrieval_still_works_after_english_fast_analysis() -> None:
    agent = FastModeAgent()
    run_fast_payload_analysis(agent, COMMAND_PAYLOAD, language="en")

    similar = run_retrieve_approved_similar_case_skill(
        SimilarCaseInput(command="find similar cases"),
        agent,
    )

    assert similar.status == "ok"
    assert similar.output["matches"][0]["case_id"] == "CASE-SEED-001"

