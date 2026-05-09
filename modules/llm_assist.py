from modules.llm_analyzer import LLMSecurityAnalyzer
from modules.llm_threat_judge import LLMThreatJudge


class LLMAssist:
    def __init__(self, threat_judge=None, security_analyzer=None):
        self.threat_judge = threat_judge or LLMThreatJudge()
        self.security_analyzer = security_analyzer or LLMSecurityAnalyzer()

    def judge_suspicious_behavior(
        self,
        query,
        detector_result,
        rag_context="",
        signals=None,
        state=None,
    ):
        return self.threat_judge.judge(
            query,
            detector_result,
            rag_context=rag_context,
            signals=signals,
            state=state,
        )

    def explain_alert(
        self,
        query,
        detector_result,
        rag_context,
        risk_result,
        decision_result,
        state,
    ):
        return self.security_analyzer.analyze(
            query,
            detector_result,
            rag_context,
            risk_result,
            decision_result,
            state,
        )
