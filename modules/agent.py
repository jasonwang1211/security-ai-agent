import re

from modules.event_followup import answer_event_followup, build_active_event_context
from modules.incident_followup import answer_incident_followup


def extract_signals(query):
    normalized = (query or "").lower()

    encoding_candidates = ["%3c", "%3e", "%27", "%22", "%2f", "%5c", "%3d", "%28", "%29"]
    suspicious_keywords = [
        "union select",
        "alert",
        "../",
        "..\\",
        "drop table",
        "script",
        "onerror",
        "or '1'='1",
    ]
    repetition_candidates = ["same ip", "same source", "repeated", "multiple", "many attempts"]
    anomaly_candidates = [
        "login failed",
        "failed login",
        "failed logins",
        "error spike",
        "abnormal",
        "anomaly",
        "unusual",
        "brute force",
    ]

    keywords = []
    patterns = []
    anomaly_signals = []

    for pattern in encoding_candidates:
        if pattern in normalized:
            patterns.append(pattern)

    for keyword in suspicious_keywords:
        if keyword in normalized:
            keywords.append(keyword)

    for phrase in repetition_candidates:
        if phrase in normalized:
            anomaly_signals.append(phrase)

    for match in re.findall(r"\b\d+\s+times\b", normalized):
        anomaly_signals.append(match)

    for indicator in anomaly_candidates:
        if indicator in normalized:
            anomaly_signals.append(indicator)

    return {
        "keywords": list(dict.fromkeys(keywords)),
        "patterns": list(dict.fromkeys(patterns)),
        "anomaly_signals": list(dict.fromkeys(anomaly_signals)),
    }


def is_security_knowledge_question(query: str) -> bool:
    normalized = (query or "").lower()
    if not normalized:
        return False

    security_topics = [
        "xss",
        "sql injection",
        "zero-day",
        "zero day",
        "anomaly detection",
        "anomaly",
        "csrf",
        "command injection",
        "path traversal",
    ]
    question_markers = [
        "什麼是",
        "是什麼",
        "怎麼",
        "如何",
        "為什麼",
        "偵測邏輯",
        "說明",
        "解釋",
        "what is",
        "explain",
        "how to",
        "why",
    ]

    has_security_topic = any(topic in normalized for topic in security_topics)
    has_question_marker = any(marker in normalized for marker in question_markers)
    return has_security_topic and has_question_marker


