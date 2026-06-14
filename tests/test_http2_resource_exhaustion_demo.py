"""v2.8 Part A: the safe synthetic HTTP/2 Resource Exhaustion demo must classify
deterministically as HTTP/2 Resource Exhaustion Suspicion / MEDIUM / MONITOR.

These tests prove the documented demo card behavior is real (router + rule-based
detector + deterministic triage policy + fast deterministic path) and that the
synthetic marker does not false-positive on benign input. The scenario remains
defensive and synthetic: no traffic, no exploit, no PoC.
"""

from typing import Any

from modules.controller.case_capture import PENDING_CASE_DRAFT_KEY
from modules.controller.fast_analysis import run_fast_payload_analysis
from modules.controller.skill_catalog import ANALYZE_PAYLOAD_SKILL
from modules.detector import RuleBasedDetector
from modules.event_followup import ActiveEventContext
from modules.followup_handler import FollowupHandler
from modules.responder import Responder
from modules.smart_router import route_user_input
from modules.triage_policy import TriagePolicy
from modules.ui.demo_scenarios import find_demo_scenario

HTTP2_ATTACK_TYPE = "HTTP/2 Resource Exhaustion Suspicion"


def _scenario_input() -> str:
    scenario = find_demo_scenario("http2_resource_exhaustion")
    assert scenario is not None
    return scenario.input_text


class _FastAgent:
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


def test_router_routes_synthetic_http2_to_payload_triage() -> None:
    decision = route_user_input(_scenario_input())

    assert decision.route == "payload_triage"
    assert decision.input_kind == "payload_or_event"
    assert decision.requires_clarification is False


def test_detector_classifies_synthetic_http2_marker() -> None:
    result = RuleBasedDetector().inspect_text(_scenario_input())

    assert result["status"] == "ALERT"
    assert HTTP2_ATTACK_TYPE in result["attack_types"]
    assert "HTTP2-RES-001" in (result["metadata"].get("rule_ids") or [])


def test_triage_maps_http2_to_medium_monitor() -> None:
    detector_result = RuleBasedDetector().inspect_text(_scenario_input())
    triage = TriagePolicy()

    risk = triage.score_risk(detector_result)
    decision = triage.decide(risk)

    assert risk["risk_level"] == "MEDIUM"
    assert decision["decision"] == "MONITOR"


def test_fast_analysis_http2_produces_medium_monitor_event_context() -> None:
    result = run_fast_payload_analysis(_FastAgent(), _scenario_input())

    assert result.status == "ok"
    assert result.selected_tool == ANALYZE_PAYLOAD_SKILL
    assert result.risk_result["risk_level"] == "MEDIUM"
    assert result.decision_result["decision"] == "MONITOR"

    context = result.active_context
    assert isinstance(context, ActiveEventContext)
    assert HTTP2_ATTACK_TYPE in context.attack_types
    assert "HTTP2-RES-001" in context.rule_ids
    # Old active-context behavior remains safe: it is an event context, not an
    # incident, and the decision is a simulated MONITOR.
    assert result.detector_result["status"] == "ALERT"


def test_demo_card_pills_match_actual_deterministic_behavior() -> None:
    scenario = find_demo_scenario("http2_resource_exhaustion")
    assert scenario is not None
    detector_result = RuleBasedDetector().inspect_text(scenario.input_text)
    triage = TriagePolicy()
    risk = triage.score_risk(detector_result)
    decision = triage.decide(risk)

    assert scenario.expected_attack == HTTP2_ATTACK_TYPE
    assert scenario.expected_attack in detector_result["attack_types"]
    assert scenario.expected_risk == risk["risk_level"] == "MEDIUM"
    assert scenario.expected_decision == decision["decision"] == "MONITOR"


def test_synthetic_marker_does_not_false_positive_on_benign_input() -> None:
    detector = RuleBasedDetector()

    for benign in (
        "hello world",
        "GET /index.html",
        "What is HTTP/2 and resource exhaustion?",  # topic words but no marker
        "http/2 performance tuning notes",
    ):
        result = detector.inspect_text(benign)
        assert HTTP2_ATTACK_TYPE not in result["attack_types"]

    # The router does not route a bare HTTP/2 mention (no marker) to payload triage.
    assert route_user_input("http/2 performance tuning notes").route != "payload_triage"
