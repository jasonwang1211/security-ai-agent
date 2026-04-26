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
    ):
        self.followup_handler = followup_handler
        self.detector = detector
        self.rag_qa = rag_qa
        self.responder = responder
        self.risk_scorer = risk_scorer
        self.decision_engine = decision_engine
        self.defense_simulator = defense_simulator

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

        return None

    def _handle_attack_flow(self, query, detector_result, state):
        risk_result = self.risk_scorer.score(detector_result["attack_types"])
        decision_result = self.decision_engine.decide(risk_result["risk_level"])
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

        if not self.rag_qa.is_security(query):
            return self.NON_SECURITY_MESSAGE

        answer = self.build_rag_answer(query)
        self._update_state(state, query, answer, keep_focus=True)
        return answer