class SecurityAgent:
    NON_SECURITY_MESSAGE = "請提出資安相關問題，或直接貼上可疑 payload 讓我協助判斷。"
    KB_UNAVAILABLE_MESSAGE = "知識庫目前不可用，請先執行 ingest_knowledge.py 建立 Chroma DB。"
    NO_CONTEXT_MESSAGE = "目前找不到足夠的知識內容來回答這個問題。"
    NO_POINT_MESSAGE = "目前沒有可供延伸說明的條列重點。"
    INVALID_POINT_MESSAGE = "找不到對應的條列項目，請重新指定點數。"
    NO_FOLLOWUP_TOPIC_MESSAGE = "目前沒有可延續的主題，請先提出一個資安問題。"

    def __init__(
        self,
        followup_handler,
        detector,
        rag_qa,
        responder,
        triage_policy,
        llm_assist=None,
    ):
        self.followup_handler = followup_handler
        self.detector = detector
        self.rag_qa = rag_qa
        self.responder = responder
        self.triage_policy = triage_policy
        self.llm_assist = llm_assist

    def preprocess_query(self, query):
        return " ".join(str(query or "").split())

    def should_append_rag_explanation(self, query, detector_result):
        if detector_result.get("status") != "ALERT":
            return False

        normalized = (query or "").lower()
        explanation_markers = [
            "?",
            "？",
            "what",
            "why",
            "how",
            "mean",
            "meaning",
            "explain",
            "解釋",
            "說明",
            "是什麼",
            "什麼意思",
            "為什麼",
            "如何",
            "怎麼",
            "影響",
            "危害",
            "防禦",
        ]
        return any(marker in normalized for marker in explanation_markers)

    def build_rag_answer(self, query):
        if not self.rag_qa.is_ready():
            return self.KB_UNAVAILABLE_MESSAGE

        if hasattr(self.rag_qa, "answer_question"):
            answer = self.rag_qa.answer_question(query)
            return answer if answer is not None else self.NO_CONTEXT_MESSAGE

        context, ok = self.rag_qa.retrieve_context(query)
        if not ok:
            return self.NO_CONTEXT_MESSAGE

        return self.rag_qa.generate_answer(query, context)

    def _update_state(self, state, query, answer, keep_focus=False):
        state["last_question"] = query
        state["last_answer"] = answer
        state["last_points"] = self.followup_handler.extract_points(answer)

        if keep_focus:
            state["last_focus"] = state["last_points"][0] if state["last_points"] else answer
        else:
            state["last_focus"] = ""

    def _should_use_llm_suspicious_finding(self, llm_judgment):
        if not llm_judgment or not llm_judgment.get("is_suspicious"):
            return False

        try:
            confidence = float(llm_judgment.get("confidence"))
        except (TypeError, ValueError):
            return False

        return confidence >= 0.75

    def _should_send_clean_input_to_llm(self, query, signals):
        signals = signals or {}
        has_payload_signal = bool(signals.get("keywords") or signals.get("patterns"))
        has_anomaly_indicator = bool(signals.get("anomaly_signals"))

        # Historical state may support analysis, but must not be the only trigger
        # for classifying a clean current input as suspicious.
        return has_payload_signal or self._is_log_like_security(query) or has_anomaly_indicator

    def _build_llm_suspicious_report(self, query, llm_judgment, signals=None):
        return self.responder.build_llm_suspicious_triage_report(
            query,
            llm_judgment,
            signals,
        )

    def _is_log_like_security(self, query):
        normalized = (query or "").lower()
        if not normalized:
            return False

        log_terms = [
            "login",
            "failed",
            "failure",
            "denied",
            "blocked",
            "attempt",
            "attempts",
            "same ip",
            "source ip",
            "from ip",
            "minute",
            "minutes",
            "second",
            "seconds",
            "times",
        ]
        suspicious_phrases = [
            "login failed",
            "failed login",
            "failed logins",
            "authentication failed",
            "failed authentication",
            "brute force",
            "same ip",
            "too many attempts",
        ]

        has_log_terms = sum(1 for term in log_terms if term in normalized) >= 3
        has_suspicious_phrase = any(phrase in normalized for phrase in suspicious_phrases)
        has_count = any(token.isdigit() and int(token) >= 10 for token in normalized.split())

        return has_suspicious_phrase and (has_log_terms or has_count)

    def _build_fallback_suspicious_report(self, query, signals=None):
        normalized = (query or "").lower()
        risk = "MEDIUM"
        action = "MONITOR"
        reasoning = "Log-like input contains suspicious authentication activity."
        attack_types = ["Suspicious Authentication Activity"]

        if (
            ("login failed" in normalized or "failed login" in normalized or "failed logins" in normalized)
            and ("same ip" in normalized or "from ip" in normalized or "source ip" in normalized)
        ):
            reasoning = "High-frequency failed logins from the same IP may indicate brute-force activity."
            risk = "HIGH"
            action = "BLOCK"
            attack_types = ["Brute Force"]

        return self.responder.build_llm_suspicious_triage_report(
            query,
            {
                "suggested_attack_types": attack_types,
                "recommended_risk": risk,
                "recommended_action": action,
                "confidence": None,
                "reasoning": reasoning,
                "llm_status": "FALLBACK",
            },
            signals,
        )

    def _handle_followup(self, query, state):
        if self.followup_handler.is_point_followup(query):
            if not state["last_points"]:
                return self.NO_POINT_MESSAGE

            if not self.followup_handler.has_valid_point_reference(query, state["last_points"]):
                return self.INVALID_POINT_MESSAGE

            index = self.followup_handler.extract_index(query)
            target = state["last_points"][index - 1]
            state["last_focus"] = target

            answer = self.rag_qa.explain_point(target)
            state["last_question"] = query
            state["last_answer"] = answer
            return answer

        active_context_kind = state.get("active_context_kind")
        if active_context_kind == "incident":
            incident_answer = answer_incident_followup(
                query,
                state.get("active_incident_context"),
            )
            if incident_answer is not None:
                self._update_state(state, query, incident_answer, keep_focus=True)
                return incident_answer
        elif active_context_kind == "event":
            event_answer = answer_event_followup(
                query,
                state.get("active_event_context"),
            )
            if event_answer is not None:
                self._update_state(state, query, event_answer, keep_focus=True)
                return event_answer
        else:
            event_answer = answer_event_followup(
                query,
                state.get("active_event_context"),
            )
            if event_answer is not None:
                self._update_state(state, query, event_answer, keep_focus=True)
                return event_answer

            incident_answer = answer_incident_followup(
                query,
                state.get("active_incident_context"),
            )
            if incident_answer is not None:
                self._update_state(state, query, incident_answer, keep_focus=True)
                return incident_answer

        if self.followup_handler.is_natural_followup(query):
            if not state["last_focus"]:
                return self.NO_FOLLOWUP_TOPIC_MESSAGE

            answer = self.rag_qa.handle_natural_followup(state["last_focus"], query)
            self._update_state(state, query, answer, keep_focus=True)
            return answer

        if self.followup_handler.is_contextual_followup(query, state):
            focus = state["last_focus"] if state["last_focus"] else state["last_answer"]
            answer = self.rag_qa.handle_natural_followup(focus, query)
            self._update_state(state, query, answer, keep_focus=True)
            return answer

        return None

    def _handle_attack_flow(self, query, detector_result, state):
        risk_result = self.triage_policy.score_risk(detector_result)
        decision_result = self.triage_policy.decide(risk_result)
        context, ok = "", False
        if self.rag_qa is not None:
            try:
                context, ok = self.rag_qa.retrieve_context(query)
            except Exception:
                context, ok = "", False

        llm_result = None
        if self.llm_assist is not None:
            try:
                llm_result = self.llm_assist.explain_alert(
                    query,
                    detector_result,
                    context if ok else "",
                    risk_result,
                    decision_result,
                    state,
                )
            except Exception:
                llm_result = None

        defense_result = self.triage_policy.simulate_defense(
            decision_result,
            detector_result,
            risk_result,
        )
        # Mode 1 attack alerts return one SOC-style report; RAG remains for Mode 3 Q&A.
        answer = self.responder.build_security_triage_report(
            detector_result,
            risk_result,
            decision_result,
            defense_result,
            llm_result,
        )
        state["active_event_context"] = build_active_event_context(
            detector_result=detector_result,
            risk_result=risk_result,
            decision_result=decision_result,
            defense_result=defense_result,
            rendered_report=answer,
        )
        state["active_context_kind"] = "event"
        self._update_state(state, query, answer, keep_focus=False)
        return answer

    def handle_knowledge_query(self, query, state):
        query = self.preprocess_query(query)
        if not query:
            return "請先輸入問題。"

        answer = self.build_rag_answer(query)
        self._update_state(state, query, answer, keep_focus=True)
        return answer

    def handle_query(self, query, state):
        query = self.preprocess_query(query)

        followup_answer = self._handle_followup(query, state)
        if followup_answer is not None:
            return followup_answer

        detector_result = self.detector.inspect_text(query)
        if detector_result["status"] == "ALERT":
            return self._handle_attack_flow(query, detector_result, state)

        if is_security_knowledge_question(query):
            answer = self.build_rag_answer(query)
            self._update_state(state, query, answer, keep_focus=True)
            return answer

        signals = extract_signals(query)
        llm_judgment = None
        should_use_llm_judge = self._should_send_clean_input_to_llm(query, signals)
        if should_use_llm_judge and self.llm_assist is not None:
            try:
                llm_judgment = self.llm_assist.judge_suspicious_behavior(
                    query,
                    detector_result,
                    rag_context="",
                    signals=signals,
                    state=state,
                )
            except Exception:
                llm_judgment = None

        if self._should_use_llm_suspicious_finding(llm_judgment):
            answer = self._build_llm_suspicious_report(query, llm_judgment, signals)
            self._update_state(state, query, answer, keep_focus=False)
            return answer

        if llm_judgment and llm_judgment.get("llm_status") == "FALLBACK" and self._is_log_like_security(query):
            answer = self._build_fallback_suspicious_report(query, signals)
            self._update_state(state, query, answer, keep_focus=False)
            return answer

        if not self.rag_qa.is_security(query):
            return self.NON_SECURITY_MESSAGE

        answer = self.build_rag_answer(query)
        self._update_state(state, query, answer, keep_focus=True)
        return answer
