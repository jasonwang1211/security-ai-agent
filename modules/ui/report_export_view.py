"""Pure Markdown report export helpers for the Streamlit analyst console.

Fixed wrapper text (section headings, human-review warning, export safety
notes, and the markdown safety-boundary lines) is language-aware. Dynamic
backend-derived content (analysis body, similar-case text, graph explanation,
raw output, case IDs, risk/decision values, file paths, payload text) is never
translated. The default language is English so existing tests and non-UI
callers keep byte-identical output. This helper does not depend on Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from modules.ai_advisory.grounded_brief import GroundedAnalystBrief, GroundedBriefItem
from modules.ui.case_draft_view import CaseDraftDisplay
from modules.ui.case_memory_view import CaseMemoryCorpusDisplay
from modules.ui.console_state import ActiveContextSummary
from modules.ui.performance_view import RuntimeTimingDisplay
from modules.ui.report_sections import ParsedReportSections
from modules.ui.route_policy_view import RoutePolicyDisplay

REPORT_TITLE = "Security AI Analyst Report"
REPORT_TYPE = "streamlit_analyst_console_markdown"
EXPORT_STATUS = "generated_for_human_review"
REPORT_SOURCE = "Streamlit Analyst Console"
MISSING_SIMILAR_CASES = "No approved similar case output is currently available."
MISSING_GRAPH_RELATIONSHIP = "No graph-grounded relationship output is currently available."
MISSING_ANALYSIS_REPORT = "No analysis report output is currently available."
MISSING_RAW_OUTPUT = "No raw console output is currently available."

EXPORT_SAFETY_NOTES = (
    "This report is generated for human review.",
    "safety_reviewed: false",
    "Review before sharing externally.",
    "The report may contain raw evidence, payload text, or log-derived content.",
    "Do not treat this report as live remediation or enforcement proof.",
)

SAFETY_BOUNDARY_LINES = (
    "BLOCK / MONITOR / ALLOW are simulated decisions.",
    "Historical approved cases are advisory references only.",
    "Similar cases do not override the current Risk Level or Decision.",
    "Drafts are not live knowledge.",
    "Drafts are not ingested.",
    "No real firewall, WAF, EDR, account, password reset, monitoring deployment, or enforcement action was executed.",
)

DEFAULT_REPORT_LANGUAGE = "en"
_SUPPORTED_REPORT_LANGUAGES = ("en", "zh-TW", "bilingual")

# Fixed markdown section headings. English wording is unchanged; bilingual is
# composed compactly as "<zh-TW> / <en>" so sections are not duplicated twice.
_SECTION_HEADINGS: dict[str, dict[str, str]] = {
    "report_metadata": {"en": "Report Metadata", "zh-TW": "報告中繼資料"},
    "human_review_warning": {"en": "Human Review Warning", "zh-TW": "人工審查警告"},
    "active_context": {"en": "Active Context", "zh-TW": "目前脈絡"},
    "analysis_mode_and_performance": {
        "en": "Analysis Mode And Performance",
        "zh-TW": "分析模式與效能",
    },
    "evidence_grounded_ai_brief": {"en": "Evidence-Grounded AI Brief", "zh-TW": "Evidence-Grounded AI Brief"},
    "analysis_report": {"en": "Analysis Report", "zh-TW": "分析報告"},
    "approved_similar_cases": {"en": "Approved Similar Cases", "zh-TW": "核准相似案例"},
    "graph_relationship": {
        "en": "Graph-Grounded Relationship Explanation",
        "zh-TW": "圖形關係說明",
    },
    "case_memory_summary": {"en": "Case Memory Summary", "zh-TW": "案例記憶"},
    "case_draft_status": {"en": "Case Draft Status", "zh-TW": "案例草稿狀態"},
    "route_policy": {"en": "Route / Policy", "zh-TW": "路由 / 政策"},
    "safety_boundary": {"en": "Safety Boundary", "zh-TW": "安全邊界"},
    "raw_output_appendix": {"en": "Raw Output Appendix", "zh-TW": "原始輸出附錄"},
}

# Export / human-review safety notes. The "safety_reviewed: false" token is a
# machine field and stays identical in every language.
_EXPORT_SAFETY_NOTES_BY_LANGUAGE: dict[str, tuple[str, ...]] = {
    "en": EXPORT_SAFETY_NOTES,
    "zh-TW": (
        "此報告產生供人工審查使用。",
        "safety_reviewed: false",
        "對外分享前請先審查。",
        "此報告可能包含原始證據、payload 文字或日誌衍生內容。",
        "請勿將此報告視為即時修復或強制執行證明。",
    ),
    "bilingual": (
        "此報告產生供人工審查使用。 / This report is generated for human review.",
        "safety_reviewed: false",
        "對外分享前請先審查。 / Review before sharing externally.",
        "此報告可能包含原始證據、payload 文字或日誌衍生內容。 / "
        "The report may contain raw evidence, payload text, or log-derived content.",
        "請勿將此報告視為即時修復或強制執行證明。 / "
        "Do not treat this report as live remediation or enforcement proof.",
    ),
}

_SAFETY_BOUNDARY_LINES_BY_LANGUAGE: dict[str, tuple[str, ...]] = {
    "en": SAFETY_BOUNDARY_LINES,
    "zh-TW": (
        "BLOCK / MONITOR / ALLOW 是模擬決策。",
        "歷史核准案例僅供參考。",
        "相似案例不會覆蓋目前的 Risk Level 或 Decision。",
        "草稿不是即時知識。",
        "草稿不會被匯入。",
        "未執行任何真實防火牆、WAF、EDR、帳號、密碼重設、監控部署或強制動作。",
    ),
    "bilingual": (
        "BLOCK / MONITOR / ALLOW 是模擬決策。 / BLOCK / MONITOR / ALLOW are simulated decisions.",
        "歷史核准案例僅供參考。 / Historical approved cases are advisory references only.",
        "相似案例不會覆蓋目前的 Risk Level 或 Decision。 / "
        "Similar cases do not override the current Risk Level or Decision.",
        "草稿不是即時知識。 / Drafts are not live knowledge.",
        "草稿不會被匯入。 / Drafts are not ingested.",
        "未執行任何真實防火牆、WAF、EDR、帳號、密碼重設、監控部署或強制動作。 / "
        "No real firewall, WAF, EDR, account, password reset, monitoring deployment, "
        "or enforcement action was executed.",
    ),
}

_MISSING_TEXT: dict[str, dict[str, str]] = {
    "analysis_report": {"en": MISSING_ANALYSIS_REPORT, "zh-TW": "目前沒有可用的分析報告輸出。"},
    "approved_similar_cases": {"en": MISSING_SIMILAR_CASES, "zh-TW": "目前沒有可用的核准相似案例輸出。"},
    "graph_relationship": {"en": MISSING_GRAPH_RELATIONSHIP, "zh-TW": "目前沒有可用的圖形關係輸出。"},
    "raw_output": {"en": MISSING_RAW_OUTPUT, "zh-TW": "目前沒有可用的原始主控台輸出。"},
}

_RAW_OUTPUT_WARNING = {
    "en": (
        "Warning: Raw console output may contain evidence or payload text and "
        "requires human review before sharing."
    ),
    "zh-TW": "警告：原始主控台輸出可能包含證據或 payload 文字，分享前需經人工審查。",
}

_ADDITIONAL_PARSED_SAFETY_LABEL = {
    "en": "Additional parsed safety text:",
    "zh-TW": "額外解析的安全文字：",
}

# Fixed labels for the "No active context" placeholder and detail fallbacks.
_NO_ACTIVE_CONTEXT_LABEL = {"en": "No active context", "zh-TW": "無目前脈絡"}


def _normalize_language(language: str) -> str:
    text = str(language or "").strip()
    return text if text in _SUPPORTED_REPORT_LANGUAGES else DEFAULT_REPORT_LANGUAGE


def _localized(mapping: dict[str, str], language: str) -> str:
    lang = _normalize_language(language)
    english = mapping["en"]
    if lang == "en":
        return english
    chinese = mapping["zh-TW"]
    if lang == "zh-TW":
        return chinese
    return f"{chinese} / {english}"


def export_safety_notes(language: str = DEFAULT_REPORT_LANGUAGE) -> tuple[str, ...]:
    """Return the language-aware export / human-review safety notes."""

    return _EXPORT_SAFETY_NOTES_BY_LANGUAGE[_normalize_language(language)]


def markdown_safety_boundary_lines(language: str = DEFAULT_REPORT_LANGUAGE) -> tuple[str, ...]:
    """Return the language-aware markdown safety-boundary lines."""

    return _SAFETY_BOUNDARY_LINES_BY_LANGUAGE[_normalize_language(language)]


def report_section_heading(key: str, language: str = DEFAULT_REPORT_LANGUAGE) -> str:
    """Return a localized ``## Heading`` for a known wrapper section key."""

    return _heading(key, language)


