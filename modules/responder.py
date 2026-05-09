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

    AUTH_SUSPICIOUS_PLAYBOOK = {
        "Immediate Actions": [
            "保留登入失敗日誌、來源 IP、使用者、endpoint、時間窗與 failed_count。",
            "檢查同一 source_ip 是否對同一 endpoint 或多個帳號重複嘗試。",
            "檢查同一 user 是否從多個 source_ip 或異常地區出現登入失敗。",
        ],
        "Mitigation": [
            "啟用 rate limiting、帳號鎖定或漸進式延遲。",
            "啟用 MFA 或加強高風險登入驗證。",
            "對異常來源 IP、ASN、地理位置或裝置指紋提高監控等級。",
        ],
        "Follow-up": [
            "查詢是否有登入成功事件緊接在大量失敗之後。",
            "比對是否有 credential stuffing、password spraying 或帳號接管跡象。",
            "將確認後的來源、使用者與時間窗加入偵測規則或告警條件。",
        ],
    }
    GENERIC_SUSPICIOUS_PLAYBOOK = {
        "Immediate Actions": [
            "保留原始事件、來源、目標、時間窗與相關上下文。",
            "檢查同一來源或同一帳號是否有重複、異常或跨 endpoint 的行為。",
            "確認近期是否有相同模式的告警、失敗事件或異常流量。",
        ],
        "Mitigation": [
            "提高相關來源、使用者與 endpoint 的監控等級。",
            "套用既有 allowlist、rate limiting 或存取控制檢查。",
            "在不影響正常服務的前提下，加強日誌與告警條件。",
        ],
        "Follow-up": [
            "比對後續是否出現成功存取、權限提升或資料外洩跡象。",
            "將確認後的行為特徵加入偵測規則或告警條件。",
            "若行為持續或擴大，升級給 SOC / IR 團隊進一步調查。",
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

    def _extract_llm_attack_types(self, llm_result):
        if not llm_result:
            return []

        raw_values = []
        for key in ("suggested_attack_types", "possible_attack_types", "attack_types"):
            value = llm_result.get(key)
            if isinstance(value, list):
                raw_values.extend(value)
            elif isinstance(value, str):
                raw_values.extend(part.strip() for part in value.split(","))

        for key in ("suggested_attack_type", "possible_attack_type", "attack_type"):
            value = llm_result.get(key)
            if isinstance(value, str):
                raw_values.extend(part.strip() for part in value.split(","))

        return self._unique_items(str(item).strip() for item in raw_values if str(item).strip())

    def _format_llm_suspicious_reason(self, llm_result, detected_signals):
        reasoning = (llm_result or {}).get("reasoning")
        if reasoning:
            text = str(reasoning).strip()
            return text[:237] + "..." if len(text) > 240 else text

        if detected_signals:
            return "Observed suspicious signals: " + ", ".join(detected_signals[:5])

        return "The event contains behavior signals associated with suspicious activity."

    def _derive_llm_suspicious_outcome(self, llm_result):
        llm_result = llm_result or {}
        try:
            confidence = float(llm_result.get("confidence"))
        except (TypeError, ValueError):
            confidence = 0.0

        try:
            anomaly_score = float(llm_result.get("anomaly_score"))
        except (TypeError, ValueError):
            anomaly_score = 0.0

        llm_status = str(llm_result.get("llm_status") or "FALLBACK").upper()
        llm_influenced_decision = llm_status != "FALLBACK" and confidence >= 0.85
        anomaly_triggered = anomaly_score >= 0.8
        final_risk = llm_result.get("recommended_risk", "MEDIUM") if llm_influenced_decision else "MEDIUM"
        final_decision = llm_result.get("recommended_action", "MONITOR") if llm_influenced_decision else "MONITOR"

        if anomaly_triggered:
            final_risk = "HIGH"
            if final_decision == "ALLOW":
                final_decision = "MONITOR"

        return final_risk, final_decision

    def _format_detected_signals(self, signals=None, llm_result=None):
        detected_signals = []
        signals = signals or {}
        for key in ("keywords", "patterns", "anomaly_signals"):
            detected_signals.extend(signals.get(key) or [])

        llm_signals = (llm_result or {}).get("detected_signals")
        if isinstance(llm_signals, list):
            detected_signals.extend(llm_signals)
        elif isinstance(llm_signals, str):
            detected_signals.extend(part.strip() for part in llm_signals.split(","))

        return self._unique_items(str(item).strip() for item in detected_signals if str(item).strip())

    def _is_auth_suspicious_attack(self, attack_types):
        normalized = " ".join(attack_types or []).lower()
        return "brute force" in normalized or "credential stuffing" in normalized

    def _format_llm_suspicious_why_it_matters(self, attack_types):
        if self._is_auth_suspicious_attack(attack_types):
            return [
                "- Brute Force / Credential Stuffing: 大量登入失敗或跨帳號嘗試可能代表密碼猜測、憑證填充或帳號接管前兆，需要確認是否已有成功登入緊接在失敗事件之後。"
            ]

        return [
            "- Suspicious Behavior: 雖然規則型偵測器未命中特定簽章，LLM 與訊號萃取仍指出異常行為，應先保留證據並提高監控，避免早期攻擊活動被誤判為正常流量。"
        ]

    def _build_llm_suspicious_playbook(self, attack_types):
        if self._is_auth_suspicious_attack(attack_types):
            return self.AUTH_SUSPICIOUS_PLAYBOOK
        return self.GENERIC_SUSPICIOUS_PLAYBOOK

    def _format_llm_suspicious_response(self, attack_types):
        playbook = self._build_llm_suspicious_playbook(attack_types)
        lines = []
        for section_title in ("Immediate Actions", "Mitigation", "Follow-up"):
            if lines:
                lines.append("")
            lines.extend(self._format_response_section(section_title, playbook[section_title]))
        return lines

    def _format_llm_simulation_notice(self):
        return [
            "",
            "5. Simulation Notice",
            "這是防禦模擬輸出：BLOCK / MONITOR / ALLOW 都是系統建議的模擬決策，不會自動封鎖、監控或放行真實流量；實際處置需由 SOC / IR 團隊確認後執行。",
        ]

    def _format_llm_suspicious_ai_assist(self, llm_result, attack_type_text):
        llm_result = llm_result or {}
        lines = [
            "",
            "6. AI Assist",
            f"LLM Suggested Attack Type: {attack_type_text}",
            f"LLM Recommended Risk: {llm_result.get('recommended_risk', 'N/A')}",
            f"LLM Suggested Decision: {llm_result.get('recommended_action', 'N/A')}",
            f"Confidence: {self._format_confidence(llm_result)}",
            f"Reasoning: {llm_result.get('reasoning', 'No reasoning provided.')}",
        ]

        if llm_result.get("llm_status"):
            lines.append(f"LLM Status: {llm_result.get('llm_status')}")

        lines.append("Note: Decision above is the final system decision; LLM Suggested Decision is AI assist only.")
        return lines

    def _format_auth_failure_value(self, event, key):
        value = (event or {}).get(key)
        text = str(value or "").strip()
        return text if text else "N/A"

    def _format_auth_failure_response(self):
        return [
            "Immediate Actions:",
            "1. 保留登入失敗日誌、來源 IP、使用者、endpoint 與時間。",
            "2. 檢查同一 source_ip / user / endpoint 是否有重複失敗。",
            "3. 檢查是否有成功登入緊接在失敗事件之後。",
            "",
            "Mitigation:",
            "1. 對登入端點啟用 rate limiting。",
            "2. 啟用 MFA 或高風險登入驗證。",
            "3. 對異常來源提高監控。",
            "",
            "Follow-up:",
            "1. 若 failed_count 在短時間內升高，升級為 brute force / credential stuffing 調查。",
            "2. 比對其他使用者是否也受到同來源嘗試。",
            "3. 將確認過的來源與時間窗加入偵測規則。",
        ]

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

    def build_llm_suspicious_triage_report(self, original_input, llm_result, signals=None):
        attack_types = self._extract_llm_attack_types(llm_result)
        attack_type_text = ", ".join(attack_types) if attack_types else "None"
        detected_signals = self._format_detected_signals(signals, llm_result)
        final_risk, final_decision = self._derive_llm_suspicious_outcome(llm_result)
        reason = self._format_llm_suspicious_reason(llm_result, detected_signals)

        lines = [
            "[Security Triage Report]",
            "",
            "0. Quick Verdict",
            f"Verdict: This event is suspicious for {attack_type_text}.",
            f"Risk Level: {final_risk}",
            f"Decision: {final_decision}",
            f"Reason: {reason}",
            "",
            "1. Summary",
            "Status: SUSPICIOUS",
            f"Attack Type: {attack_type_text}",
            f"Risk Level: {final_risk}",
            f"Decision: {final_decision}",
            "Detection Source: llm_assist + signal_extraction",
            "",
            "2. Evidence",
            "Input / Event:",
            str(original_input or ""),
            "",
            "Detected Signals:",
        ]

        if detected_signals:
            lines.extend(f"- {signal}" for signal in detected_signals)
        else:
            lines.append("- None")

        lines.extend(["", "3. Why It Matters"])
        lines.extend(self._format_llm_suspicious_why_it_matters(attack_types))
        lines.extend(["", "4. Recommended Response"])
        lines.extend(self._format_llm_suspicious_response(attack_types))
        lines.extend(self._format_llm_simulation_notice())
        lines.extend(self._format_llm_suspicious_ai_assist(llm_result, attack_type_text))
        return "\n".join(lines).strip()

    def build_auth_failure_triage_report(self, normalized_event, agent_input):
        normalized_event = normalized_event or {}
        source_ip = self._format_auth_failure_value(normalized_event, "source_ip")
        user = self._format_auth_failure_value(normalized_event, "user")
        endpoint = self._format_auth_failure_value(normalized_event, "target")
        status = self._format_auth_failure_value(normalized_event, "status")

        lines = [
            "[Security Triage Report]",
            "",
            "0. Quick Verdict",
            "Verdict: This is a failed login event. A single failure is not enough to confirm brute force; monitor for repeated failures from the same source_ip, user, or endpoint.",
            "Risk Level: LOW",
            "Decision: MONITOR",
            "Reason: Single auth_failure event should be reviewed, but repeated-failure evidence is required before labeling it Brute Force or Credential Stuffing.",
            "",
            "1. Summary",
            "Status: REVIEW",
            "Attack Type: Authentication Failure",
            "Risk Level: LOW",
            "Decision: MONITOR",
            "Detection Source: raw_log_translation",
            "",
            "2. Evidence",
            f"Source IP: {source_ip}",
            f"User: {user}",
            f"Endpoint: {endpoint}",
            f"Status: {status}",
            "Converted SecurityAgent Input:",
            str(agent_input or ""),
            "",
            "3. Why It Matters",
            "- Authentication Failure: 單次登入失敗可能是使用者輸入錯誤或正常背景雜訊，但也可能是暴力破解、credential stuffing 或帳號接管的早期訊號；需要觀察同一 source_ip / user / endpoint 是否在短時間內重複失敗。",
            "",
            "4. Recommended Response",
        ]
        lines.extend(self._format_auth_failure_response())
        lines.extend(self._format_llm_simulation_notice())
        lines.extend(
            [
                "",
                "6. AI Assist",
                "LLM Suggested Attack Type: N/A",
                "LLM Suggested Decision: N/A",
                "Confidence: N/A",
                "Reasoning: Rule-free raw log translation identified a single auth_failure event; no LLM classification is required for this formatting path.",
                "Note: Decision above is the final system decision; LLM Suggested Decision is AI assist only.",
            ]
        )
        return "\n".join(lines).strip()

    def trigger_automated_defense(self, action):
        """
        Keep the original placeholder automation hook.
        """
        print(f"已觸發自動化防禦動作：{action}")
        return True
