class DecisionEngine:
    DEFAULT_RISK = "LOW"
    DEFAULT_DECISION = "ALLOW"
    DECISION_BY_RISK = {
        "HIGH": "BLOCK",
        "MEDIUM": "MONITOR",
        "LOW": "ALLOW",
    }

    def _normalize_risk(self, risk_level):
        return (risk_level or self.DEFAULT_RISK).upper()

    def _decision_for_risk(self, risk_level):
        return self.DECISION_BY_RISK.get(risk_level, self.DEFAULT_DECISION)

    def _build_result(self, decision, reason):
        return {
            "decision": decision,
            "reason": reason,
        }

    def decide(self, risk_level):
        normalized_risk = self._normalize_risk(risk_level)
        decision = self._decision_for_risk(normalized_risk)
        return self._build_result(
            decision,
            f"依據風險等級 {normalized_risk} 採取 {decision}。",
        )