@dataclass(frozen=True)
class MarkdownReportExport:
    """Generated Markdown report plus metadata needed by the UI download button."""

    filename: str
    markdown: str
    generated_at: str
    safety_notes: tuple[str, ...] = EXPORT_SAFETY_NOTES


def build_markdown_report_export(
    *,
    active_context_summary: ActiveContextSummary,
    report_sections: ParsedReportSections,
    case_memory_display: CaseMemoryCorpusDisplay,
    case_draft_display: CaseDraftDisplay,
    runtime_timing_display: RuntimeTimingDisplay,
    route_policy_display: RoutePolicyDisplay,
    raw_output: str,
    generated_at: str,
    safety_boundary_text: str = "",
    language: str = DEFAULT_REPORT_LANGUAGE,
    evidence_grounded_brief: GroundedAnalystBrief | None = None,
) -> MarkdownReportExport:
    """Build a deterministic Markdown report from existing UI display models."""

    lang = _normalize_language(language)
    safe_generated_at = str(generated_at or "").strip() or "unknown"
    markdown = _join_blocks(
        [
            _metadata_section(safe_generated_at, lang),
            _review_warning_section(lang),
            _active_context_section(active_context_summary, lang),
            _performance_section(runtime_timing_display, lang),
            _evidence_grounded_brief_section(evidence_grounded_brief, lang),
            _analysis_report_section(report_sections.analysis_report, lang),
            _approved_similar_cases_section(report_sections.approved_similar_cases, lang),
            _graph_relationship_section(report_sections.graph_relationship_explanation, lang),
            _case_memory_section(case_memory_display, lang),
            _case_draft_section(case_draft_display, lang),
            _route_policy_section(route_policy_display, lang),
            _safety_boundary_section(safety_boundary_text, lang),
            _raw_output_section(raw_output, lang),
        ]
    )
    return MarkdownReportExport(
        filename=build_markdown_report_filename(safe_generated_at),
        markdown=markdown,
        generated_at=safe_generated_at,
        safety_notes=export_safety_notes(lang),
    )


