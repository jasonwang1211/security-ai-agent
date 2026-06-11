"""Pure internationalization helpers for the analyst console."""

from __future__ import annotations

DEFAULT_LANGUAGE = "zh-TW"
LANGUAGE_OPTIONS = ("zh-TW", "en", "bilingual")
STATE_LANGUAGE = "sentinel_ui_language"

_DISPLAY_NAMES = {
    "zh-TW": "繁體中文",
    "en": "English",
    "bilingual": "中英雙語",
}

CORE_UI_KEYS = (
    "header_title",
    "header_subtitle",
    "control_panel",
    "active_context",
    "analysis_group",
    "case_intelligence_group",
    "draft_export_group",
    "system_debug_group",
    "visual_relationship_graph",
    "case_draft",
    "export_report",
    "performance",
    "route_policy",
)

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "language_selector": {
        "zh-TW": "介面語言",
        "en": "Interface Language",
        "bilingual": "介面語言 / Interface Language",
    },
    "header_title": {
        "zh-TW": "Security AI Agent 控制台",
        "en": "Security AI Agent Console",
        "bilingual": "Security AI Agent 控制台 / Security AI Agent Console",
    },
    "header_subtitle": {
        "zh-TW": "AI 輔助安全分流展示，結合確定性偵測、核准相似案例檢索與需核准的案例草稿流程。",
        "en": "AI-assisted security triage demo with deterministic detection, approved similar-case retrieval, and approval-gated case draft workflow.",
        "bilingual": "AI 輔助安全分流展示 / AI-assisted security triage demo with deterministic detection, approved similar-case retrieval, and approval-gated case draft workflow.",
    },
    "simulated_boundary_caption": {
        "zh-TW": "BLOCK / MONITOR / ALLOW 是專案模擬決策；未執行任何真實防護動作。",
        "en": "BLOCK / MONITOR / ALLOW are simulated project decisions. No real enforcement is executed.",
        "bilingual": "BLOCK / MONITOR / ALLOW 是模擬決策 / simulated project decisions. No real enforcement is executed.",
    },
    "status_detector_ok": {
        "zh-TW": "偵測器正常",
        "en": "Detector OK",
        "bilingual": "偵測器正常 / Detector OK",
    },
    "status_similar_case_ready": {
        "zh-TW": "相似案例就緒",
        "en": "Similar Case ready",
        "bilingual": "相似案例就緒 / Similar Case ready",
    },
    "status_draft_gated": {
        "zh-TW": "草稿需核准",
        "en": "Draft approval-gated",
        "bilingual": "草稿需核准 / Draft approval-gated",
    },
    "console_mode_label": {
        "zh-TW": "模式",
        "en": "Mode",
        "bilingual": "模式 / Mode",
    },
    "console_active_label": {
        "zh-TW": "目前脈絡",
        "en": "Active",
        "bilingual": "目前脈絡 / Active",
    },
    "console_latest_label": {
        "zh-TW": "最近",
        "en": "Latest",
        "bilingual": "最近 / Latest",
    },
    "no_active_short": {
        "zh-TW": "無",
        "en": "None",
        "bilingual": "無 / None",
    },
    "control_panel": {
        "zh-TW": "輸入 / 控制面板",
        "en": "Input / Control Panel",
        "bilingual": "輸入 / 控制面板 / Input / Control Panel",
    },
    "demo_scenario_launcher": {
        "zh-TW": "示範情境啟動器",
        "en": "Demo Scenario Launcher",
        "bilingual": "示範情境啟動器 / Demo Scenario Launcher",
    },
    "load_scenario": {
        "zh-TW": "載入情境",
        "en": "Load Scenario",
        "bilingual": "載入情境 / Load Scenario",
    },
    "input_preview": {
        "zh-TW": "輸入預覽",
        "en": "Input Preview",
        "bilingual": "輸入預覽 / Input Preview",
    },
    "expected": {
        "zh-TW": "預期",
        "en": "Expected",
        "bilingual": "預期 / Expected",
    },
    "suggested_next": {
        "zh-TW": "建議下一步",
        "en": "Suggested Next",
        "bilingual": "建議下一步 / Suggested Next",
    },
    "suggested_next_none": {
        "zh-TW": "無",
        "en": "None",
        "bilingual": "無 / None",
    },
    "loaded_scenario": {
        "zh-TW": "已載入情境",
        "en": "Loaded scenario",
        "bilingual": "已載入情境 / Loaded scenario",
    },
    "scenario_command_injection_title": {
        "zh-TW": "命令注入示範",
        "en": "Command Injection Demo",
        "bilingual": "命令注入示範 / Command Injection Demo",
    },
    "scenario_command_injection_desc": {
        "zh-TW": "含 shell 串接符號的可疑命令輸入。",
        "en": "Suspicious command input with shell chaining metacharacters.",
        "bilingual": "含 shell 串接符號的可疑命令 / Suspicious command with shell chaining.",
    },
    "scenario_sql_injection_title": {
        "zh-TW": "SQL 注入示範",
        "en": "SQL Injection Demo",
        "bilingual": "SQL 注入示範 / SQL Injection Demo",
    },
    "scenario_sql_injection_desc": {
        "zh-TW": "查詢字串中的恆真條件 SQL 注入樣態。",
        "en": "Tautology-style SQL injection in a query string.",
        "bilingual": "恆真條件 SQL 注入 / Tautology-style SQL injection.",
    },
    "scenario_http2_resource_exhaustion_title": {
        "zh-TW": "HTTP/2 資源耗盡疑似事件",
        "en": "HTTP/2 Resource Exhaustion Suspicion",
        "bilingual": "HTTP/2 資源耗盡疑似事件 / HTTP/2 Resource Exhaustion Suspicion",
    },
    "scenario_http2_resource_exhaustion_desc": {
        "zh-TW": "合成遙測摘要：低流量卻伴隨伺服端資源壓力，供分析師安全複核。",
        "en": "Synthetic telemetry summary for a suspected case where low inbound traffic correlates with server-side resource pressure.",
        "bilingual": "合成遙測摘要 / Synthetic telemetry summary for suspected server-side resource pressure.",
    },
    "scenario_http2_resource_exhaustion_preview": {
        "zh-TW": (
            "摘要：合成 HTTP/2 資源耗盡疑似事件\n"
            "重點：低請求量 + worker/resource pressure\n"
            "跡象：stream reset / long-lived connection telemetry\n"
            "邊界：no traffic generated / no real enforcement / human review required"
        ),
        "en": (
            "Summary: Synthetic HTTP/2 resource exhaustion suspicion\n"
            "Signals: low request volume + worker/resource pressure\n"
            "Telemetry: stream reset / long-lived connection pattern\n"
            "Boundary: no traffic generated / no real enforcement / human review required"
        ),
        "bilingual": (
            "摘要 / Summary：合成 HTTP/2 資源耗盡疑似事件 / "
            "synthetic HTTP/2 resource exhaustion suspicion\n"
            "重點 / Signals：低請求量 + worker/resource pressure\n"
            "跡象 / Telemetry：stream reset / long-lived connection pattern\n"
            "邊界 / Boundary：no traffic generated / no real enforcement / human review required"
        ),
    },
    "scenario_auth_incident_title": {
        "zh-TW": "身分驗證事件示範",
        "en": "Authentication Incident Demo",
        "bilingual": "身分驗證事件示範 / Authentication Incident Demo",
    },
    "scenario_auth_incident_desc": {
        "zh-TW": "登入失敗後成功的混合驗證日誌檔。",
        "en": "Mixed auth log with success after repeated failures.",
        "bilingual": "登入失敗後成功的日誌 / Auth log with success after failures.",
    },
    "analysis_mode": {
        "zh-TW": "分析模式",
        "en": "Analysis Mode",
        "bilingual": "分析模式 / Analysis Mode",
    },
    "input": {
        "zh-TW": "輸入",
        "en": "Input",
        "bilingual": "輸入 / Input",
    },
    "run_input": {
        "zh-TW": "執行輸入",
        "en": "Run input",
        "bilingual": "執行輸入 / Run input",
    },
    "find_similar_cases": {
        "zh-TW": "尋找相似案例",
        "en": "Find Similar Cases",
        "bilingual": "尋找相似案例 / Find Similar Cases",
    },
    "clear_context": {
        "zh-TW": "清除脈絡",
        "en": "Clear Context",
        "bilingual": "清除脈絡 / Clear Context",
    },
    "fast_deterministic_mode": {
        "zh-TW": "快速確定性",
        "en": "Fast deterministic",
        "bilingual": "快速確定性 / Fast deterministic",
    },
    "full_ai_assisted_mode": {
        "zh-TW": "完整 AI 輔助",
        "en": "Full AI-assisted",
        "bilingual": "完整 AI 輔助 / Full AI-assisted",
    },
    "fast_mode_note": {
        "zh-TW": "快速確定性模式使用規則偵測與確定性政策，並略過選用的 AI/RAG 說明層。",
        "en": "Fast deterministic mode uses rule-based detection and deterministic policy, then skips optional AI/RAG explanation layers.",
        "bilingual": "快速確定性模式使用規則偵測 / Fast deterministic mode uses rule-based detection and deterministic policy, then skips optional AI/RAG explanation layers.",
    },
    "full_mode_note": {
        "zh-TW": "完整 AI 輔助模式保留既有 orchestrator / SecurityAgent 路徑。",
        "en": "Full AI-assisted mode preserves the existing orchestrator / SecurityAgent path.",
        "bilingual": "完整 AI 輔助模式保留既有路徑 / Full AI-assisted mode preserves the existing orchestrator / SecurityAgent path.",
    },
    "shared_mode_boundary_note": {
        "zh-TW": "Risk Level 與 Decision 仍為確定性結果；未執行任何真實防護動作。",
        "en": "Risk Level and Decision remain deterministic; no real enforcement is executed.",
        "bilingual": "Risk Level 與 Decision 仍為確定性結果 / remain deterministic; no real enforcement is executed.",
    },
    "full_mode_warmup_note": {
        "zh-TW": "完整 AI 輔助模式會執行 AI/RAG 說明層；首次執行可能需要 30～60 秒載入模型。",
        "en": "Full AI-assisted mode runs the AI/RAG explanation layer. First run may take 30–60 seconds while models warm up.",
        "bilingual": "完整 AI 輔助會執行 AI/RAG 說明層 / runs the AI/RAG explanation layer; first run may take 30–60s while models warm up.",
    },
    "mode_banner_full": {
        "zh-TW": "完整 AI 輔助：已執行 AI/RAG 說明層",
        "en": "Full AI-assisted: AI/RAG explanation layer executed",
        "bilingual": "完整 AI 輔助：已執行 AI/RAG 說明層 / Full AI-assisted: AI/RAG explanation layer executed",
    },
    "mode_banner_fast": {
        "zh-TW": "快速確定性：規則式偵測與確定性決策",
        "en": "Fast deterministic: rule-based detection and deterministic decision",
        "bilingual": "快速確定性：規則式偵測與確定性決策 / Fast deterministic: rule-based detection and deterministic decision",
    },
    "mode_banner_advisory": {
        "zh-TW": "AI/RAG 說明僅供參考，不會覆蓋 Risk Level 或 Decision",
        "en": "AI/RAG explanation is advisory and does not override Risk Level or Decision",
        "bilingual": "AI/RAG 說明僅供參考 / advisory; does not override Risk Level or Decision",
    },
    "ai_rag_assisted_badge": {
        "zh-TW": "AI/RAG 輔助",
        "en": "AI/RAG assisted",
        "bilingual": "AI/RAG 輔助 / AI/RAG assisted",
    },
    "active_context": {
        "zh-TW": "目前脈絡",
        "en": "Active Context",
        "bilingual": "目前脈絡 / Active Context",
    },
    "no_active_context": {
        "zh-TW": "尚無目前脈絡。請執行輸入或載入日誌開始。",
        "en": "No active context yet. Run an input or load a log to begin.",
        "bilingual": "尚無目前脈絡 / No active context yet. Run an input or load a log to begin.",
    },
    "context": {
        "zh-TW": "脈絡",
        "en": "Context",
        "bilingual": "脈絡 / Context",
    },
    "risk_level": {
        "zh-TW": "風險等級",
        "en": "Risk Level",
        "bilingual": "風險等級 / Risk Level",
    },
    "decision": {
        "zh-TW": "決策",
        "en": "Decision",
        "bilingual": "決策 / Decision",
    },
    "simulated_decision": {
        "zh-TW": "模擬決策",
        "en": "Simulated Decision",
        "bilingual": "模擬決策 / Simulated Decision",
    },
    "attack_incident": {
        "zh-TW": "攻擊 / 事件",
        "en": "Attack / Incident",
        "bilingual": "攻擊 / 事件 / Attack / Incident",
    },
    "rules_evidence": {
        "zh-TW": "規則 / 證據",
        "en": "Rules / Evidence",
        "bilingual": "規則 / 證據 / Rules / Evidence",
    },
    "context_details": {
        "zh-TW": "脈絡細節",
        "en": "Context details",
        "bilingual": "脈絡細節 / Context details",
    },
    "analysis_group": {
        "zh-TW": "分析",
        "en": "Analysis",
        "bilingual": "分析 / Analysis",
    },
    "case_intelligence_group": {
        "zh-TW": "案例情報",
        "en": "Case Intelligence",
        "bilingual": "案例情報 / Case Intelligence",
    },
    "draft_export_group": {
        "zh-TW": "草稿 / 匯出",
        "en": "Draft / Export",
        "bilingual": "草稿 / 匯出 / Draft / Export",
    },
    "system_debug_group": {
        "zh-TW": "系統 / 除錯",
        "en": "System / Debug",
        "bilingual": "系統 / 除錯 / System / Debug",
    },
    "analysis_report": {
        "zh-TW": "分析報告",
        "en": "Analysis Report",
        "bilingual": "分析報告 / Analysis Report",
    },
    "safety_boundary": {
        "zh-TW": "安全邊界",
        "en": "Safety Boundary",
        "bilingual": "安全邊界 / Safety Boundary",
    },
    "raw_output": {
        "zh-TW": "原始輸出",
        "en": "Raw Output",
        "bilingual": "原始輸出 / Raw Output",
    },
    "approved_similar_cases": {
        "zh-TW": "核准相似案例",
        "en": "Approved Similar Cases",
        "bilingual": "核准相似案例 / Approved Similar Cases",
    },
    "graph_relations": {
        "zh-TW": "圖形關係",
        "en": "Graph Relations",
        "bilingual": "圖形關係 / Graph Relations",
    },
    "case_memory": {
        "zh-TW": "案例記憶",
        "en": "Case Memory",
        "bilingual": "案例記憶 / Case Memory",
    },
    "case_draft": {
        "zh-TW": "案例草稿",
        "en": "Case Draft",
        "bilingual": "案例草稿 / Case Draft",
    },
    "export_report": {
        "zh-TW": "匯出報告",
        "en": "Export Report",
        "bilingual": "匯出報告 / Export Report",
    },
    "performance": {
        "zh-TW": "效能",
        "en": "Performance",
        "bilingual": "效能 / Performance",
    },
    "route_policy": {
        "zh-TW": "路由 / 政策",
        "en": "Route / Policy",
        "bilingual": "路由 / 政策 / Route / Policy",
    },
    "visual_relationship_graph": {
        "zh-TW": "視覺關係圖",
        "en": "Visual Relationship Graph",
        "bilingual": "視覺關係圖 / Visual Relationship Graph",
    },
    "graph_legend": {
        "zh-TW": "圖例",
        "en": "Graph Legend",
        "bilingual": "圖例 / Graph Legend",
    },
    "key_relationship_summary": {
        "zh-TW": "關鍵關係摘要",
        "en": "Key Relationship Summary",
        "bilingual": "關鍵關係摘要 / Key Relationship Summary",
    },
    "graph_notes": {
        "zh-TW": "圖形說明",
        "en": "Graph Notes",
        "bilingual": "圖形說明 / Graph Notes",
    },
    "dot_source": {
        "zh-TW": "DOT 原始碼",
        "en": "DOT Source",
        "bilingual": "DOT 原始碼 / DOT Source",
    },
    "fallback_dot_graphviz": {
        "zh-TW": "備援 DOT / Graphviz 圖",
        "en": "Fallback DOT / Graphviz",
        "bilingual": "備援 DOT / Graphviz / Fallback DOT / Graphviz",
    },
    "text_relationship_explanation": {
        "zh-TW": "文字關係說明",
        "en": "Text Relationship Explanation",
        "bilingual": "文字關係說明 / Text Relationship Explanation",
    },
    "request_draft": {
        "zh-TW": "要求草稿",
        "en": "Request Draft",
        "bilingual": "要求草稿 / Request Draft",
    },
    "approve_draft": {
        "zh-TW": "核准草稿",
        "en": "Approve Draft",
        "bilingual": "核准草稿 / Approve Draft",
    },
    "cancel_draft": {
        "zh-TW": "取消草稿",
        "en": "Cancel Draft",
        "bilingual": "取消草稿 / Cancel Draft",
    },
    "status": {
        "zh-TW": "狀態",
        "en": "Status",
        "bilingual": "狀態 / Status",
    },
    "pending_approval": {
        "zh-TW": "等待核准",
        "en": "Pending Approval",
        "bilingual": "等待核准 / Pending Approval",
    },
    "draft_path": {
        "zh-TW": "草稿路徑",
        "en": "Draft Path",
        "bilingual": "草稿路徑 / Draft Path",
    },
    "no_draft_file_path": {
        "zh-TW": "沒有草稿檔案路徑。",
        "en": "No draft file path.",
        "bilingual": "沒有草稿檔案路徑 / No draft file path.",
    },
    "download_markdown_report": {
        "zh-TW": "下載 Markdown 報告",
        "en": "Download Markdown Report",
        "bilingual": "下載 Markdown 報告 / Download Markdown Report",
    },
    "markdown_preview": {
        "zh-TW": "Markdown 預覽",
        "en": "Markdown Preview",
        "bilingual": "Markdown 預覽 / Markdown Preview",
    },
    "safety_notes": {
        "zh-TW": "安全說明",
        "en": "Safety Notes",
        "bilingual": "安全說明 / Safety Notes",
    },
    "latest_action": {
        "zh-TW": "最近動作",
        "en": "Latest Action",
        "bilingual": "最近動作 / Latest Action",
    },
    "selected_skill": {
        "zh-TW": "選取技能",
        "en": "Selected Skill",
        "bilingual": "選取技能 / Selected Skill",
    },
    "elapsed": {
        "zh-TW": "耗時",
        "en": "Elapsed",
        "bilingual": "耗時 / Elapsed",
    },
    "output_kind": {
        "zh-TW": "輸出類型",
        "en": "Output Kind",
        "bilingual": "輸出類型 / Output Kind",
    },
    "timestamp": {
        "zh-TW": "時間戳記",
        "en": "Timestamp",
        "bilingual": "時間戳記 / Timestamp",
    },
    "started_at": {
        "zh-TW": "開始時間",
        "en": "Started At",
        "bilingual": "開始時間 / Started At",
    },
    "ended_at": {
        "zh-TW": "結束時間",
        "en": "Ended At",
        "bilingual": "結束時間 / Ended At",
    },
    "latest_input": {
        "zh-TW": "最近輸入",
        "en": "Latest Input",
        "bilingual": "最近輸入 / Latest Input",
    },
    "no_input_recorded": {
        "zh-TW": "尚未記錄輸入命令。",
        "en": "No input command recorded.",
        "bilingual": "尚未記錄輸入命令 / No input command recorded.",
    },
    "notes": {
        "zh-TW": "說明",
        "en": "Notes",
        "bilingual": "說明 / Notes",
    },
    "permission": {
        "zh-TW": "權限",
        "en": "Permission",
        "bilingual": "權限 / Permission",
    },
    "execution_mode": {
        "zh-TW": "執行模式",
        "en": "Execution Mode",
        "bilingual": "執行模式 / Execution Mode",
    },
    "route_reason": {
        "zh-TW": "路由原因",
        "en": "Route Reason",
        "bilingual": "路由原因 / Route Reason",
    },
    "human_approval_required": {
        "zh-TW": "需要人工核准",
        "en": "Human Approval Required",
        "bilingual": "需要人工核准 / Human Approval Required",
    },
    "write_behavior": {
        "zh-TW": "寫入行為",
        "en": "Write Behavior",
        "bilingual": "寫入行為 / Write Behavior",
    },
    "approved_seeds": {
        "zh-TW": "核准種子",
        "en": "Approved Seeds",
        "bilingual": "核准種子 / Approved Seeds",
    },
    "approved_for_retrieval": {
        "zh-TW": "允許檢索",
        "en": "Approved For Retrieval",
        "bilingual": "允許檢索 / Approved For Retrieval",
    },
    "source_directory": {
        "zh-TW": "來源目錄",
        "en": "Source Directory",
        "bilingual": "來源目錄 / Source Directory",
    },
    "boundary_notes": {
        "zh-TW": "邊界說明",
        "en": "Boundary Notes",
        "bilingual": "邊界說明 / Boundary Notes",
    },
    "no_approved_case_seeds": {
        "zh-TW": "未載入核准案例種子。",
        "en": "No approved case seeds loaded.",
        "bilingual": "未載入核准案例種子 / No approved case seeds loaded.",
    },
    "metadata": {
        "zh-TW": "中繼資料",
        "en": "Metadata",
        "bilingual": "中繼資料 / Metadata",
    },
    "matched_fields": {
        "zh-TW": "符合欄位",
        "en": "Matched Fields",
        "bilingual": "符合欄位 / Matched Fields",
    },
    "summary": {
        "zh-TW": "摘要",
        "en": "Summary",
        "bilingual": "摘要 / Summary",
    },
    "key_facts": {
        "zh-TW": "關鍵事實",
        "en": "Key Facts",
        "bilingual": "關鍵事實 / Key Facts",
    },
    "investigation_notes": {
        "zh-TW": "調查說明",
        "en": "Investigation Notes",
        "bilingual": "調查說明 / Investigation Notes",
    },
    "differences_to_check": {
        "zh-TW": "需檢查差異",
        "en": "Differences To Check",
        "bilingual": "需檢查差異 / Differences To Check",
    },
    "analyst_conclusion": {
        "zh-TW": "分析師結論",
        "en": "Analyst Conclusion",
        "bilingual": "分析師結論 / Analyst Conclusion",
    },
    "outcome": {
        "zh-TW": "結果",
        "en": "Outcome",
        "bilingual": "結果 / Outcome",
    },
    "no_analysis_report": {
        "zh-TW": "尚無分析報告。",
        "en": "No analysis report yet.",
        "bilingual": "尚無分析報告 / No analysis report yet.",
    },
    "no_approved_similar_cases": {
        "zh-TW": "尚無核准相似案例。",
        "en": "No approved similar cases yet.",
        "bilingual": "尚無核准相似案例 / No approved similar cases yet.",
    },
    "no_output": {
        "zh-TW": "尚無輸出。",
        "en": "No output yet.",
        "bilingual": "尚無輸出 / No output yet.",
    },
    "no_dot_source": {
        "zh-TW": "尚無 DOT 原始碼。",
        "en": "No DOT source yet.",
        "bilingual": "尚無 DOT 原始碼 / No DOT source yet.",
    },
    "no_graph_relationship": {
        "zh-TW": "尚無圖形關係說明。",
        "en": "No graph-grounded relationship explanation yet.",
        "bilingual": "尚無圖形關係說明 / No graph-grounded relationship explanation yet.",
    },
    "no_relationship_summary": {
        "zh-TW": "尚無核准相似案例關係摘要。",
        "en": "No approved similar-case relationship summary yet.",
        "bilingual": "尚無核准相似案例關係摘要 / No approved similar-case relationship summary yet.",
    },
    "analysis_group_caption": {
        "zh-TW": "主要分流輸出、安全邊界與原始輸出附錄。",
        "en": "Primary triage output, safety boundary, and raw output appendix.",
        "bilingual": "主要分流輸出 / Primary triage output, safety boundary, and raw output appendix.",
    },
    "case_intelligence_caption": {
        "zh-TW": "核准案例參考與關係說明僅供參考。",
        "en": "Approved case references and relationship explanations are advisory only.",
        "bilingual": "核准案例參考僅供參考 / Approved case references and relationship explanations are advisory only.",
    },
    "draft_export_caption": {
        "zh-TW": "草稿擷取仍需核准；匯出仍為記憶體內操作。",
        "en": "Draft capture remains approval-gated; export remains in-memory.",
        "bilingual": "草稿需核准、匯出不寫檔 / Draft capture remains approval-gated; export remains in-memory.",
    },
    "system_debug_caption": {
        "zh-TW": "診斷計時與確定性路由 / 政策資訊。",
        "en": "System / Debug contains diagnostic/debug information.",
        "bilingual": "診斷資訊 / System / Debug contains diagnostic/debug information.",
    },
    "safety_boundary_caption": {
        "zh-TW": "每次執行都會顯示模擬與權限邊界。",
        "en": "Simulation and authority boundaries remain visible for every run.",
        "bilingual": "模擬與權限邊界固定顯示 / Simulation and authority boundaries remain visible for every run.",
    },
    "ai_analyst_group": {
        "zh-TW": "AI 分析助理",
        "en": "AI Analyst",
        "bilingual": "AI 分析助理 / AI Analyst",
    },
    "followup_assistant": {
        "zh-TW": "追問助理",
        "en": "Follow-up Assistant",
        "bilingual": "追問助理 / Follow-up Assistant",
    },
    "knowledge_qa": {
        "zh-TW": "知識問答",
        "en": "Knowledge Q&A",
        "bilingual": "知識問答 / Knowledge Q&A",
    },
    "ai_analyst_caption": {
        "zh-TW": "AI / RAG 提供解釋與分析師情境，不會覆蓋確定性的 Risk Level 或 Decision。",
        "en": "AI / RAG provides explanation and analyst context; it never overrides the deterministic Risk Level or Decision.",
        "bilingual": "AI / RAG 提供解釋與情境 / provides explanation and context; it never overrides the deterministic Risk Level or Decision.",
    },
    "ai_analyst_empty": {
        "zh-TW": "先執行一個示範情境，AI 分析助理會根據目前事件提供追問與解釋。",
        "en": "Run a demo scenario first. The AI analyst will explain the current event context.",
        "bilingual": "先執行一個示範情境 / Run a demo scenario first. The AI analyst will explain the current event context.",
    },
    "ai_suggested_questions": {
        "zh-TW": "建議追問",
        "en": "Suggested questions",
        "bilingual": "建議追問 / Suggested questions",
    },
    "ask_ai_analyst": {
        "zh-TW": "詢問 AI 分析助理",
        "en": "Ask AI Analyst",
        "bilingual": "詢問 AI 分析助理 / Ask AI Analyst",
    },
    "ai_submit_question": {
        "zh-TW": "送出問題",
        "en": "Ask",
        "bilingual": "送出問題 / Ask",
    },
    "ai_response_heading": {
        "zh-TW": "AI 回覆",
        "en": "AI Response",
        "bilingual": "AI 回覆 / AI Response",
    },
    "ai_no_response": {
        "zh-TW": "尚無 AI 回覆。",
        "en": "No AI response yet.",
        "bilingual": "尚無 AI 回覆 / No AI response yet.",
    },
    "ai_badge_followup": {
        "zh-TW": "確定性追問",
        "en": "Deterministic follow-up",
        "bilingual": "確定性追問 / Deterministic follow-up",
    },
    "ai_badge_knowledge": {
        "zh-TW": "RAG / 知識問答",
        "en": "RAG / Knowledge Q&A",
        "bilingual": "RAG / 知識問答 / Knowledge Q&A",
    },
    "ai_advisory_boundary": {
        "zh-TW": "AI / RAG 回覆僅供分析師參考，不會覆蓋目前事件的 Risk Level 或 Decision。",
        "en": "AI/RAG output is advisory analyst context and does not override the current Risk Level or Decision.",
        "bilingual": "AI / RAG 回覆僅供分析師參考 / advisory analyst context; it does not override the current Risk Level or Decision.",
    },
    "ai_safety_note": {
        "zh-TW": "AI 不偵測攻擊、不決定最終風險或決策、不執行任何防護動作；僅提供解釋與情境。",
        "en": "The AI does not detect attacks, decide the final risk/decision, or execute enforcement; it only explains and adds context.",
        "bilingual": "AI 不偵測攻擊、不決定風險/決策、不執行防護動作 / it only explains and adds context.",
    },
    "ai_advisory_only": {
        "zh-TW": "僅供參考",
        "en": "Advisory only",
        "bilingual": "僅供參考 / Advisory only",
    },
    "ai_followup_panel_caption": {
        "zh-TW": "使用目前 active context 解釋事件為何被如此判定；為確定性追問，不會用來覆蓋 Risk Level 或 Decision。",
        "en": "Explains the current active context — why the event was classified this way. Deterministic follow-up; it does not override Risk Level or Decision.",
        "bilingual": "使用目前 active context 解釋判定原因 / explains the current active context; deterministic follow-up, it does not override Risk Level or Decision.",
    },
    "ai_knowledge_empty": {
        "zh-TW": "目前知識庫沒有足夠內容回答這題；請改問已收錄的攻擊類型，例如 Command Injection、SQL Injection、XSS、CSRF。",
        "en": "The knowledge base doesn't have enough content for this question yet. Try a covered attack type, e.g. Command Injection, SQL Injection, XSS, or CSRF.",
        "bilingual": "目前知識庫沒有足夠內容回答這題 / not enough knowledge content yet; try a covered attack type, e.g. Command Injection, SQL Injection, XSS, or CSRF.",
    },
    "knowledge_qa_caption": {
        "zh-TW": "搜尋資安知識庫（RAG）；僅供參考，若知識庫沒有相關內容可能不會有答案。",
        "en": "Searches the security knowledge base (RAG); advisory only — it may return no answer if the knowledge base lacks content.",
        "bilingual": "搜尋資安知識庫（RAG）/ searches the security knowledge base; advisory only, may return no answer if content is missing.",
    },
    "knowledge_qa_input": {
        "zh-TW": "詢問資安知識問題",
        "en": "Ask a security knowledge question",
        "bilingual": "詢問資安知識問題 / Ask a security knowledge question",
    },
    "ai_analyst_brief_panel_title": {
        "zh-TW": "AI 分析摘要",
        "en": "AI Analyst Brief",
        "bilingual": "AI 分析摘要 / AI Analyst Brief",
    },
    "ai_analyst_brief_panel_subtitle": {
        "zh-TW": "確定性建議情境，彙整規則式結果、證據缺口與下一步複核建議；這不是最終判決。",
        "en": "Deterministic advisory context summarizing rule-based results, evidence gaps, and next review steps. It is not a final verdict.",
        "bilingual": "確定性建議情境 / deterministic advisory context summarizing rule-based results, evidence gaps, and next review steps; not a final verdict.",
    },
    "ai_analyst_brief_empty": {
        "zh-TW": "請先執行一次分析，才能產生 AI 分析摘要。",
        "en": "Run an analysis first to generate an AI Analyst Brief.",
        "bilingual": "請先執行一次分析 / Run an analysis first to generate an AI Analyst Brief.",
    },
    "ai_analyst_brief_chip": {
        "zh-TW": "確定性 AI 建議 · 未使用 LLM",
        "en": "Deterministic AI advisory · no LLM",
        "bilingual": "確定性 AI 建議 / Deterministic AI advisory · no LLM",
    },
    "ai_analyst_brief_what_happened": {
        "zh-TW": "發生了什麼",
        "en": "What happened",
        "bilingual": "發生了什麼 / What happened",
    },
    "ai_analyst_brief_why_it_matters": {
        "zh-TW": "為什麼重要",
        "en": "Why it matters",
        "bilingual": "為什麼重要 / Why it matters",
    },
    "ai_analyst_brief_deterministic_verdict": {
        "zh-TW": "確定性判定",
        "en": "Deterministic verdict",
        "bilingual": "確定性判定 / Deterministic verdict",
    },
    "ai_analyst_brief_advisory_summary": {
        "zh-TW": "建議摘要",
        "en": "Advisory summary",
        "bilingual": "建議摘要 / Advisory summary",
    },
    "ai_analyst_brief_evidence_gap": {
        "zh-TW": "證據缺口摘要",
        "en": "Evidence gap summary",
        "bilingual": "證據缺口摘要 / Evidence gap summary",
    },
    "ai_analyst_brief_next_steps": {
        "zh-TW": "建議下一步",
        "en": "Recommended next steps",
        "bilingual": "建議下一步 / Recommended next steps",
    },
    "ai_analyst_brief_unsafe": {
        "zh-TW": "不安全的假設",
        "en": "Unsafe assumptions",
        "bilingual": "不安全的假設 / Unsafe assumptions",
    },
    "evidence_gap_panel_title": {
        "zh-TW": "證據缺口分析",
        "en": "Evidence Gap Analyzer",
        "bilingual": "證據缺口分析 / Evidence Gap Analyzer",
    },
    "evidence_gap_panel_subtitle": {
        "zh-TW": "確定性建議情境，協助判斷還缺哪些證據；這不是判決，也不會覆蓋 Risk Level 或 Decision。",
        "en": "Deterministic advisory context to help decide what evidence is still needed. It is not a verdict and does not override Risk Level or Decision.",
        "bilingual": "確定性建議情境 / deterministic advisory context; not a verdict and does not override Risk Level or Decision.",
    },
    "evidence_gap_empty": {
        "zh-TW": "請先執行一次分析，才能產生證據缺口建議情境。",
        "en": "Run an analysis first to generate evidence-gap advisory context.",
        "bilingual": "請先執行一次分析 / Run an analysis first to generate evidence-gap advisory context.",
    },
    "evidence_gap_confirmed": {
        "zh-TW": "已確認事實",
        "en": "Confirmed facts",
        "bilingual": "已確認事實 / Confirmed facts",
    },
    "evidence_gap_missing": {
        "zh-TW": "缺少的證據",
        "en": "Missing evidence",
        "bilingual": "缺少的證據 / Missing evidence",
    },
    "evidence_gap_checks": {
        "zh-TW": "建議檢查",
        "en": "Recommended checks",
        "bilingual": "建議檢查 / Recommended checks",
    },
    "evidence_gap_unsafe": {
        "zh-TW": "不安全的假設",
        "en": "Unsafe assumptions",
        "bilingual": "不安全的假設 / Unsafe assumptions",
    },
    "evidence_gap_advisory_chip": {
        "zh-TW": "確定性建議 · 未使用 LLM",
        "en": "Deterministic advisory · no LLM",
        "bilingual": "確定性建議 / Deterministic advisory · no LLM",
    },
}


