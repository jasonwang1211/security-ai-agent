class DefenseSimulator:
    ACTION_MESSAGES = {
        "BLOCK": "已模擬封鎖這次可疑請求，未實際修改任何系統或防火牆設定。",
        "MONITOR": "已模擬將此事件加入監控與告警佇列，未實際部署監控規則。",
        "ALLOW": "已模擬允許流量通過，但標記為低風險事件供後續觀察。",
    }

    def simulate(self, decision, detector_result, risk_result):
        normalized_decision = (decision or "ALLOW").upper()
        summary = self.ACTION_MESSAGES.get(
            normalized_decision,
            "已完成模擬應變，但未執行任何實際系統操作。",
        )
        return {
            "action": normalized_decision,
            "status": "SIMULATED",
            "summary": summary,
            "attack_types": detector_result.get("attack_types", []),
            "risk_level": risk_result.get("risk_level", "LOW"),
        }