def build_markdown_report_filename(generated_at: str) -> str:
    """Return a safe demo filename ending in .md."""

    timestamp = _timestamp_slug(generated_at)
    return f"security-ai-report-{timestamp}.md"


def _heading(key: str, language: str) -> str:
    return f"## {_localized(_SECTION_HEADINGS[key], language)}"


def _metadata_section(generated_at: str, language: str) -> str:
    return "\n".join(
        [
            f"# {REPORT_TITLE}",
            "",
            _heading("report_metadata", language),
            f"- title: {REPORT_TITLE}",
            f"- generated_at: {generated_at}",
            f"- report_type: {REPORT_TYPE}",
            "- safety_reviewed: false",
            f"- export_status: {EXPORT_STATUS}",
            "- simulated_decision: true",
            f"- source: {REPORT_SOURCE}",
        ]
    )


def _review_warning_section(language: str) -> str:
    return _bullet_section(_heading("human_review_warning", language), export_safety_notes(language))


def _active_context_section(summary: ActiveContextSummary, language: str) -> str:
    context_kind = (
        summary.title if summary.has_context else _localized(_NO_ACTIVE_CONTEXT_LABEL, language)
    )
    lines = [
        _heading("active_context", language),
        f"- context_kind: {context_kind}",
        f"- risk_level: {summary.risk_level or 'N/A'}",
        f"- decision: {summary.decision or 'N/A'}",
    ]
    if summary.details:
        lines.append("- details:")
        lines.extend(f"  - {detail}" for detail in summary.details)
    else:
        lines.append("- details: None")
    return "\n".join(lines)


def _performance_section(display: RuntimeTimingDisplay, language: str) -> str:
    lines = [
        _heading("analysis_mode_and_performance", language),
        f"- latest_action: {display.action_label}",
        f"- selected_skill: {display.selected_skill}",
        f"- analysis_mode: {display.analysis_mode}",
        f"- elapsed_seconds: {display.elapsed_seconds:.3f}",
        f"- elapsed_display: {display.elapsed_display}",
        f"- output_kind: {display.output_kind}",
        f"- timestamp: {display.timestamp or 'N/A'}",
        "- timing_scope: local demo environment only",
        "- notes:",
    ]
    lines.extend(f"  - {note}" for note in display.notes)
    return "\n".join(lines)


def _evidence_grounded_brief_section(
    brief: GroundedAnalystBrief | None, language: str
) -> str:
    if brief is None:
        return ""
    lines = [
        _heading("evidence_grounded_ai_brief", language),
        f"- schema_version: {brief.schema_version}",
        f"- llm_status: {brief.llm_status}",
        f"- official_risk_level: {brief.official_verdict.risk_level or 'N/A'}",
        f"- official_decision: {brief.official_verdict.decision or 'N/A'}",
        f"- simulated_decision: {str(brief.official_verdict.simulated_decision).lower()}",
        f"- authority: {brief.official_verdict.authority}",
        "- executive_summary:",
        *_brief_item_lines(brief.executive_summary),
        "- supporting_evidence:",
        *_brief_item_lines(brief.supporting_evidence),
        "- evidence_gap_summary:",
        *_brief_item_lines(brief.evidence_gap_summary),
        "- advisory_context:",
        *_brief_item_lines(brief.advisory_context),
        "- recommended_next_steps:",
        *_brief_item_lines(brief.recommended_next_steps),
        "- unsafe_assumptions:",
        *_brief_item_lines(brief.unsafe_assumptions),
        "- citations:",
        *[
            f"  - {citation.citation_id}: {citation.kind} - {citation.label}"
            for citation in brief.citations
        ],
        "- safety_boundary:",
        *[f"  - {line}" for line in brief.safety_boundary],
    ]
    return "\n".join(lines)


