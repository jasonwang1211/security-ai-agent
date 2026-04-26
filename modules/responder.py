class Responder:
    def __init__(self):
        pass

    def provide_recommendations(self, attack_type, details):
        """
        Provide defensive recommendations for the detected attack type.
        """
        recommendations = {
            "SQL Injection": [
                "使用參數化查詢或 prepared statements，避免字串拼接 SQL。",
                "驗證與限制使用者輸入格式，避免危險字元直接進入查詢。",
                "優先使用 ORM 或安全的資料存取層來降低手寫 SQL 風險。",
            ],
            "XSS": [
                "輸出到 HTML 前先做適當跳脫，避免惡意腳本被瀏覽器執行。",
                "啟用 Content Security Policy (CSP) 限制可執行腳本來源。",
                "避免直接信任使用者輸入，特別是可回顯到頁面的欄位。",
            ],
            "Path Traversal": [
                "限制可存取的檔案路徑，避免直接使用使用者提供的路徑。",
                "對路徑做正規化與白名單驗證，拒絕包含 ../ 或 ..\\ 的輸入。",
                "讓應用程式只在受控目錄下讀寫，避免碰觸系統敏感檔案。",
            ],
        }

        return recommendations.get(attack_type, ["請參考資安最佳實務並進一步人工確認。"])

    def plan_response_steps(self, incident):
        """
        Return a small, reusable incident response checklist.
        """
        return [
            "1. 先確認影響範圍並保留相關請求、日誌與證據。",
            "2. 暫時阻擋或限制可疑來源、輸入點或受影響功能。",
            "3. 檢查是否已有資料外洩、權限提升或檔案讀取跡象。",
            "4. 修補對應弱點後再重新驗證是否仍可重現。",
            "5. 補上監控、告警與輸入驗證，避免同類事件再次發生。",
        ]

    def build_response_package(self, attack_types, details=None):
        unique_attack_types = list(dict.fromkeys(attack_types or []))
        recommendation_map = {
            attack_type: self.provide_recommendations(attack_type, details)
            for attack_type in unique_attack_types
        }

        summary = "未偵測到明確攻擊特徵。"
        if unique_attack_types:
            summary = "偵測到可能的攻擊類型：" + ", ".join(unique_attack_types)

        return {
            "summary": summary,
            "recommendations": recommendation_map,
            "response_steps": self.plan_response_steps(details),
        }

    def trigger_automated_defense(self, action):
        """
        Keep the original placeholder automation hook.
        """
        print(f"已觸發自動化防禦動作：{action}")
        return True
