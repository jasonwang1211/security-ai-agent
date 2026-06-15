import sys
from pathlib import Path
from types import SimpleNamespace

from modules.ai_advisory.evidence_bundle import build_evidence_grounding_bundle
from modules.ai_advisory.grounded_brief import generate_grounded_analyst_brief
from modules.ai_advisory.types import AIAdvisoryInput
from modules.graph.types import GraphEdge, GraphEdgeKind, GraphNode, GraphNodeKind, GraphSnapshot
from modules.ui.case_draft_view import CASE_DRAFT_SAFETY_NOTES, CaseDraftDisplay
from modules.ui.case_memory_view import build_case_memory_display
from modules.ui.console_state import ActiveContextSummary
from modules.ui.performance_view import RuntimeTimingDisplay
from modules.ui.report_export_view import (
    EXPORT_SAFETY_NOTES,
    MISSING_GRAPH_RELATIONSHIP,
    MISSING_SIMILAR_CASES,
    build_markdown_report_export,
    export_safety_notes,
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


_SAFETY_BOUNDARY_TEXT = (
    "No real firewall, WAF, EDR, account, password reset, monitoring deployment, "
    "or enforcement action was executed."
)


def _grounded_brief():
    bundle = build_evidence_grounding_bundle(
        AIAdvisoryInput(
            event_kind="payload_or_event",
            attack_type="Command Injection",
            risk_label="HIGH",
            decision_label="BLOCK",
            matched_rule_ids=["CMD-001"],
            matched_signatures=["; rm -rf"],
            evidence_labels=["shell_metacharacter_payload"],
        )
    )
    return generate_grounded_analyst_brief(bundle)


def _export(
    sections: ParsedReportSections | None = None,
    language: str = "en",
    evidence_grounded_brief=None,
):
    return build_markdown_report_export(
        active_context_summary=_active_context(),
        report_sections=sections or _sections(),
        case_memory_display=build_case_memory_display(),
        case_draft_display=_case_draft(),
        runtime_timing_display=_timing(),
        route_policy_display=_route_policy(),
        raw_output="AI: raw console output",
        generated_at=GENERATED_AT,
        safety_boundary_text=_SAFETY_BOUNDARY_TEXT,
        language=language,
        evidence_grounded_brief=evidence_grounded_brief,
    )


def _export_builder_default():
    """Build with no explicit language to exercise the builder's own default."""

    return build_markdown_report_export(
        active_context_summary=_active_context(),
        report_sections=_sections(),
        case_memory_display=build_case_memory_display(),
        case_draft_display=_case_draft(),
        runtime_timing_display=_timing(),
        route_policy_display=_route_policy(),
        raw_output="AI: raw console output",
        generated_at=GENERATED_AT,
        safety_boundary_text=_SAFETY_BOUNDARY_TEXT,
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


# --- v2.6-R language-aware export wrapper ------------------------------------


def test_english_export_preserves_wrapper_headings_and_warning() -> None:
    markdown = _export(language="en").markdown

    assert "## Report Metadata" in markdown
    assert "## Human Review Warning" in markdown
    assert "This report is generated for human review." in markdown
    assert "safety_reviewed: false" in markdown


def test_default_language_export_matches_explicit_english() -> None:
    assert _export_builder_default().markdown == _export(language="en").markdown
    assert _export_builder_default().safety_notes == EXPORT_SAFETY_NOTES


def test_zh_tw_export_uses_chinese_wrapper_and_keeps_dynamic_values() -> None:
    export = _export(language="zh-TW")
    markdown = export.markdown

    assert "## 報告中繼資料" in markdown
    assert "## 人工審查警告" in markdown
    assert "此報告產生供人工審查使用" in markdown
    # machine field tokens stay identical across languages.
    assert "safety_reviewed: false" in markdown
    assert "export_status: generated_for_human_review" in markdown
    # dynamic backend-derived content is not translated.
    assert "Risk Level: HIGH" in markdown
    assert "CASE-SEED-001" in markdown
    assert "Current context shares rule ID CMD-001 with CASE-SEED-001." in markdown
    # English wrapper headings must not leak in zh-TW.
    assert "## Report Metadata" not in markdown
    assert "## Human Review Warning" not in markdown
    # panel-facing safety notes are localized too.
    assert export.safety_notes == export_safety_notes("zh-TW")
    assert any("此報告產生供人工審查使用" in note for note in export.safety_notes)


def test_bilingual_export_uses_compact_bilingual_headings() -> None:
    markdown = _export(language="bilingual").markdown

    assert "## 報告中繼資料 / Report Metadata" in markdown
    assert "## 人工審查警告 / Human Review Warning" in markdown
    # dynamic values unchanged.
    assert "Risk Level: HIGH" in markdown
    assert "CASE-SEED-001" in markdown


def test_export_safety_notes_are_language_aware() -> None:
    assert export_safety_notes("en") == EXPORT_SAFETY_NOTES
    zh = export_safety_notes("zh-TW")
    assert "此報告產生供人工審查使用。" in zh
    assert "safety_reviewed: false" in zh  # field token preserved
    bilingual = export_safety_notes("bilingual")
    assert any(" / This report is generated for human review." in note for note in bilingual)


def test_unsupported_export_language_falls_back_to_english() -> None:
    markdown = _export(language="fr").markdown

    assert "## Report Metadata" in markdown
    assert "## 報告中繼資料" not in markdown
    assert export_safety_notes("fr") == EXPORT_SAFETY_NOTES


def test_export_includes_localized_similar_case_and_graph_sections() -> None:
    # v2.6-S: when the parsed sections carry localized similar-case / graph text,
    # the export embeds that text verbatim under the (localized) wrapper headings.
    localized_sections = ParsedReportSections(
        approved_similar_cases="\n".join(
            [
                "[核准相似案例]",
                "目前風險等級：HIGH",
                "1. CASE-SEED-001 - Command Injection Payload",
                "   相似原因：matched attack_types: Command Injection",
            ]
        ),
        graph_relationship_explanation="\n".join(
            [
                "圖形關係說明：",
                "      - 目前脈絡與 CASE-SEED-001 共享攻擊類型：Command Injection。",
            ]
        ),
    )

    markdown = _export(sections=localized_sections, language="zh-TW").markdown

    assert "## 核准相似案例" in markdown
    assert "## 圖形關係說明" in markdown
    assert "[核准相似案例]" in markdown
    assert "目前脈絡與 CASE-SEED-001 共享攻擊類型：Command Injection。" in markdown
    # dynamic values are preserved unchanged inside the localized wrapper.
    assert "CASE-SEED-001" in markdown
    assert "matched attack_types: Command Injection" in markdown



def test_markdown_export_omits_evidence_grounded_brief_when_absent() -> None:
    markdown = _export().markdown

    assert "Evidence-Grounded AI Brief" not in markdown


def test_markdown_export_includes_evidence_grounded_brief_when_present() -> None:
    markdown = _export(evidence_grounded_brief=_grounded_brief()).markdown

    assert "## Evidence-Grounded AI Brief" in markdown
    assert "official_risk_level: HIGH" in markdown
    assert "official_decision: BLOCK" in markdown
    assert "llm_status: not_used_deterministic_fallback" in markdown
    assert "CMD-001" in markdown
    # Assert tokens that are rendered specifically inside the brief section
    # (schema header, official-verdict fields, and the brief's own citation
    # rendering) rather than a token that also appears in unrelated sections.
    assert "schema_version: v2.9-ai-analyst-brief1" in markdown
    assert "simulated_decision: true" in markdown
    assert "rule-001: rule - Rule CMD-001" in markdown


def _grounded_brief_with_structured_advisory():
    """Brief whose bundle carries structured similar-case and graph context."""

    similar_case_result = SimpleNamespace(
        matches=[
            SimpleNamespace(
                seed=SimpleNamespace(
                    case_id="CASE-SEED-001",
                    title="Command Injection Payload",
                    outcome="Blocked in demo.",
                    analyst_conclusion="Payload was suspicious.",
                ),
                score=125,
                reasons=("matched attack_types: Command Injection",),
                differences=("Check execution telemetry.",),
            )
        ]
    )
    graph_snapshot = GraphSnapshot(
        nodes=[
            GraphNode(id="current_context", kind=GraphNodeKind.INCIDENT, label="Current Event"),
            GraphNode(id="CASE-SEED-001", kind=GraphNodeKind.INCIDENT, label="CASE-SEED-001 - X"),
        ],
        edges=[
            GraphEdge(
                id="edge-1",
                kind=GraphEdgeKind.RELATED_TO,
                source_node_id="current_context",
                target_node_id="CASE-SEED-001",
            ),
        ],
    )
    bundle = build_evidence_grounding_bundle(
        AIAdvisoryInput(
            event_kind="payload_or_event",
            attack_type="Command Injection",
            risk_label="HIGH",
            decision_label="BLOCK",
            matched_rule_ids=["CMD-001"],
            matched_signatures=["; rm -rf"],
            evidence_labels=["shell_metacharacter_payload"],
        ),
        similar_case_result=similar_case_result,
        graph_snapshot=graph_snapshot,
    )
    return generate_grounded_analyst_brief(bundle)


def test_markdown_export_includes_structured_similar_case_and_graph_citations() -> None:
    markdown = _export(evidence_grounded_brief=_grounded_brief_with_structured_advisory()).markdown

    assert "case-001" in markdown
    assert "graph-001" in markdown
    # advisory framing must travel with the citations
    assert "not proof of current compromise" in markdown
    assert "is not a detection source" in markdown
