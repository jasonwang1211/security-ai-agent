"""Pure language helper for the deterministic Fast-mode report.

This helper provides the fixed report headings, field labels, and explanatory
template text in Traditional Chinese, English, and a compact bilingual form.
It is presentation-text only:

- It does not change rule-based detection, risk scoring, decision logic, or any
  backend behavior.
- It must not import any UI rendering framework.
- The default language is English so existing report consumers that do not pass
  a language keep the exact prior wording.

Only fixed labels / headings / explanatory template text are translated.
Dynamic values (attack types, risk levels, decisions, rule IDs, source paths,
matched indicators, payload text) are inserted by the caller and never
translated here.
"""

from __future__ import annotations

DEFAULT_REPORT_LANGUAGE = "en"
SUPPORTED_REPORT_LANGUAGES = ("en", "zh-TW", "bilingual")

_SEPARATORS = {"en": ": ", "zh-TW": "：", "bilingual": "："}


def normalize_report_language(language: str | None) -> str:
    """Return a supported report language, defaulting to English."""

    text = str(language or "").strip()
    if text in SUPPORTED_REPORT_LANGUAGES:
        return text
    return DEFAULT_REPORT_LANGUAGE


def label_separator(language: str | None) -> str:
    """Return the label/value separator for the selected language."""

    return _SEPARATORS.get(normalize_report_language(language), ": ")


def report_text(key: str, language: str | None) -> str:
    """Return the fixed report text for a key in the selected language."""

    entry = _TEXT.get(key)
    if entry is None:
        return key
    lang = normalize_report_language(language)
    return entry.get(lang) or entry.get(DEFAULT_REPORT_LANGUAGE) or key


def labeled_line(label_key: str, value: str, language: str | None) -> str:
    """Compose ``label<sep>value`` using the language-aware label/separator."""

    return f"{report_text(label_key, language)}{label_separator(language)}{value}"


