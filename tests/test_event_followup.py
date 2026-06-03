from modules.agent import SecurityAgent
from modules.detector import RuleBasedDetector
from modules.event_followup import ActiveEventContext
from modules.followup_handler import FollowupHandler
from modules.responder import Responder
from modules.triage_policy import TriagePolicy


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


def build_command_event_state() -> tuple[SecurityAgent, dict]:
    agent = build_agent()
    state: dict = {}
    report = agent.handle_query(COMMAND_PAYLOAD, state)

    assert "[Security Triage Report]" in report
    return agent, state


def test_mode1_command_analysis_creates_and_replaces_active_event_context() -> None:
    agent = build_agent()
    state: dict = {}

    agent.handle_query("<script>alert(1)</script>", state)
    first_context = state["active_event_context"]
    assert isinstance(first_context, ActiveEventContext)
    assert first_context.attack_types == ("XSS",)

    agent.handle_query(COMMAND_PAYLOAD, state)
    second_context = state["active_event_context"]
    assert isinstance(second_context, ActiveEventContext)
    assert second_context is not first_context
    assert second_context.attack_types == ("Command Injection",)
    assert second_context.rule_ids == ("CMD-001",)
    assert second_context.risk_level == "HIGH"
    assert second_context.decision == "BLOCK"


def test_mode3_knowledge_qa_does_not_overwrite_active_event_context() -> None:
    agent, state = build_command_event_state()
    original_context = state["active_event_context"]

    answer = agent.handle_knowledge_query("SQL Injection 是什麼？", state)

    assert "knowledge answer" in answer
    assert state["active_event_context"] is original_context


def test_mode4_uses_generic_fallback_when_no_active_event_context_exists() -> None:
    agent = build_agent()
    state = {
        "last_question": "previous",
        "last_answer": "previous report text",
        "last_points": [],
        "last_focus": "previous report focus",
    }

    answer = agent.handle_query("為什麼", state)

    assert answer.startswith("generic follow-up:")


def test_command_classification_followup_uses_current_event_facts() -> None:
    agent, state = build_command_event_state()

    answer = agent.handle_query("為什麼這筆事件被判定為 Command Injection？", state)

    assert "Mode 1 deterministic detector" in answer
    assert "Command Injection" in answer
    assert "CMD-001" in answer
    assert "; rm" in answer
    assert "Risk Level 為 HIGH" in answer
    assert "Decision 為 BLOCK" in answer
    assert "模擬決策" in answer
    assert "不代表已執行真實封鎖" in answer


def test_command_rule_and_evidence_followup_uses_retained_matches() -> None:
    agent, state = build_command_event_state()

    answer = agent.handle_query("命中了哪條規則？有什麼證據？", state)

    assert "CMD-001" in answer
    assert "Command Injection" in answer
    assert "; rm" in answer
    assert COMMAND_PAYLOAD in answer


def test_block_followup_states_simulated_decision_only() -> None:
    agent, state = build_command_event_state()

    answer = agent.handle_query("BLOCK 是真的已經封鎖了嗎？", state)

    assert "模擬決策" in answer
    assert "不代表已執行真實封鎖" in answer
    assert "防火牆/WAF/EDR" in answer
    assert "已模擬封鎖這次可疑請求" in answer


def test_command_execution_success_followup_does_not_claim_execution() -> None:
    agent, state = build_command_event_state()

    answer = agent.handle_query("這代表命令已經成功執行了嗎？", state)

    assert "不代表" in answer
    assert "不能證明命令已成功執行" in answer
    assert "系統已遭入侵" in answer
    assert "process/audit logs" in answer
    assert "outbound connections" in answer


def test_command_investigation_followup_gives_safe_next_checks() -> None:
    agent, state = build_command_event_state()

    answer = agent.handle_query("我現在應該先做哪些調查與修補？", state)

    assert "人工複核" in answer
    assert "command execution sinks" in answer
    assert "allowlist" in answer
    assert "不要把模擬決策視為已執行的處置" in answer


def test_xss_event_followup_is_not_hard_coded_to_command_injection() -> None:
    agent = build_agent()
    state: dict = {}
    agent.handle_query("<script>alert(1)</script>", state)

    answer = agent.handle_query("為什麼這筆事件被判定為 XSS？", state)

    assert "XSS" in answer
    assert "<script>" in answer or "alert(" in answer
    assert "Command Injection" not in answer


def test_event_followup_boundaries_do_not_fabricate_ids_or_real_enforcement() -> None:
    agent, state = build_command_event_state()
    questions = [
        "為什麼這筆事件被判定為 Command Injection？",
        "命中了哪條規則？有什麼證據？",
        "BLOCK 是真的已經封鎖了嗎？",
        "這代表命令已經成功執行了嗎？",
        "我現在應該先做哪些調查與修補？",
    ]

    answers = "\n".join(agent.handle_query(question, state) for question in questions)
    lowered = answers.casefold()

    assert "EV-" not in answers
    assert "F-" not in answers
    assert "INC-" not in answers
    assert "confirmed compromise" not in lowered
    assert "firewall blocked" not in lowered
    assert "real monitoring deployment" not in lowered


def test_mode1_detector_risk_and_decision_outputs_remain_unchanged() -> None:
    agent = build_agent()
    state: dict = {}

    report = agent.handle_query(COMMAND_PAYLOAD, state)

    assert "Status: ALERT" in report
    assert "Attack Type: Command Injection" in report
    assert "Risk Level: HIGH" in report
    assert "Decision: BLOCK" in report
