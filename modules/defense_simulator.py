class DefenseSimulator:
    DEFAULT_DECISION = "ALLOW"
    DEFAULT_RISK = "LOW"
    SIMULATED_STATUS = "SIMULATED"
    FALLBACK_MESSAGE = "已完成模擬應變，但未執行任何實際系統操作。"
    ACTION_MESSAGES = {
        "BLOCK": "已模擬封鎖這次可疑請求，未實際修改任何系統或防火牆設定。",
        "MONITOR": "已模擬將此事件加入監控與告警佇列，未實際部署監控規則。",
        "ALLOW": "已模擬允許流量通過，但標記為低風險事件供後續觀察。",
    }

    def _normalize_decision(self, decision):
        return (decision or self.DEFAULT_DECISION).upper()

    def _summary_for_decision(self, decision):
        return self.ACTION_MESSAGES.get(decision, self.FALLBACK_MESSAGE)

    def _build_result(self, action, summary, detector_result, risk_result):
        return {
            "action": action,
            "status": self.SIMULATED_STATUS,
            "summary": summary,
            "attack_types": detector_result.get("attack_types", []),
            "risk_level": risk_result.get("risk_level", self.DEFAULT_RISK),
        }

    def simulate(self, decision, detector_result, risk_result):
        normalized_decision = self._normalize_decision(decision)
        return self._build_result(
            normalized_decision,
            self._summary_for_decision(normalized_decision),
            detector_result,
            risk_result,
        )
