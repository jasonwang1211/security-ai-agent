"""Pure Markdown report export helpers for the Streamlit analyst console."""

from __future__ import annotations

from dataclasses import dataclass
import re

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
) -> MarkdownReportExport:
    """Build a deterministic Markdown report from existing UI display models."""

    safe_generated_at = str(generated_at or "").strip() or "unknown"
    markdown = _join_blocks(
        [
            _metadata_section(safe_generated_at),
            _review_warning_section(),
            _active_context_section(active_context_summary),
            _performance_section(runtime_timing_display),
            _analysis_report_section(report_sections.analysis_report),
            _approved_similar_cases_section(report_sections.approved_similar_cases),
            _graph_relationship_section(report_sections.graph_relationship_explanation),
            _case_memory_section(case_memory_display),
            _case_draft_section(case_draft_display),
            _route_policy_section(route_policy_display),
            _safety_boundary_section(safety_boundary_text),
            _raw_output_section(raw_output),
        ]
    )
    return MarkdownReportExport(
        filename=build_markdown_report_filename(safe_generated_at),
        markdown=markdown,
        generated_at=safe_generated_at,
    )


def build_markdown_report_filename(generated_at: str) -> str:
    """Return a safe demo filename ending in .md."""

    timestamp = _timestamp_slug(generated_at)
    return f"security-ai-report-{timestamp}.md"


def _metadata_section(generated_at: str) -> str:
    return "\n".join(
        [
            f"# {REPORT_TITLE}",
            "",
            "## Report Metadata",
            f"- title: {REPORT_TITLE}",
            f"- generated_at: {generated_at}",
            f"- report_type: {REPORT_TYPE}",
            "- safety_reviewed: false",
            f"- export_status: {EXPORT_STATUS}",
            "- simulated_decision: true",
            f"- source: {REPORT_SOURCE}",
        ]
    )


def _review_warning_section() -> str:
    return _bullet_section("## Human Review Warning", EXPORT_SAFETY_NOTES)


def _active_context_section(summary: ActiveContextSummary) -> str:
    lines = [
        "## Active Context",
        f"- context_kind: {summary.title if summary.has_context else 'No active context'}",
        f"- risk_level: {summary.risk_level or 'N/A'}",
        f"- decision: {summary.decision or 'N/A'}",
    ]
    if summary.details:
        lines.append("- details:")
        lines.extend(f"  - {detail}" for detail in summary.details)
    else:
        lines.append("- details: None")
    return "\n".join(lines)


def _performance_section(display: RuntimeTimingDisplay) -> str:
    lines = [
        "## Analysis Mode And Performance",
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


def _analysis_report_section(text: str) -> str:
    return _markdown_text_section("## Analysis Report", text, MISSING_ANALYSIS_REPORT)


def _approved_similar_cases_section(text: str) -> str:
    return _markdown_text_section("## Approved Similar Cases", text, MISSING_SIMILAR_CASES)


def _graph_relationship_section(text: str) -> str:
    return _markdown_text_section(
        "## Graph-Grounded Relationship Explanation",
        text,
        MISSING_GRAPH_RELATIONSHIP,
    )


def _case_memory_section(display: CaseMemoryCorpusDisplay) -> str:
    lines = [
        "## Case Memory Summary",
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


def _case_draft_section(display: CaseDraftDisplay) -> str:
    lines = [
        "## Case Draft Status",
        f"- status: {display.status}",
        f"- pending_approval: {_yes_no(display.has_pending_request)}",
        f"- active_context: {_yes_no(display.has_active_context)}",
        f"- draft_path: {display.draft_path or 'N/A'}",
        f"- message: {display.message}",
        "- safety_notes:",
    ]
    lines.extend(f"  - {note}" for note in display.safety_notes)
    return "\n".join(lines)


def _route_policy_section(display: RoutePolicyDisplay) -> str:
    lines = [
        "## Route / Policy",
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


def _safety_boundary_section(safety_boundary_text: str) -> str:
    lines = ["## Safety Boundary"]
    lines.extend(f"- {line}" for line in SAFETY_BOUNDARY_LINES)
    extra = str(safety_boundary_text or "").strip()
    if extra:
        lines.extend(["", "Additional parsed safety text:", "", _code_block(extra)])
    return "\n".join(lines)


def _raw_output_section(raw_output: str) -> str:
    text = str(raw_output or "").strip() or MISSING_RAW_OUTPUT
    return "\n".join(
        [
            "## Raw Output Appendix",
            "Warning: Raw console output may contain evidence or payload text and requires human review before sharing.",
            "",
            _code_block(text),
        ]
    )


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
