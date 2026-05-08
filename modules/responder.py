class Responder:
    WHY_IT_MATTERS = {
        "XSS": "XSS 可能讓攻擊者把腳本注入頁面，影響使用者瀏覽器、竊取 session 或執行未授權操作。",
        "SQL Injection": "SQL Injection 可能讓攻擊者改變資料庫查詢邏輯，造成資料外洩、驗證繞過或資料破壞。",
        "Path Traversal": "Path Traversal 可能讓攻擊者嘗試讀取應用程式目錄外的敏感檔案，例如系統密碼檔或設定檔。",
        "Command Injection": "Command Injection 可能讓攻擊者透過 shell metacharacters 影響系統命令，進一步執行未授權程序。",
    }
    TRIAGE_NEXT_STEPS = {
        "XSS": [
            "檢查可疑輸入是否被反射到 response body 或頁面模板。",
            "確認輸出點已依 HTML、JavaScript 或 attribute context 正確 encoding。",
            "檢查 Content Security Policy (CSP) 是否啟用並限制不可信腳本來源。",
        ],
        "SQL Injection": [
            "確認受影響 endpoint、參數與原始請求內容。",
            "檢查 SQL error、異常查詢結果、資料外洩或 auth bypass 跡象。",
            "確認查詢使用參數化查詢或 prepared statements，避免字串拼接 SQL。",
        ],
        "Path Traversal": [
            "檢查檔案存取日誌，確認是否有敏感檔案讀取跡象。",
            "檢視被封鎖或拒絕的路徑嘗試，例如 ../、..\\ 或 /etc/passwd。",
            "確認路徑 normalization 與白名單限制只允許受控目錄內的檔案。",
        ],
        "Command Injection": [
            "檢查 spawned process logs，確認是否有非預期程序被啟動。",
            "檢視輸入中是否包含 shell metacharacters、管線或命令串接符號。",
            "盤點 command execution sinks，確認外部輸入不會直接進入系統命令。",
        ],
    }
    GENERIC_NEXT_STEPS = [
        "保留原始請求、時間、來源與相關日誌作為證據。",
        "確認受影響 endpoint 與使用者輸入進入點。",
        "依偵測結果檢查對應防護與監控是否生效。",
    ]

    RESPONSE_PLAYBOOKS = {
        "XSS": {
            "Immediate Actions": [
                "保留原始請求、時間、來源 IP、受影響 endpoint。",
                "檢查 payload 是否被反射到 response body、HTML template 或前端渲染點。",
                "暫時提高相關 endpoint 的監控等級。",
            ],
            "Mitigation": [
                "依 HTML、JavaScript、URL、attribute context 套用正確輸出 encoding。",
                "啟用或收緊 Content Security Policy (CSP)。",
                "避免將使用者輸入直接寫入 DOM 或 template。",
            ],
            "Follow-up": [
                "查詢同來源 IP 或同 endpoint 是否有其他 XSS payload。",
                "加入 XSS regression test cases。",
                "補上 WAF / IDS 偵測規則與告警。",
            ],
        },
        "SQL Injection": {
            "Immediate Actions": [
                "保留原始請求、參數、來源 IP、時間與受影響 endpoint。",
                "檢查 SQL error、登入繞過、異常查詢結果或資料外洩跡象。",
                "暫時提高受影響 endpoint 的監控等級。",
            ],
            "Mitigation": [
                "使用 parameterized queries 或 prepared statements。",
                "移除字串拼接 SQL。",
                "驗證輸入格式並限制不必要的特殊字元。",
            ],
            "Follow-up": [
                "查詢同來源 IP 是否有多次注入嘗試。",
                "檢查資料庫 audit log。",
                "加入 SQL injection regression test cases。",
            ],
        },
        "Path Traversal": {
            "Immediate Actions": [
                "保留原始請求、路徑參數、來源 IP、時間與 endpoint。",
                "檢查是否有敏感檔案讀取跡象。",
                "檢視相關檔案存取日誌。",
            ],
            "Mitigation": [
                "對路徑做 normalization。",
                "使用 allowlist 限制可存取檔案與目錄。",
                "阻擋 ../、..\\、絕對路徑與敏感系統檔案路徑。",
            ],
            "Follow-up": [
                "查詢同來源 IP 是否有其他 traversal 嘗試。",
                "檢查是否有 /etc/passwd、config、secret、.env 等目標。",
                "加入 path traversal regression test cases。",
            ],
        },
        "Command Injection": {
            "Immediate Actions": [
                "保留原始請求、參數、來源 IP、時間與 endpoint。",
                "檢查是否有非預期 process 被啟動。",
                "檢查 shell metacharacters、pipe、command chaining patterns。",
            ],
            "Mitigation": [
                "避免將使用者輸入直接傳入 shell command。",
                "使用安全 API 取代 shell execution。",
                "對命令參數使用 allowlist。",
            ],
            "Follow-up": [
                "查詢 process logs 與系統 audit logs。",
                "檢查是否有 lateral movement 或 privilege escalation 跡象。",
                "加入 command injection regression test cases。",
            ],
        },
    }
    GENERIC_RESPONSE_PLAYBOOK = {
        "Immediate Actions": [
            "保留原始事件、時間、來源與相關日誌。",
            "確認受影響 endpoint 或系統元件。",
            "標記事件供後續人工複核。",
        ],
        "Mitigation": [
            "檢查輸入驗證、輸出處理與存取控制。",
            "確認監控與告警規則是否涵蓋此類事件。",
            "降低不必要的攻擊面。",
        ],
        "Follow-up": [
            "查詢同來源或相同 pattern 的其他事件。",
            "將確認過的指標加入知識庫或偵測規則。",
            "建立回歸測試案例。",
        ],
    }

    def __init__(self):
        pass

    def _unique_items(self, items):
        return [item for item in dict.fromkeys(items or []) if item]

    def _format_detection_source(self, detector_result):
        detector = detector_result.get("detector") or {}
        name = detector.get("name") or "rule-based detector"
        detector_type = detector.get("type")
        if detector_type:
            return f"{name} ({detector_type})"
        return name

    def _format_quick_reason(self, matched_signatures):
        if not matched_signatures:
            return "No matched signature evidence was available."

        reasons = []
        for attack_type, signatures in matched_signatures.items():
            signatures = self._unique_items(signatures)
            if signatures:
                reasons.append(f"Matched {attack_type} indicators: {', '.join(signatures)}")

        return "; ".join(reasons) if reasons else "No matched signature evidence was available."

    def _format_quick_verdict(self, attack_types, detector_result, risk_result, decision_result):
        attack_type_text = ", ".join(attack_types)
        if attack_type_text:
            verdict = f"This event is likely {attack_type_text}."
        else:
            verdict = "No known attack signature was confirmed."

        return [
            "0. Quick Verdict",
            f"Verdict: {verdict}",
            f"Risk Level: {risk_result.get('risk_level', 'LOW')}",
            f"Decision: {decision_result.get('decision', 'ALLOW')}",
            f"Reason: {self._format_quick_reason(detector_result.get('matched_signatures'))}",
            "",
        ]

    def _format_matched_signatures(self, matched_signatures):
        if not matched_signatures:
            return ["- 無"]

        lines = []
        for attack_type, signatures in matched_signatures.items():
            joined = ", ".join(signatures) if signatures else "無"
            lines.append(f"- {attack_type}: {joined}")
        return lines

    def _format_evidence(self, detector_result):
        lines = [
            "2. Evidence",
            "Input / Payload:",
            str(detector_result.get("original_input", "")),
            "",
            "Matched Signatures:",
        ]
        lines.extend(self._format_matched_signatures(detector_result.get("matched_signatures")))
        return lines

    def _format_why_it_matters(self, attack_types):
        descriptions = [
            f"- {attack_type}: {self.WHY_IT_MATTERS[attack_type]}"
            for attack_type in attack_types
            if attack_type in self.WHY_IT_MATTERS
        ]
        if descriptions:
            return descriptions
        return ["- 此輸入命中可疑模式，建議保留證據並進一步確認是否影響實際服務。"]

    def _build_response_playbook(self, attack_types):
        sections = {
            "Immediate Actions": [],
            "Mitigation": [],
            "Follow-up": [],
        }

        selected_playbooks = [
            self.RESPONSE_PLAYBOOKS[attack_type]
            for attack_type in attack_types
            if attack_type in self.RESPONSE_PLAYBOOKS
        ]
        if not selected_playbooks:
            selected_playbooks = [self.GENERIC_RESPONSE_PLAYBOOK]

        for playbook in selected_playbooks:
            for section_title in sections:
                sections[section_title].extend(playbook.get(section_title, []))

        return {
            section_title: self._unique_items(items)
            for section_title, items in sections.items()
        }

    def _format_response_section(self, section_title, items):
        lines = [f"{section_title}:"]
        lines.extend(f"{index}. {item}" for index, item in enumerate(items, start=1))
        return lines

    def _format_recommended_response(self, attack_types):
        playbook = self._build_response_playbook(attack_types)
        lines = []
        for section_title in ("Immediate Actions", "Mitigation", "Follow-up"):
            if lines:
                lines.append("")
            lines.extend(self._format_response_section(section_title, playbook[section_title]))
        return lines

    def _format_confidence(self, llm_result):
        try:
            return f"{float(llm_result.get('confidence')):.2f}"
        except (TypeError, ValueError):
            return "N/A"

    def _format_ai_assist_note(self, llm_result):
        if not llm_result:
            return []

        attack_types = self._unique_items(llm_result.get("possible_attack_types") or [])
        suggested_attack_type = ", ".join(attack_types) if attack_types else "None"
        return [
            "",
            "6. AI Assist",
            f"LLM Suggested Attack Type: {suggested_attack_type}",
            f"LLM Suggested Decision: {llm_result.get('recommended_decision', 'N/A')}",
            f"Confidence: {self._format_confidence(llm_result)}",
            "Note: Decision above is the final system decision; LLM Suggested Decision is AI assist only.",
        ]

    def _format_simulation_note(self, defense_result):
        return [
            "",
            "5. Simulation Notice",
            defense_result.get("summary", "此判定僅為模擬，不會執行實際系統操作。"),
        ]

    def build_security_triage_report(
        self,
        detector_result,
        risk_result,
        decision_result,
        defense_result,
        llm_result=None,
    ):
        attack_types = self._unique_items(detector_result.get("attack_types"))
        attack_type_text = ", ".join(attack_types) if attack_types else "None"

        lines = [
            "[Security Triage Report]",
            "",
        ]
        lines.extend(self._format_quick_verdict(attack_types, detector_result, risk_result, decision_result))
        lines.extend(
            [
                "1. Summary",
                f"Status: {detector_result.get('status', 'UNKNOWN')}",
                f"Attack Type: {attack_type_text}",
                f"Risk Level: {risk_result.get('risk_level', 'LOW')}",
                f"Decision: {decision_result.get('decision', 'ALLOW')}",
                f"Detection Source: {self._format_detection_source(detector_result)}",
                "",
            ]
        )
        lines.extend(self._format_evidence(detector_result))
        lines.extend(["", "3. Why It Matters"])
        lines.extend(self._format_why_it_matters(attack_types))
        lines.extend(["", "4. Recommended Response"])
        lines.extend(self._format_recommended_response(attack_types))
        lines.extend(self._format_simulation_note(defense_result))
        lines.extend(self._format_ai_assist_note(llm_result))
        return "\n".join(lines).strip()

    def trigger_automated_defense(self, action):
        """
        Keep the original placeholder automation hook.
        """
        print(f"已觸發自動化防禦動作：{action}")
        return True
