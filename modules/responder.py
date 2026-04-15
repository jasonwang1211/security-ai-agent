class Responder:
    def __init__(self):
        pass

    def provide_recommendations(self, attack_type, details):
        """
        根據攻擊類型提供修補建議
        """
        recommendations = {
            "SQL Injection": [
                "使用參數化查詢或預編譯語句",
                "對用戶輸入進行適當的清理和驗證",
                "使用 ORM 框架避免直接拼接 SQL"
            ],
            "XSS": [
                "對所有用戶輸入進行 HTML 編碼",
                "使用 Content Security Policy (CSP)",
                "驗證和清理用戶提供的數據"
            ],
            "Path Traversal": [
                "驗證和清理文件路徑輸入",
                "使用白名單限制可訪問的文件",
                "避免直接使用用戶輸入作為文件路徑"
            ]
        }

        return recommendations.get(attack_type, ["請參考資安最佳實務"])

    def plan_response_steps(self, incident):
        """
        規劃後續處理步驟
        """
        steps = [
            "1. 立即隔離受影響系統",
            "2. 收集和分析攻擊證據",
            "3. 通知相關利益相關者",
            "4. 執行修補措施",
            "5. 監控系統恢復情況",
            "6. 進行事後檢討和改進"
        ]
        return steps

    def trigger_automated_defense(self, action):
        """
        預留自動化防禦接口
        """
        # 這裡可以實現自動化防禦邏輯
        # 例如：封鎖 IP、更新防火牆規則等
        print(f"觸發自動防禦動作: {action}")
        return True