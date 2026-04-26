class DecisionEngine:
    DECISION_BY_RISK = {
        "HIGH": "BLOCK",
        "MEDIUM": "MONITOR",
        "LOW": "ALLOW",
    }

    def decide(self, risk_level):
        normalized_risk = (risk_level or "LOW").upper()
        decision = self.DECISION_BY_RISK.get(normalized_risk, "ALLOW")
        return {
            "decision": decision,
            "reason": f"依據風險等級 {normalized_risk} 採取 {decision}。",
        }
