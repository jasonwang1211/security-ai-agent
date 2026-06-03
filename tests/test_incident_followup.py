from pathlib import Path

from modules.agent import SecurityAgent
from modules.detector import RuleBasedDetector
from modules.followup_handler import FollowupHandler
from modules.incident_followup import ActiveAuthIncidentContext, answer_incident_followup
from modules.mode_handlers import (
    get_agent_state,
    run_followup,
    run_knowledge_qa,
    run_log_ingestion,
    run_payload_analysis,
)
from modules.responder import Responder
from modules.triage_policy import TriagePolicy


SCENARIO_A_LOG = Path("demo_logs/scenario_a_mixed_auth.log")
NON_QUALIFYING_AUTH_LOG = Path("demo_logs/auth_bruteforce.log")
COMMAND_PAYLOAD = "test; rm -rf /tmp/test"


class DummyRAG:
    def is_ready(self):
        return True

    def answer_question(self, query):
        return f"knowledge answer: {query}"

    def retrieve_context(self, query):
        return "", False

    def is_security(self, query):
        return True

    def generate_answer(self, query, context):
        return f"generated: {query} / {context}"

    def explain_point(self, target):
        return f"point explanation: {target}"

    def handle_natural_followup(self, focus, query):
        return f"generic follow-up: {focus} / {query}"


class DummyLLMAssist:
    def explain_alert(self, query, detector_result, rag_context, risk_result, decision_result, state):
        return {
            "is_suspicious": True,
            "possible_attack_types": detector_result.get("attack_types", []),
            "reasoning": "Dummy alert explanation.",
            "recommended_decision": decision_result.get("decision", "MONITOR"),
            "confidence": 0.9,
        }

    def judge_suspicious_behavior(
        self,
        query,
        detector_result,
        rag_context="",
        signals=None,
        state=None,
    ):
        return None


def build_agent() -> SecurityAgent:
    return SecurityAgent(
        followup_handler=FollowupHandler(),
        detector=RuleBasedDetector(),
        rag_qa=DummyRAG(),
        responder=Responder(),
        triage_policy=TriagePolicy(),
        llm_assist=DummyLLMAssist(),
    )


def run_scenario_a_mode2(agent: SecurityAgent) -> ActiveAuthIncidentContext:
    output = run_log_ingestion(str(SCENARIO_A_LOG), agent=agent)
    state = get_agent_state(agent)

    assert "[Log Ingestion Summary]" in output
    assert state["active_context_kind"] == "incident"
    context = state["active_incident_context"]
    assert isinstance(context, ActiveAuthIncidentContext)
    return context


def test_mode2_auth_log_stores_active_incident_context() -> None:
    agent = build_agent()

    context = run_scenario_a_mode2(agent)

    assert context.source == "mode2_auth_sequence_correlation"
    assert context.incident.status == "SUSPICIOUS"
    assert context.incident.risk_level == "HIGH"
    assert context.incident.decision == "MONITOR"
    assert context.incident.attack_type == "Possible Account Compromise"
    assert context.incident.findings[0].id == "F-001"
    assert {"EV-001", "EV-002", "EV-003"}.issubset(
        context.incident.evidence_bundle.available_ids
    )
    assert context.graph_snapshot.nodes
    assert context.graph_snapshot.edges


def test_mode2_auth_log_returns_visible_structured_incident_summary() -> None:
    agent = build_agent()

    output = run_log_ingestion(str(SCENARIO_A_LOG), agent=agent)
    context = get_agent_state(agent)["active_incident_context"]

    assert isinstance(context, ActiveAuthIncidentContext)
    assert "Log ingestion and deterministic authentication-incident correlation completed." in output
    assert "Structured incident follow-up is available when an incident is detected." in output
    assert "Optional SecurityAgent analysis of aggregated events has not been run unless requested below." in output
    assert "Log ingestion only. Events are not sent into SecurityAgent yet." not in output
    assert "[Structured Authentication Incident]" in output
    assert f"Incident ID: {context.incident.id}" in output
    assert "Status: SUSPICIOUS" in output
    assert "Attack Type: Possible Account Compromise" in output
    assert "Risk Level: HIGH" in output
    assert "Decision: MONITOR" in output
    assert "simulated decision" in output
    assert "no real monitoring deployment" in output
    assert "EV-003" in output
    assert "F-001" in output
    assert "does not prove account takeover or intrusion by itself" in output
    assert "confirmed compromise" not in output.casefold()
    assert "EV-003" in output and "是什麼意思" in output
    assert "EV-003" in output and "F-001" in output and "有什麼關係" in output


def test_non_qualifying_mode2_log_does_not_emit_fabricated_incident_summary() -> None:
    agent = build_agent()

    output = run_log_ingestion(str(NON_QUALIFYING_AUTH_LOG), agent=agent)
    state = get_agent_state(agent)

    assert "[Log Ingestion Summary]" in output
    assert "Log ingestion and deterministic authentication-incident correlation completed." in output
    assert "Structured incident follow-up is available when an incident is detected." in output
    assert "Log ingestion only. Events are not sent into SecurityAgent yet." not in output
    assert "[Structured Authentication Incident]" not in output
    assert state["active_incident_context"] is None
    assert state["active_event_context"] is None
    assert state["active_context_kind"] == ""


