import sys
from pathlib import Path

from modules.ui.console_state import (
    STATE_ANALYSIS_OUTPUT,
    STATE_SIMILAR_CASE_OUTPUT,
    combined_display_output,
    record_analysis_output,
)
from modules.ui.report_sections import (
    APPROVED_SIMILAR_CASES,
    DEFAULT_SAFETY_BOUNDARY_TEXT,
    GRAPH_RELATIONSHIP_TITLE,
    SECURITY_TRIAGE_REPORT,
    build_safety_boundary_text,
    extract_approved_similar_cases,
    extract_safety_boundary,
    has_graph_relationship_explanation,
    parse_report_sections,
)


def test_parses_security_triage_report_section() -> None:
    text = "\n".join(
        [
            "AI: [Security Triage Report]",
            "",
            "0. Quick Verdict",
            "Risk Level: HIGH",
            "Decision: BLOCK",
            "",
            "5. Simulation Notice",
            "BLOCK / MONITOR / ALLOW are simulated decisions.",
            "",
            "[Approved Similar Cases]",
            "Current context kind: active_event",
        ]
    )

    sections = parse_report_sections(text)

    assert sections.security_triage_report.startswith(SECURITY_TRIAGE_REPORT)
    assert "Risk Level: HIGH" in sections.security_triage_report
    assert APPROVED_SIMILAR_CASES not in sections.security_triage_report
    assert "Risk Level: HIGH" in sections.analysis_report


def test_parses_approved_similar_cases_section() -> None:
    text = "\n".join(
        [
            "[Approved Similar Cases]",
            "Current context kind: active_event",
            "1. CASE-SEED-001 - Command Injection Payload",
            "   Similarity reasons: matched attack_types: Command Injection",
            "   Key differences / missing evidence to check: process evidence missing",
        ]
    )

    section = extract_approved_similar_cases(text)

    assert section.startswith(APPROVED_SIMILAR_CASES)
    assert "CASE-SEED-001" in section
    assert "Similarity reasons:" in section


def test_detects_graph_grounded_relationship_explanation() -> None:
    text = "\n".join(
        [
            "[Approved Similar Cases]",
            "1. CASE-SEED-001 - Command Injection Payload",
            "   Graph-Grounded Relationship Explanation:",
            "      - Current context shares rule ID CMD-001 with CASE-SEED-001.",
            "      - Boundary: Historical approved cases are advisory references only.",
            "   Analyst conclusion: Historical BLOCK was simulated.",
        ]
    )

    sections = parse_report_sections(text)

    assert has_graph_relationship_explanation(text)
    assert sections.graph_relationship_explanation.startswith(GRAPH_RELATIONSHIP_TITLE)
    assert "shares rule ID CMD-001" in sections.graph_relationship_explanation
    assert "Analyst conclusion" not in sections.graph_relationship_explanation


def test_extracts_safety_boundary_and_simulation_notice_text() -> None:
    text = "\n".join(
        [
            "[Security Triage Report]",
            "5. Simulation Notice",
            "BLOCK / MONITOR / ALLOW are simulated decisions.",
            "6. AI Assist",
            "Historical approved cases are advisory references only. They do not override Risk Level or Decision.",
            "Repeated login failures followed by success do not prove account compromise by themselves.",
        ]
    )

    boundary = extract_safety_boundary(text)
    ui_boundary = build_safety_boundary_text(text)

    assert "5. Simulation Notice" in boundary
    assert "simulated decisions" in boundary
    assert "do not override" in boundary
    assert "do not prove account compromise" in boundary
    assert DEFAULT_SAFETY_BOUNDARY_TEXT in ui_boundary


def test_handles_missing_sections_gracefully() -> None:
    sections = parse_report_sections("plain text without known report headings")

    assert sections.security_triage_report == ""
    assert sections.log_ingestion_summary == ""
    assert sections.structured_authentication_incident == ""
    assert sections.approved_similar_cases == ""
    assert sections.graph_relationship_explanation == ""
    assert sections.safety_boundary == ""
    assert sections.analysis_report == ""


def test_record_analysis_output_clears_stale_similar_case_output() -> None:
    session_state = {
        STATE_ANALYSIS_OUTPUT: "old analysis",
        STATE_SIMILAR_CASE_OUTPUT: "[Approved Similar Cases]\n1. CASE-SEED-001",
    }

    record_analysis_output(session_state, "[Log Ingestion Summary]\nnew auth analysis")

    assert session_state[STATE_ANALYSIS_OUTPUT] == "[Log Ingestion Summary]\nnew auth analysis"
    assert session_state[STATE_SIMILAR_CASE_OUTPUT] == ""
    assert "CASE-SEED-001" not in combined_display_output(session_state)


def test_report_section_helpers_do_not_import_streamlit() -> None:
    source = Path("modules/ui/report_sections.py").read_text(encoding="utf-8")

    assert "streamlit" not in source
    assert "streamlit" not in sys.modules