# All English values are kept verbatim to preserve existing report wording.
# Bilingual values use compact "zh / en" labels/headings, but keep explanatory
# free-text bodies in English to avoid full duplicated paragraphs.
_TEXT: dict[str, dict[str, str]] = {
    "report_title": {
        "en": "[Security Triage Report]",
        "zh-TW": "[資安分流報告]",
        "bilingual": "[資安分流報告 / Security Triage Report]",
    },
    "mode_label": {"en": "Mode", "zh-TW": "模式", "bilingual": "模式 / Mode"},
    "mode_value": {
        "en": "Fast Deterministic Mode",
        "zh-TW": "快速確定性模式",
        "bilingual": "快速確定性模式 / Fast Deterministic Mode",
    },
    "section_quick_verdict": {
        "en": "0. Quick Verdict",
        "zh-TW": "0. 快速判定",
        "bilingual": "0. 快速判定 / Quick Verdict",
    },
    "verdict_label": {"en": "Verdict", "zh-TW": "判定", "bilingual": "判定 / Verdict"},
    "risk_level_label": {
        "en": "Risk Level",
        "zh-TW": "風險等級",
        "bilingual": "風險等級 / Risk Level",
    },
    "decision_label": {"en": "Decision", "zh-TW": "決策", "bilingual": "決策 / Decision"},
    "reason_label": {"en": "Reason", "zh-TW": "原因", "bilingual": "原因 / Reason"},
    "section_summary": {
        "en": "1. Summary",
        "zh-TW": "1. 摘要",
        "bilingual": "1. 摘要 / Summary",
    },
    "status_label": {"en": "Status", "zh-TW": "狀態", "bilingual": "狀態 / Status"},
    "attack_type_label": {
        "en": "Attack Type",
        "zh-TW": "攻擊類型",
        "bilingual": "攻擊類型 / Attack Type",
    },
    "detection_source_label": {
        "en": "Detection Source",
        "zh-TW": "偵測來源",
        "bilingual": "偵測來源 / Detection Source",
    },
    "rule_ids_label": {"en": "Rule IDs", "zh-TW": "規則 ID", "bilingual": "規則 ID / Rule IDs"},
    "rule_sources_label": {
        "en": "Rule Sources",
        "zh-TW": "規則來源",
        "bilingual": "規則來源 / Rule Sources",
    },
    "section_evidence": {
        "en": "2. Evidence",
        "zh-TW": "2. 證據",
        "bilingual": "2. 證據 / Evidence",
    },
    "input_payload_heading": {
        "en": "Input / Payload:",
        "zh-TW": "輸入內容：",
        "bilingual": "輸入內容 / Input：",
    },
    "matched_signatures_heading": {
        "en": "Matched Signatures:",
        "zh-TW": "命中特徵：",
        "bilingual": "命中特徵 / Matched Signatures：",
    },
    "section_explanation": {
        "en": "3. Deterministic Explanation",
        "zh-TW": "3. 確定性說明",
        "bilingual": "3. 確定性說明 / Deterministic Explanation",
    },
    "explanation_line_1": {
        "en": "Fast mode used rule-based detection and deterministic policy only.",
        "zh-TW": "快速模式僅使用規則式偵測與確定性政策。",
        "bilingual": "Fast mode used rule-based detection and deterministic policy only.",
    },
    "explanation_line_2": {
        "en": "LLM Assist and expensive RAG explanation were skipped.",
        "zh-TW": "已略過 LLM Assist 與昂貴的 RAG 說明。",
        "bilingual": "LLM Assist and expensive RAG explanation were skipped.",
    },
    "explanation_line_3": {
        "en": "The final Risk Level and Decision remain deterministic.",
        "zh-TW": "最終的風險等級與決策維持確定性結果。",
        "bilingual": "The final Risk Level and Decision remain deterministic.",
    },
    "section_recommended": {
        "en": "4. Recommended Response",
        "zh-TW": "4. 建議處置",
        "bilingual": "4. 建議處置 / Recommended Response",
    },
    "immediate_actions_heading": {
        "en": "Immediate Actions:",
        "zh-TW": "立即行動：",
        "bilingual": "立即行動 / Immediate Actions：",
    },
    "immediate_action_1": {
        "en": "1. Preserve request, endpoint, source, timestamp, and application logs.",
        "zh-TW": "1. 保留請求、端點、來源、時間戳記與應用程式日誌。",
        "bilingual": "1. Preserve request, endpoint, source, timestamp, and application logs.",
    },
    "immediate_action_2": {
        "en": "2. Check process logs and audit logs for execution evidence.",
        "zh-TW": "2. 檢查程序日誌與稽核日誌中的執行證據。",
        "bilingual": "2. Check process logs and audit logs for execution evidence.",
    },
    "immediate_action_3": {
        "en": "3. Verify whether the payload reached command execution sinks.",
        "zh-TW": "3. 確認 payload 是否到達命令執行點。",
        "bilingual": "3. Verify whether the payload reached command execution sinks.",
    },
    "mitigation_heading": {
        "en": "Mitigation:",
        "zh-TW": "緩解措施：",
        "bilingual": "緩解措施 / Mitigation：",
    },
    "mitigation_1": {
        "en": "1. Avoid passing user input into shell commands.",
        "zh-TW": "1. 避免將使用者輸入傳入 shell 命令。",
        "bilingual": "1. Avoid passing user input into shell commands.",
    },
    "mitigation_2": {
        "en": "2. Use safe APIs instead of shell execution.",
        "zh-TW": "2. 使用安全 API 取代 shell 執行。",
        "bilingual": "2. Use safe APIs instead of shell execution.",
    },
    "mitigation_3": {
        "en": "3. Apply allowlist validation for command parameters.",
        "zh-TW": "3. 對命令參數套用允許清單驗證。",
        "bilingual": "3. Apply allowlist validation for command parameters.",
    },
    "section_simulation_notice": {
        "en": "5. Simulation Notice",
        "zh-TW": "5. 模擬決策聲明",
        "bilingual": "5. 模擬決策聲明 / Simulation Notice",
    },
    "simulation_boundary": {
        "en": (
            "BLOCK / MONITOR / ALLOW are simulated project decisions. No real firewall, "
            "WAF, EDR, account, password reset, monitoring deployment, or enforcement "
            "action was executed."
        ),
        "zh-TW": (
            "BLOCK / MONITOR / ALLOW 為專案模擬決策；未執行任何真實防火牆、WAF、EDR、"
            "帳號、密碼重設、監控部署或強制動作。"
        ),
        "bilingual": (
            "BLOCK / MONITOR / ALLOW are simulated project decisions. No real firewall, "
            "WAF, EDR, account, password reset, monitoring deployment, or enforcement "
            "action was executed."
        ),
    },
    "section_ai_assist": {
        "en": "6. AI Assist",
        "zh-TW": "6. AI 輔助",
        "bilingual": "6. AI 輔助 / AI Assist",
    },
    "ai_assist_line_1": {
        "en": "Skipped in Fast Deterministic Mode.",
        "zh-TW": "在快速確定性模式中略過。",
        "bilingual": "Skipped in Fast Deterministic Mode.",
    },
    "ai_assist_line_2": {
        "en": "LLM Assist is not used in fast mode.",
        "zh-TW": "快速模式不使用 LLM Assist。",
        "bilingual": "LLM Assist is not used in fast mode.",
    },
    "ai_assist_line_3": {
        "en": "Fast mode is for demo responsiveness, not production benchmarking.",
        "zh-TW": "快速模式用於展示反應速度，而非正式效能評測。",
        "bilingual": "Fast mode is for demo responsiveness, not production benchmarking.",
    },
    "simulated_decision_note_label": {
        "en": "Simulated Decision Note",
        "zh-TW": "模擬決策說明",
        "bilingual": "模擬決策說明 / Simulated Decision Note",
    },
    # Dynamic-text templates (caller fills the placeholders with backend values).
    "verdict_known": {
        "en": "This event is likely {attack}.",
        "zh-TW": "此事件可能為 {attack}。",
        "bilingual": "This event is likely {attack}.",
    },
    "verdict_unknown": {
        "en": "No known attack signature was confirmed.",
        "zh-TW": "未確認任何已知攻擊特徵。",
        "bilingual": "No known attack signature was confirmed.",
    },
    "reason_item": {
        "en": "Matched {attack} indicators: {indicators}",
        "zh-TW": "命中 {attack} 指標：{indicators}",
        "bilingual": "Matched {attack} indicators: {indicators}",
    },
    "reason_separator": {"en": "; ", "zh-TW": "；", "bilingual": "; "},
    "reason_empty": {
        "en": "No matched signature evidence was available.",
        "zh-TW": "無可用的特徵命中證據。",
        "bilingual": "No matched signature evidence was available.",
    },
    "none_value": {"en": "None", "zh-TW": "無", "bilingual": "None"},
    # --- Auth-log ingestion / structured authentication incident report ----
    "log_ingestion_title": {
        "en": "[Log Ingestion Summary]",
        "zh-TW": "[登入日誌匯入摘要]",
        "bilingual": "[登入日誌匯入摘要 / Log Ingestion Summary]",
    },
    "auth_incident_title": {
        "en": "[Structured Authentication Incident]",
        "zh-TW": "[結構化驗證事件]",
        "bilingual": "[結構化驗證事件 / Structured Authentication Incident]",
    },
    "file_label": {"en": "File", "zh-TW": "檔案", "bilingual": "檔案 / File"},
    "total_lines_label": {
        "en": "Total Lines",
        "zh-TW": "總行數",
        "bilingual": "總行數 / Total Lines",
    },
    "parsed_logs_label": {
        "en": "Parsed Logs",
        "zh-TW": "解析日誌數",
        "bilingual": "解析日誌數 / Parsed Logs",
    },
    "normalized_events_label": {
        "en": "Normalized Events",
        "zh-TW": "正規化事件數",
        "bilingual": "正規化事件數 / Normalized Events",
    },
    "aggregated_events_label": {
        "en": "Aggregated Events",
        "zh-TW": "聚合事件數",
        "bilingual": "聚合事件數 / Aggregated Events",
    },
    "detected_event_types_heading": {
        "en": "Detected Event Types:",
        "zh-TW": "偵測到的事件類型：",
        "bilingual": "偵測到的事件類型 / Detected Event Types：",
    },
    "current_stage_heading": {
        "en": "Current Stage:",
        "zh-TW": "目前階段：",
        "bilingual": "目前階段 / Current Stage：",
    },
    "agent_stage_line_1": {
        "en": "Log ingestion and deterministic authentication-incident correlation completed.",
        "zh-TW": "日誌匯入與確定性驗證事件關聯已完成。",
        "bilingual": "Log ingestion and deterministic authentication-incident correlation completed.",
    },
    "agent_stage_line_2": {
        "en": "Structured incident follow-up is available when an incident is detected.",
        "zh-TW": "偵測到事件時，可使用結構化事件追蹤。",
        "bilingual": "Structured incident follow-up is available when an incident is detected.",
    },
    "agent_stage_line_3": {
        "en": "Optional SecurityAgent analysis of aggregated events has not been run unless requested below.",
        "zh-TW": "除非下方明確要求，否則尚未執行 SecurityAgent 對聚合事件的選用分析。",
        "bilingual": (
            "Optional SecurityAgent analysis of aggregated events has not been run unless requested below."
        ),
    },
    "log_only_stage_line": {
        "en": "Log ingestion only. Events are not sent into SecurityAgent yet.",
        "zh-TW": "僅執行日誌匯入；事件尚未送入 SecurityAgent。",
        "bilingual": "Log ingestion only. Events are not sent into SecurityAgent yet.",
    },
    "aggregated_findings_heading": {
        "en": "Aggregated Findings:",
        "zh-TW": "聚合發現：",
        "bilingual": "聚合發現 / Aggregated Findings：",
    },
    "finding_event_type_label": {
        "en": "Event Type",
        "zh-TW": "事件類型",
        "bilingual": "事件類型 / Event Type",
    },
    "finding_source_ip_label": {
        "en": "Source IP",
        "zh-TW": "來源 IP",
        "bilingual": "來源 IP / Source IP",
    },
    "finding_target_label": {"en": "Target", "zh-TW": "目標", "bilingual": "目標 / Target"},
    "finding_failed_count_label": {
        "en": "Failed Count",
        "zh-TW": "失敗次數",
        "bilingual": "失敗次數 / Failed Count",
    },
    "finding_evidence_label": {
        "en": "Evidence",
        "zh-TW": "證據",
        "bilingual": "證據 / Evidence",
    },
    "preserved_payloads_heading": {
        "en": "Preserved Payloads:",
        "zh-TW": "保留的 Payload：",
        "bilingual": "保留的 Payload / Preserved Payloads：",
    },
    "incident_id_label": {
        "en": "Incident ID",
        "zh-TW": "事件 ID",
        "bilingual": "事件 ID / Incident ID",
    },
    "evidence_ids_label": {
        "en": "Evidence IDs",
        "zh-TW": "證據 ID",
        "bilingual": "證據 ID / Evidence IDs",
    },
    "finding_ids_label": {
        "en": "Finding IDs",
        "zh-TW": "Finding ID",
        "bilingual": "Finding ID / Finding IDs",
    },
    "auth_decision_note": {
        "en": (
            "(simulated decision; no real monitoring deployment, blocking, password "
            "reset, account disablement, or enforcement was executed.)"
        ),
        "zh-TW": "（模擬決策；未執行真實監控部署、封鎖、密碼重設、帳號停用或強制動作。）",
        "bilingual": (
            "(simulated decision; no real monitoring deployment, blocking, password "
            "reset, account disablement, or enforcement was executed.)"
        ),
    },
    "auth_failure_then_success_note": {
        "en": (
            "Failure-then-success authentication is suspicious, but it does not "
            "prove account takeover or intrusion by itself."
        ),
        "zh-TW": "登入失敗後成功的驗證模式具可疑性，但不能單獨證明帳號接管或入侵。",
        "bilingual": (
            "Failure-then-success authentication is suspicious, but it does not "
            "prove account takeover or intrusion by itself."
        ),
    },
    "auth_suggested_followup_label": {
        "en": "Suggested follow-up questions:",
        "zh-TW": "建議追問：",
        "bilingual": "建議追問 / Suggested follow-up questions:",
    },
}