def _brief_item_lines(items: list[GroundedBriefItem]) -> list[str]:
    if not items:
        return ["  - None"]
    lines = []
    for item in items:
        citations = f" [{', '.join(item.citation_ids)}]" if item.citation_ids else ""
        lines.append(f"  - {item.text}{citations}")
    return lines


def _analysis_report_section(text: str, language: str) -> str:
    return _markdown_text_section(
        _heading("analysis_report", language), text, _missing_text("analysis_report", language)
    )


def _approved_similar_cases_section(text: str, language: str) -> str:
    return _markdown_text_section(
        _heading("approved_similar_cases", language),
        text,
        _missing_text("approved_similar_cases", language),
    )


def _graph_relationship_section(text: str, language: str) -> str:
    return _markdown_text_section(
        _heading("graph_relationship", language),
        text,
        _missing_text("graph_relationship", language),
    )


def _case_memory_section(display: CaseMemoryCorpusDisplay, language: str) -> str:
    lines = [
        _heading("case_memory_summary", language),
        f"- approved_seed_count: {display.approved_seed_count}",
        f"- approved_for_retrieval_count: {display.approved_for_retrieval_count}",
        f"- source_directory: {display.source_directory}",
        "- approved_seeds:",
    ]
    if display.seeds:
        lines.extend(f"  - {seed.case_id}: {seed.title}" for seed in display.seeds)
    else:
        lines.append("  - None loaded")
    lines.append("- boundary_notes:")
    lines.extend(f"  - {note}" for note in display.boundary_notes)
    return "\n".join(lines)


def _case_draft_section(display: CaseDraftDisplay, language: str) -> str:
    lines = [
        _heading("case_draft_status", language),
        f"- status: {display.status}",
        f"- pending_approval: {_yes_no(display.has_pending_request)}",
        f"- active_context: {_yes_no(display.has_active_context)}",
        f"- draft_path: {display.draft_path or 'N/A'}",
        f"- message: {display.message}",
        "- safety_notes:",
    ]
    lines.extend(f"  - {note}" for note in display.safety_notes)
    return "\n".join(lines)


def _route_policy_section(display: RoutePolicyDisplay, language: str) -> str:
    lines = [
        _heading("route_policy", language),
        f"- selected_skill: {display.selected_skill}",
        f"- route_reason: {display.route_reason}",
        f"- permission: {display.permission}",
        f"- execution_mode: {display.execution_mode}",
        f"- human_approval_required: {str(display.human_approval_required).lower()}",
        f"- write_behavior: {display.write_behavior}",
        "- safety_notes:",
    ]
    lines.extend(f"  - {note}" for note in display.safety_notes)
    return "\n".join(lines)


def _safety_boundary_section(safety_boundary_text: str, language: str) -> str:
    lines = [_heading("safety_boundary", language)]
    lines.extend(f"- {line}" for line in markdown_safety_boundary_lines(language))
    extra = str(safety_boundary_text or "").strip()
    if extra:
        lines.extend(
            ["", _localized(_ADDITIONAL_PARSED_SAFETY_LABEL, language), "", _code_block(extra)]
        )
    return "\n".join(lines)


def _raw_output_section(raw_output: str, language: str) -> str:
    text = str(raw_output or "").strip() or _missing_text("raw_output", language)
    return "\n".join(
        [
            _heading("raw_output_appendix", language),
            _localized(_RAW_OUTPUT_WARNING, language),
            "",
            _code_block(text),
        ]
    )


def _missing_text(key: str, language: str) -> str:
    return _localized(_MISSING_TEXT[key], language)


def _markdown_text_section(title: str, text: str, missing_text: str) -> str:
    body = str(text or "").strip() or missing_text
    return "\n".join([title, "", _code_block(body)])


def _bullet_section(title: str, notes: tuple[str, ...]) -> str:
    return "\n".join([title, *[f"- {note}" for note in notes]])


def _code_block(text: str) -> str:
    safe_text = str(text or "").replace("```", "```")
    return f"```text\n{safe_text}\n```"


def _join_blocks(blocks: list[str]) -> str:
    return "\n\n".join(block.strip() for block in blocks if block and block.strip()) + "\n"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _timestamp_slug(generated_at: str) -> str:
    digits = re.sub(r"\D", "", str(generated_at or ""))
    if len(digits) >= 14:
        return f"{digits[:8]}-{digits[8:14]}"
    if len(digits) >= 8:
        return digits[:8]
    return "unknown"
