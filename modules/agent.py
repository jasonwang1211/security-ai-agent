import re

from modules.llm_analyzer import LLMSecurityAnalyzer


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
        risk_scorer,
        decision_engine,
        defense_simulator,
        llm_analyzer=None,
        llm_threat_judge=None,
    ):
        self.followup_handler = followup_handler
        self.detector = detector
        self.rag_qa = rag_qa
        self.responder = responder
        self.risk_scorer = risk_scorer
        self.decision_engine = decision_engine
        self.defense_simulator = defense_simulator
        self.llm_analyzer = llm_analyzer
        self.llm_threat_judge = llm_threat_judge

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

    def _format_signatures(self, matched_signatures):
        if not matched_signatures:
            return ["- 無"]

        lines = []
        for attack_type, signatures in matched_signatures.items():
            joined = ", ".join(signatures) if signatures else "無"
            lines.append(f"- {attack_type}: {joined}")
        return lines

    def _format_recommendations(self, recommendations):
        lines = []
        for attack_type, items in recommendations.items():
            lines.append(f"{attack_type}:")
            for item in items:
                lines.append(f"- {item}")
        return lines or ["- 無額外建議"]

    def _format_ai_assisted_analysis(self, llm_result):
        if not llm_result:
            return []

        attack_types = [
            str(item).strip()
            for item in (llm_result.get("possible_attack_types") or [])
            if str(item).strip()
        ]
        reasoning = str(llm_result.get("reasoning") or "").strip() or "No additional analysis available."
        recommended_decision = str(llm_result.get("recommended_decision") or "N/A").strip()

        try:
            confidence_text = f"{float(llm_result.get('confidence')):.2f}"
        except (TypeError, ValueError):
            confidence_text = "N/A"

        return [
            "AI-Assisted Analysis",
            f"Reasoning: {reasoning}",
            f"Possible Attack Types: {', '.join(attack_types) if attack_types else 'None'}",
            f"Recommended Decision: {recommended_decision}",
            f"Confidence: {confidence_text}",
        ]

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

    def _build_llm_suspicious_report(self, llm_judgment, signals=None):
        attack_types = [
            str(item).strip()
            for item in (llm_judgment.get("suggested_attack_types") or [])
            if str(item).strip()
        ]

        try:
            confidence_text = f"{float(llm_judgment.get('confidence')):.2f}"
        except (TypeError, ValueError):
            confidence_text = "N/A"

        lines = [
            "LLM-assisted suspicious finding",
            f"Suggested Attack Types: {', '.join(attack_types) if attack_types else 'None'}",
            f"Recommended Risk: {llm_judgment.get('recommended_risk', 'N/A')}",
            f"Recommended Action: {llm_judgment.get('recommended_action', 'N/A')}",
            f"Confidence: {confidence_text}",
            f"Reasoning: {llm_judgment.get('reasoning', 'No reasoning provided.')}",
            f"LLM Status: {llm_judgment.get('llm_status', 'FALLBACK')}",
        ]

        try:
            confidence = float(llm_judgment.get("confidence"))
        except (TypeError, ValueError):
            confidence = 0.0

        try:
            anomaly_score = float(llm_judgment.get("anomaly_score"))
        except (TypeError, ValueError):
            anomaly_score = 0.0

        llm_status = str(llm_judgment.get("llm_status") or "FALLBACK").upper()
        llm_influenced_decision = llm_status != "FALLBACK" and confidence >= 0.85
        anomaly_triggered = anomaly_score >= 0.8
        final_risk = llm_judgment.get("recommended_risk", "MEDIUM") if llm_influenced_decision else "MEDIUM"
        final_decision = llm_judgment.get("recommended_action", "MONITOR") if llm_influenced_decision else "MONITOR"

        if anomaly_triggered:
            final_risk = "HIGH"
            if final_decision == "ALLOW":
                final_decision = "MONITOR"

        lines.append(f"Final Risk: {final_risk}")
        lines.append(f"Final Decision: {final_decision}")

        if llm_influenced_decision:
            lines.append("Decision influenced by AI analysis")

        if anomaly_triggered:
            lines.append("Anomaly-based detection triggered (possible zero-day)")

        signals = signals or {}
        detected_signals = []
        for key in ("keywords", "patterns", "anomaly_signals"):
            detected_signals.extend(signals.get(key) or [])

        lines.extend(
            [
                "",
                "Threat Intelligence Analysis",
                f"Why Suspicious: {llm_judgment.get('reasoning', 'The input contains signals associated with suspicious activity.')}",
                f"Detected Signals: {', '.join(detected_signals) if detected_signals else 'None'}",
                f"Attack Pattern Explanation: {', '.join(attack_types) if attack_types else 'No specific attack pattern identified; behavior is anomalous.'}",
                f"Risk Reasoning: Recommended risk is {llm_judgment.get('recommended_risk', 'N/A')} based on confidence {confidence_text} and observed signals.",
            ]
        )

        return "\n".join(lines)

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

    def _build_fallback_suspicious_report(self, query):
        normalized = (query or "").lower()
        risk = "MEDIUM"
        action = "MONITOR"
        reasoning = "Log-like input contains suspicious authentication activity."

        if (
            ("login failed" in normalized or "failed login" in normalized or "failed logins" in normalized)
            and ("same ip" in normalized or "from ip" in normalized or "source ip" in normalized)
        ):
            reasoning = "High-frequency failed logins from the same IP may indicate brute-force activity."
            risk = "HIGH"
            action = "BLOCK"

        return "\n".join(
            [
                "Fallback Suspicious Finding (LLM unavailable)",
                f"Reasoning: {reasoning}",
                f"Recommended Action: {action}",
                f"Risk: {risk}",
                "Note: LLM unavailable, heuristic fallback used",
                "LLM Status: FALLBACK",
            ]
        )

    def _build_attack_report(self, detector_result, response_package, risk_result, decision_result, defense_result):
        lines = [
            "藍隊分析報告",
            f"攻擊摘要：{response_package['summary']}",
            f"攻擊類型：{', '.join(detector_result['attack_types'])}",
            "命中簽章：",
        ]
        lines.extend(self._format_signatures(detector_result.get("matched_signatures")))
        lines.extend(
            [
                f"風險等級：{risk_result['risk_level']}",
                f"判定動作：{decision_result['decision']}",
                f"模擬防禦：{defense_result['summary']}",
                "",
                "防禦建議：",
            ]
        )
        lines.extend(self._format_recommendations(response_package["recommendations"]))
        lines.extend(["", "Incident Response Checklist:"])
        lines.extend(response_package["response_steps"])
        return "\n".join(lines).strip()

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
        risk_result = self.risk_scorer.score(detector_result["attack_types"])
        decision_result = self.decision_engine.decide(risk_result["risk_level"])
        context, ok = "", False
        if self.rag_qa is not None:
            try:
                context, ok = self.rag_qa.retrieve_context(query)
            except Exception:
                context, ok = "", False

        llm_result = None
        if self.llm_analyzer is not None:
            try:
                llm_result = self.llm_analyzer.analyze(
                    query,
                    detector_result,
                    context if ok else "",
                    risk_result,
                    decision_result,
                    state,
                )
            except Exception:
                llm_result = None

        defense_result = self.defense_simulator.simulate(
            decision_result["decision"],
            detector_result,
            risk_result,
        )
        response_package = self.responder.build_response_package(
            detector_result["attack_types"],
            details=detector_result,
        )

        parts = [
            self._build_attack_report(
                detector_result,
                response_package,
                risk_result,
                decision_result,
                defense_result,
            )
        ]

        if self.should_append_rag_explanation(query, detector_result):
            rag_query = query
            if not self.rag_qa.is_security(query):
                rag_query = f"{query}\n\n攻擊類型：{', '.join(detector_result['attack_types'])}"
            rag_answer = self.build_rag_answer(rag_query)
            parts.append(f"補充說明：\n{rag_answer}")

        if llm_result:
            parts.append("\n".join(self._format_ai_assisted_analysis(llm_result)))

        answer = "\n\n".join(parts)
        self._update_state(state, query, answer, keep_focus=False)
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
        if should_use_llm_judge and self.llm_threat_judge is not None:
            try:
                llm_judgment = self.llm_threat_judge.judge(
                    query,
                    detector_result,
                    rag_context="",
                    signals=signals,
                    state=state,
                )
            except Exception:
                llm_judgment = None

        if self._should_use_llm_suspicious_finding(llm_judgment):
            answer = self._build_llm_suspicious_report(llm_judgment, signals)
            self._update_state(state, query, answer, keep_focus=False)
            return answer

        if llm_judgment and llm_judgment.get("llm_status") == "FALLBACK" and self._is_log_like_security(query):
            answer = self._build_fallback_suspicious_report(query)
            self._update_state(state, query, answer, keep_focus=False)
            return answer

        if not self.rag_qa.is_security(query):
            return self.NON_SECURITY_MESSAGE

        answer = self.build_rag_answer(query)
        self._update_state(state, query, answer, keep_focus=True)
        return answer
