import sys
from pathlib import Path

from modules.ui.case_draft_view import CASE_DRAFT_SAFETY_NOTES, CaseDraftDisplay
from modules.ui.case_memory_view import build_case_memory_display
from modules.ui.console_state import ActiveContextSummary
from modules.ui.performance_view import RuntimeTimingDisplay
from modules.ui.report_export_view import (
    EXPORT_SAFETY_NOTES,
    MISSING_GRAPH_RELATIONSHIP,
    MISSING_SIMILAR_CASES,
    build_markdown_report_export,
)
from modules.ui.report_sections import ParsedReportSections
from modules.ui.route_policy_view import RoutePolicyDisplay

GENERATED_AT = "2026-06-08T10:11:12+08:00"


def _active_context() -> ActiveContextSummary:
    return ActiveContextSummary(
        kind="event",
        title="Payload/Event",
        risk_level="HIGH",
        decision="BLOCK",
        details=("Attack Type: Command Injection", "Rule IDs: CMD-001"),
    )


def _sections() -> ParsedReportSections:
    return ParsedReportSections(
        security_triage_report="[Security Triage Report]\nRisk Level: HIGH\nDecision: BLOCK",
        approved_similar_cases="[Approved Similar Cases]\n1. CASE-SEED-001 - Command Injection Payload",
        graph_relationship_explanation=(
            "Graph-Grounded Relationship Explanation:\n"
            "Current context shares rule ID CMD-001 with CASE-SEED-001."
        ),
        safety_boundary="5. Simulation Notice\nBLOCK / MONITOR / ALLOW are simulated decisions.",
    )


def _case_draft() -> CaseDraftDisplay:
    return CaseDraftDisplay(
        status="pending approval",
        message="Case draft request prepared; explicit approval is required.",
        draft_path="workbench/case_drafts/example.md",
        has_active_context=True,
        has_pending_request=True,
        safety_notes=CASE_DRAFT_SAFETY_NOTES,
    )


def _timing() -> RuntimeTimingDisplay:
    return RuntimeTimingDisplay(
        action_label="Run input",
        selected_skill="AnalyzePayloadSkill",
        elapsed_seconds=0.123,
        elapsed_display="0.123s",
        input_text="test; rm -rf /tmp/test",
        status="ok",
        output_kind="analysis",
        started_at="2026-06-08T10:11:11+08:00",
        ended_at=GENERATED_AT,
        timestamp=GENERATED_AT,
        analysis_mode="Fast deterministic",
        notes=("Timing is for the local demo environment only.",),
    )


def _route_policy() -> RoutePolicyDisplay:
    return RoutePolicyDisplay(
        selected_skill="AnalyzePayloadSkill",
        route_reason="payload-style input matched deterministic payload analysis route",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        human_approval_required=False,
        write_behavior="none",
        safety_notes=("No real enforcement was executed.",),
    )


def _export(sections: ParsedReportSections | None = None):
    return build_markdown_report_export(
        active_context_summary=_active_context(),
        report_sections=sections or _sections(),
        case_memory_display=build_case_memory_display(),
        case_draft_display=_case_draft(),
        runtime_timing_display=_timing(),
        route_policy_display=_route_policy(),
        raw_output="AI: raw console output",
        generated_at=GENERATED_AT,
        safety_boundary_text="No real firewall, WAF, EDR, account, password reset, monitoring deployment, or enforcement action was executed.",
    )


def test_markdown_export_includes_required_metadata() -> None:
    export = _export()

    assert export.generated_at == GENERATED_AT
    assert export.safety_notes == EXPORT_SAFETY_NOTES
    assert "# Security AI Analyst Report" in export.markdown
    assert "safety_reviewed: false" in export.markdown
    assert "export_status: generated_for_human_review" in export.markdown
    assert "simulated_decision: true" in export.markdown
    assert "source: Streamlit Analyst Console" in export.markdown


def test_markdown_export_includes_active_context() -> None:
    markdown = _export().markdown

    assert "## Active Context" in markdown
    assert "Payload/Event" in markdown
    assert "HIGH" in markdown
    assert "BLOCK" in markdown
    assert "Command Injection" in markdown
    assert "CMD-001" in markdown


def test_markdown_export_includes_approved_similar_case_section_when_present() -> None:
    markdown = _export().markdown

    assert "## Approved Similar Cases" in markdown
    assert "CASE-SEED-001" in markdown


def test_markdown_export_includes_graph_relationship_section_when_present() -> None:
    markdown = _export().markdown

    assert "## Graph-Grounded Relationship Explanation" in markdown
    assert "Current context shares rule ID CMD-001 with CASE-SEED-001." in markdown


def test_markdown_export_includes_case_memory_summary() -> None:
    markdown = _export().markdown

    assert "## Case Memory Summary" in markdown
    assert "approved_seed_count: 3" in markdown
    assert "approved_for_retrieval_count: 3" in markdown
    assert "CASE-SEED-001" in markdown
    assert "CASE-SEED-002" in markdown
    assert "CASE-SEED-003" in markdown
    assert "advisory references only" in markdown


def test_markdown_export_includes_case_draft_status_and_safety_notes() -> None:
    markdown = _export().markdown

    assert "## Case Draft Status" in markdown
    assert "status: pending approval" in markdown
    assert "pending_approval: yes" in markdown
    assert "active_context: yes" in markdown
    assert "workbench/case_drafts/example.md" in markdown
    assert "Draft files are not live knowledge." in markdown


def test_markdown_export_includes_performance_timing() -> None:
    markdown = _export().markdown

    assert "## Analysis Mode And Performance" in markdown
    assert "latest_action: Run input" in markdown
    assert "selected_skill: AnalyzePayloadSkill" in markdown
    assert "analysis_mode: Fast deterministic" in markdown
    assert "elapsed_display: 0.123s" in markdown
    assert "timing_scope: local demo environment only" in markdown


def test_markdown_export_includes_route_policy() -> None:
    markdown = _export().markdown

    assert "## Route / Policy" in markdown
    assert "selected_skill: AnalyzePayloadSkill" in markdown
    assert "permission: READ_ONLY" in markdown
    assert "execution_mode: DIRECT_ALLOWED" in markdown
    assert "human_approval_required: false" in markdown
    assert "write_behavior: none" in markdown


def test_markdown_export_includes_safety_boundary_and_no_real_enforcement_language() -> None:
    markdown = _export().markdown

    assert "## Safety Boundary" in markdown
    assert "BLOCK / MONITOR / ALLOW are simulated decisions." in markdown
    assert "Historical approved cases are advisory references only." in markdown
    assert "Similar cases do not override the current Risk Level or Decision." in markdown
    assert "Drafts are not live knowledge." in markdown
    assert "Drafts are not ingested." in markdown
    assert "No real firewall, WAF, EDR, account, password reset" in markdown


def test_markdown_export_handles_missing_sections_gracefully() -> None:
    markdown = _export(ParsedReportSections()).markdown

    assert "No analysis report output is currently available." in markdown
    assert MISSING_SIMILAR_CASES in markdown
    assert MISSING_GRAPH_RELATIONSHIP in markdown


def test_markdown_export_produces_safe_markdown_filename() -> None:
    export = _export()

    assert export.filename == "security-ai-report-20260608-101112.md"
    assert export.filename.endswith(".md")
    assert ":" not in export.filename


def test_report_export_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/report_export_view.py").read_text(encoding="utf-8")

    assert "import streamlit" not in source.casefold()
    assert "streamlit" not in sys.modules
