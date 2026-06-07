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

