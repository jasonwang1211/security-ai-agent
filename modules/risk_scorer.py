class RiskScorer:
    DEFAULT_RISK = "LOW"
    RISK_BY_ATTACK_TYPE = {
        "SQL Injection": "HIGH",
        "Path Traversal": "HIGH",
        "XSS": "MEDIUM",
    }
    RISK_PRIORITY = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
    }

    def _build_result(self, risk_level, reason):
        return {
            "risk_level": risk_level,
            "reason": reason,
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

    def score(self, attack_types):
        unique_attack_types = self._unique_attack_types(attack_types)
        if not unique_attack_types:
            return self._build_result(
                self.DEFAULT_RISK,
                "未命中已知攻擊類型，維持低風險。",
            )

        return self._build_result(
            self._highest_risk(unique_attack_types),
            "根據目前命中的攻擊類型進行簡單風險評分。",
        )
