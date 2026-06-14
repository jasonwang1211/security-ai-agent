class TriagePolicy:
    DEFAULT_RISK = "LOW"
    DEFAULT_DECISION = "ALLOW"
    SIMULATED_STATUS = "SIMULATED"

    RISK_BY_ATTACK_TYPE = {
        "SQL Injection": "HIGH",
        "Path Traversal": "HIGH",
        "Command Injection": "HIGH",
        "XSS": "MEDIUM",
        "HTTP/2 Resource Exhaustion Suspicion": "MEDIUM",
    }
    RISK_PRIORITY = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
    }
    DECISION_BY_RISK = {
        "HIGH": "BLOCK",
        "MEDIUM": "MONITOR",
        "LOW": "ALLOW",
    }
    FALLBACK_MESSAGE = "已完成模擬應變，但未執行任何實際系統操作。"
    ACTION_MESSAGES = {
        "BLOCK": "已模擬封鎖這次可疑請求，未實際修改任何系統或防火牆設定。",
        "MONITOR": "已模擬將此事件加入監控與告警佇列，未實際部署監控規則。",
        "ALLOW": "已模擬允許流量通過，但標記為低風險事件供後續觀察。",
    }

    def _build_risk_result(self, risk_level, reason):
        return {
            "risk_level": risk_level,
            "reason": reason,
        }

    def _build_decision_result(self, decision, reason):
        return {
            "decision": decision,
            "reason": reason,
        }

    def _build_defense_result(self, action, summary, detector_result, risk_result):
        return {
            "action": action,
            "status": self.SIMULATED_STATUS,
            "summary": summary,
            "attack_types": detector_result.get("attack_types", []),
            "risk_level": risk_result.get("risk_level", self.DEFAULT_RISK),
        }

    def _unique_attack_types(self, attack_types):
        return list(dict.fromkeys(attack_types or []))

    def _highest_risk(self, attack_types):
        highest_risk = self.DEFAULT_RISK
        for attack_type in attack_types:
            risk_level = self.RISK_BY_ATTACK_TYPE.get(attack_type, self.DEFAULT_RISK)
            if self.RISK_PRIORITY[risk_level] > self.RISK_PRIORITY[highest_risk]:
                highest_risk = risk_level
        return highest_risk

    def _normalize_risk(self, risk_level):
        return (risk_level or self.DEFAULT_RISK).upper()

    def _decision_for_risk(self, risk_level):
        return self.DECISION_BY_RISK.get(risk_level, self.DEFAULT_DECISION)

    def _normalize_decision(self, decision):
        return (decision or self.DEFAULT_DECISION).upper()

    def _summary_for_decision(self, decision):
        return self.ACTION_MESSAGES.get(decision, self.FALLBACK_MESSAGE)

    def score_risk(self, detector_result, llm_result=None):
        attack_types = []
        if isinstance(detector_result, dict):
            attack_types = detector_result.get("attack_types", [])

        unique_attack_types = self._unique_attack_types(attack_types)
        if not unique_attack_types:
            return self._build_risk_result(
                self.DEFAULT_RISK,
                "未命中已知攻擊類型，維持低風險。",
            )

        return self._build_risk_result(
            self._highest_risk(unique_attack_types),
            "根據目前命中的攻擊類型進行簡單風險評分。",
        )

    def decide(self, risk_result, llm_result=None):
        risk_level = None
        if isinstance(risk_result, dict):
            risk_level = risk_result.get("risk_level")

        normalized_risk = self._normalize_risk(risk_level)
        decision = self._decision_for_risk(normalized_risk)
        return self._build_decision_result(
            decision,
            f"依據風險等級 {normalized_risk} 採取 {decision}。",
        )

    def simulate_defense(self, decision_result, detector_result=None, risk_result=None):
        decision = None
        if isinstance(decision_result, dict):
            decision = decision_result.get("decision")

        detector_result = detector_result or {}
        risk_result = risk_result or {}
        normalized_decision = self._normalize_decision(decision)
        return self._build_defense_result(
            normalized_decision,
            self._summary_for_decision(normalized_decision),
            detector_result,
            risk_result,
        )
