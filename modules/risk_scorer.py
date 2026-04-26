class RiskScorer:
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

    def score(self, attack_types):
        unique_attack_types = list(dict.fromkeys(attack_types or []))
        if not unique_attack_types:
            return {
                "risk_level": "LOW",
                "reason": "未命中已知攻擊類型，維持低風險。",
            }

        highest_risk = "LOW"
        for attack_type in unique_attack_types:
            risk_level = self.RISK_BY_ATTACK_TYPE.get(attack_type, "LOW")
            if self.RISK_PRIORITY[risk_level] > self.RISK_PRIORITY[highest_risk]:
                highest_risk = risk_level

        return {
            "risk_level": highest_risk,
            "reason": "根據目前命中的攻擊類型進行簡單風險評分。",
        }