def normalize_language(value: str | None) -> str:
    """Return a supported language code, defaulting to Traditional Chinese."""

    text = str(value or "").strip()
    if text in LANGUAGE_OPTIONS:
        return text
    return language_from_display_name(text) if text in _DISPLAY_NAMES.values() else DEFAULT_LANGUAGE


def language_display_name(value: str) -> str:
    """Return the display name for a language code."""

    return _DISPLAY_NAMES.get(normalize_language(value), _DISPLAY_NAMES[DEFAULT_LANGUAGE])


def language_display_options() -> tuple[str, ...]:
    """Return language display names in supported option order."""

    return tuple(_DISPLAY_NAMES[language] for language in LANGUAGE_OPTIONS)


def language_from_display_name(value: str | None) -> str:
    """Return a language code from a display name or supported code."""

    text = str(value or "").strip()
    if text in LANGUAGE_OPTIONS:
        return text
    for language, display_name in _DISPLAY_NAMES.items():
        if text == display_name:
            return language
    return DEFAULT_LANGUAGE


def t(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Translate a fixed UI key with a safe key fallback."""

    values = _TRANSLATIONS.get(key)
    if values is None:
        return key
    normalized = normalize_language(language)
    return values.get(normalized) or values.get(DEFAULT_LANGUAGE) or key