def test_non_qualifying_mode2_log_clears_stale_structured_context() -> None:
    agent = build_agent()
    run_scenario_a_mode2(agent)
    assert get_agent_state(agent)["active_context_kind"] == "incident"

    output = run_log_ingestion(str(NON_QUALIFYING_AUTH_LOG), agent=agent)
    state = get_agent_state(agent)
    answer = run_followup(agent, "EV-003 是什麼意思？")

    assert "Log ingestion only. Events are not sent into SecurityAgent yet." not in output
    assert "[Structured Authentication Incident]" not in output
    assert state["active_incident_context"] is None
    assert state["active_event_context"] is None
    assert state["active_context_kind"] == ""
    assert "success_after_failures" not in answer
    assert "F-001" not in answer
    assert "explicitly supports" not in answer


def test_mode4_ev_id_followup_uses_actual_incident_and_graph_facts() -> None:
    agent = build_agent()
    run_scenario_a_mode2(agent)

    answer = run_followup(agent, "EV-003 是什麼意思？")

    assert "EV-003" in answer
    assert "success_after_failures" in answer
    assert "A successful authentication followed repeated failures." in answer
    assert "F-001" in answer
    assert "explicitly supports" in answer
    assert "not Graph RAG" in answer
    assert "knowledge answer" not in answer


def test_mode4_ev_and_finding_relationship_uses_graph_snapshot() -> None:
    agent = build_agent()
    run_scenario_a_mode2(agent)

    answer = run_followup(agent, "EV-003 和 F-001 有什麼關係？")

    assert "F-001 is explicitly supported by EV-003" in answer
    assert "Graph fact:" in answer
    assert "Only explicit GraphSnapshot edges" in answer
    assert "no relationship was inferred from free text" in answer


def test_mode4_monitor_followup_keeps_simulated_boundary() -> None:
    agent = build_agent()
    run_scenario_a_mode2(agent)

    answer = run_followup(agent, "為什麼是 MONITOR？")

    assert "Risk Level 為 HIGH" in answer
    assert "Decision 為 MONITOR" in answer
    assert "possible_account_compromise candidate" in answer
    assert "模擬決策" in answer
    assert "不代表已執行真實封鎖" in answer
    assert "does not change the deterministic Risk Level or Decision" in answer


def test_mode4_compromise_uncertainty_does_not_claim_confirmed_intrusion() -> None:
    agent = build_agent()
    run_scenario_a_mode2(agent)

    answer = run_followup(agent, "這代表帳號已經被入侵了嗎？")

    assert "不能只靠這份 evidence 宣稱帳號已確認被入侵" in answer
    assert "suspicious sequence" in answer
    assert "not confirmed compromise" in answer
    assert "successful login session" in answer
    assert "MFA" in answer


def test_mode4_investigation_guidance_uses_incident_response_without_action_claim() -> None:
    agent = build_agent()
    run_scenario_a_mode2(agent)

    answer = run_followup(agent, "我現在應該先做哪些調查與修補？")

    assert "Review the successful login session after repeated failures." in answer
    assert "Check whether the same source attempted other users." in answer
    assert "session revocation or password reset after analyst review" in answer
    assert "系統沒有宣稱已執行任何處置" in answer


def test_mode3_knowledge_qa_does_not_overwrite_active_incident_context() -> None:
    agent = build_agent()
    original_context = run_scenario_a_mode2(agent)

    answer = run_knowledge_qa(agent, "什麼是 brute force？")
    state = get_agent_state(agent)

    assert "knowledge answer" in answer
    assert state["active_context_kind"] == "incident"
    assert state["active_incident_context"] is original_context


def test_mode2_incident_context_replaces_older_mode1_event_context_for_followup() -> None:
    agent = build_agent()
    run_payload_analysis(agent, COMMAND_PAYLOAD)
    state = get_agent_state(agent)
    assert state["active_context_kind"] == "event"

    run_scenario_a_mode2(agent)
    answer = run_followup(agent, "為什麼是 MONITOR？")

    assert "Possible Account Compromise" in answer or "possible_account_compromise" in answer
    assert "Command Injection" not in answer
    assert "Decision 為 MONITOR" in answer


def test_mode1_event_context_replaces_older_mode2_incident_context_for_followup() -> None:
    agent = build_agent()
    run_scenario_a_mode2(agent)

    run_payload_analysis(agent, COMMAND_PAYLOAD)
    state = get_agent_state(agent)
    assert state["active_context_kind"] == "event"

    answer = run_followup(agent, "EV-003 是什麼意思？")

    assert "success_after_failures" not in answer
    assert "F-001" not in answer
    assert "explicitly supports" not in answer


def test_incident_followup_returns_none_for_unrelated_question() -> None:
    agent = build_agent()
    context = run_scenario_a_mode2(agent)

    assert answer_incident_followup("random unrelated chat", context) is None
