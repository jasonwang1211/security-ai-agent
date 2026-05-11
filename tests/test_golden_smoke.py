from pathlib import Path

from modules.agent import SecurityAgent
from modules.detector import RuleBasedDetector
from modules.followup_handler import FollowupHandler
from modules.mode_handlers import run_log_agent_analysis, run_log_ingestion, run_payload_analysis
from modules.responder import Responder
from modules.triage_policy import TriagePolicy


AUTH_BRUTEFORCE_LOG = str(Path("demo_logs") / "auth_bruteforce.log")


class DummyRAG:
    def is_ready(self):
        return False

    def retrieve_context(self, query):
        return "", False

    def is_security(self, query):
        return True

    def generate_answer(self, query, context):
        return ""

    def explain_point(self, target):
        return ""

    def handle_natural_followup(self, focus, query):
        return ""


class DummyLLMAssist:
    def explain_alert(self, query, detector_result, rag_context, risk_result, decision_result, state):
        return {
            "is_suspicious": True,
            "possible_attack_types": detector_result.get("attack_types", []),
            "reasoning": "Dummy AI assist for golden smoke test.",
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
        return {
            "is_suspicious": True,
            "suggested_attack_types": ["Brute Force", "Credential Stuffing"],
            "confidence": 0.9,
            "anomaly_score": 0.8,
            "reasoning": "Dummy suspicious behavior judgment for golden smoke test.",
            "recommended_risk": "MEDIUM",
            "recommended_action": "MONITOR",
            "llm_status": "DUMMY",
        }


def build_test_agent():
    return SecurityAgent(
        followup_handler=FollowupHandler(),
        detector=RuleBasedDetector(),
        rag_qa=DummyRAG(),
        responder=Responder(),
        triage_policy=TriagePolicy(),
        llm_assist=DummyLLMAssist(),
    )


def test_mode1_xss_payload_triage():
    agent = build_test_agent()

    output = run_payload_analysis(agent, "<script>alert(1)</script>")

    assert "[Security Triage Report]" in output
    assert "Status: ALERT" in output
    assert "Attack Type: XSS" in output
    assert "Risk Level: MEDIUM" in output
    assert "Decision: MONITOR" in output
    assert "Detection Source: rule_based_detector (rule_based)" in output
    assert "6. AI Assist" in output


def test_mode1_sql_injection_payload_regression():
    agent = build_test_agent()

    output = run_payload_analysis(agent, "?id=1' OR '1'='1")

    assert isinstance(output, str)
    assert "[Security Triage Report]" in output
    assert "Status: ALERT" in output
    assert "Attack Type: SQL Injection" in output
    assert "Detection Source: rule_based_detector (rule_based)" in output


def test_mode1_path_traversal_payload_regression():
    agent = build_test_agent()

    output = run_payload_analysis(agent, "../../etc/passwd")

    assert isinstance(output, str)
    assert "[Security Triage Report]" in output
    assert "Status: ALERT" in output
    assert "Attack Type: Path Traversal" in output
    assert "Detection Source: rule_based_detector (rule_based)" in output


def test_mode1_command_injection_payload_regression():
    agent = build_test_agent()

    output = run_payload_analysis(agent, "test; rm -rf /tmp/test")

    assert "[Security Triage Report]" in output
    assert "Status: ALERT" in output
    assert "Attack Type: Command Injection" in output
    assert "Risk Level: HIGH" in output
    assert "Decision: BLOCK" in output
    assert "Detection Source: rule_based_detector (rule_based)" in output


def test_mode1_benign_input_does_not_trigger_known_payload_alerts():
    agent = build_test_agent()

    output = run_payload_analysis(agent, "hello world")

    assert isinstance(output, str)
    assert "Status: ALERT" not in output
    assert "Attack Type: SQL Injection" not in output
    assert "Attack Type: XSS" not in output
    assert "Attack Type: Path Traversal" not in output


def test_mode1_malformed_raw_log_does_not_translate_as_auth_failure():
    agent = build_test_agent()

    output = run_payload_analysis(agent, "this is not a valid auth log")

    assert isinstance(output, str)
    assert "[Input Translation]" not in output
    assert "Normalized Event Type: auth_failure" not in output


def test_mode1_empty_input_does_not_crash():
    agent = build_test_agent()

    output = run_payload_analysis(agent, "")

    assert isinstance(output, str)


def test_mode1_raw_auth_log_triage():
    agent = build_test_agent()
    raw_log = "2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401"

    output = run_payload_analysis(agent, raw_log)

    assert "[Input Translation]" in output
    assert "Detected Input Type: raw_log" in output
    assert "Normalized Event Type: auth_failure" in output
    assert "[Security Triage Report]" in output
    assert "Status: REVIEW" in output
    assert "Attack Type: Authentication Failure" in output
    assert "Risk Level: LOW" in output
    assert "Decision: MONITOR" in output
    assert "Detection Source: raw_log_translation" in output
    assert "Single auth_failure event should be reviewed" in output


def test_mode2_auth_bruteforce_ingestion_summary():
    output = run_log_ingestion(AUTH_BRUTEFORCE_LOG)

    assert "Log Ingestion Summary" in output
    assert "Total Lines: 10" in output
    assert "Parsed Logs: 10" in output
    assert "Normalized Events: 10" in output
    assert "Aggregated Events: 1" in output
    assert "auth_failure" in output
    assert "brute_force_candidate" in output
    assert "Failed Count: 10" in output


def test_mode2_auth_bruteforce_agent_analysis():
    agent = build_test_agent()

    output = run_log_agent_analysis(agent, AUTH_BRUTEFORCE_LOG, scope="first")

    assert "[Security Triage Report]" in output
    assert "Status: SUSPICIOUS" in output
    assert "Brute Force" in output
    assert "Credential Stuffing" in output
    assert "Decision: MONITOR" in output
    assert "Detection Source: llm_assist + signal_extraction" in output
    assert "6. AI Assist" in output
