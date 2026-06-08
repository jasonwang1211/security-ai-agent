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
    "control_panel": {
        "zh-TW": "輸入 / 控制面板",
        "en": "Input / Control Panel",
        "bilingual": "輸入 / 控制面板 / Input / Control Panel",
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
