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


# --- v2.6-P localized fast-report title parsing -----------------------------


def _zh_fast_report() -> str:
    return "\n".join(
        [
            "AI: [資安分流報告]",
            "模式：快速確定性模式",
            "",
            "0. 快速判定",
            "判定：此事件可能為 Command Injection。",
            "風險等級：HIGH",
            "決策：BLOCK",
            "",
            "1. 摘要",
            "攻擊類型：Command Injection",
            "規則 ID：CMD-001",
        ]
    )


def _bilingual_fast_report() -> str:
    return "\n".join(
        [
            "AI: [資安分流報告 / Security Triage Report]",
            "模式 / Mode：快速確定性模式 / Fast Deterministic Mode",
            "",
            "0. 快速判定 / Quick Verdict",
            "風險等級 / Risk Level：HIGH",
            "決策 / Decision：BLOCK",
        ]
    )


def test_english_triage_marker_still_parses() -> None:
    text = "AI: [Security Triage Report]\nRisk Level: HIGH\nDecision: BLOCK"

    sections = parse_report_sections(text)

    assert sections.security_triage_report.startswith(SECURITY_TRIAGE_REPORT)
    assert "[Security Triage Report]" in sections.analysis_report
    assert "Risk Level: HIGH" in sections.analysis_report


def test_zh_tw_triage_marker_parses_into_analysis_report() -> None:
    sections = parse_report_sections(_zh_fast_report())

    assert "[資安分流報告]" in sections.analysis_report
    assert "風險等級：HIGH" in sections.analysis_report
    assert "攻擊類型：Command Injection" in sections.analysis_report
    assert "CMD-001" in sections.analysis_report


def test_bilingual_triage_marker_parses_into_analysis_report() -> None:
    sections = parse_report_sections(_bilingual_fast_report())

    assert "[資安分流報告 / Security Triage Report]" in sections.analysis_report
    assert "風險等級 / Risk Level：HIGH" in sections.analysis_report


def test_localized_report_combined_with_similar_and_graph_sections() -> None:
    text = "\n\n".join(
        [
            _zh_fast_report(),
            "\n".join(
                [
                    "[Approved Similar Cases]",
                    "Current context kind: active_event",
                    "1. CASE-SEED-001 - Command Injection Payload",
                    "   Graph-Grounded Relationship Explanation:",
                    "      - Current context shares rule ID CMD-001 with CASE-SEED-001.",
                ]
            ),
        ]
    )

    sections = parse_report_sections(text)

    # localized triage parses but stops before the similar-case block.
    assert "[資安分流報告]" in sections.analysis_report
    assert "CASE-SEED-001" not in sections.analysis_report
    # other sections remain intact.
    assert sections.approved_similar_cases.startswith(APPROVED_SIMILAR_CASES)
    assert "CASE-SEED-001" in sections.approved_similar_cases
    assert "shares rule ID CMD-001" in sections.graph_relationship_explanation


def _zh_auth_log_output() -> str:
    return "\n\n".join(
        [
            "\n".join(
                [
                    "[登入日誌匯入摘要]",
                    "",
                    "檔案：demo_logs\\scenario_a_mixed_auth.log",
                    "總行數：33",
                    "偵測到的事件類型：",
                    "- auth_success：18",
                    "- auth_failure：15",
                ]
            ),
            "\n".join(
                [
                    "[結構化驗證事件]",
                    "事件 ID：INC-20260501-001",
                    "風險等級：HIGH",
                    "決策：MONITOR（模擬決策；未執行真實監控部署...）",
                    "Finding ID：F-001",
                ]
            ),
        ]
    )


def _bilingual_auth_log_output() -> str:
    return "\n\n".join(
        [
            "[登入日誌匯入摘要 / Log Ingestion Summary]\n檔案 / File：demo_logs\\x.log",
            "[結構化驗證事件 / Structured Authentication Incident]\n風險等級 / Risk Level：HIGH",
        ]
    )


def test_zh_tw_log_and_auth_titles_parse_into_sections() -> None:
    sections = parse_report_sections(_zh_auth_log_output())

    assert "[登入日誌匯入摘要]" in sections.log_ingestion_summary
    assert "[結構化驗證事件]" in sections.structured_authentication_incident
    assert "[登入日誌匯入摘要]" in sections.analysis_report
    assert "[結構化驗證事件]" in sections.analysis_report
    # the log-ingestion section stops before the structured-incident block.
    assert "[結構化驗證事件]" not in sections.log_ingestion_summary
    # dynamic values stay attached to their sections.
    assert "INC-20260501-001" in sections.structured_authentication_incident
    assert "F-001" in sections.structured_authentication_incident


def test_bilingual_log_and_auth_titles_parse_into_sections() -> None:
    sections = parse_report_sections(_bilingual_auth_log_output())

    assert "[登入日誌匯入摘要 / Log Ingestion Summary]" in sections.log_ingestion_summary
    assert (
        "[結構化驗證事件 / Structured Authentication Incident]"
        in sections.structured_authentication_incident
    )
    assert "[登入日誌匯入摘要 / Log Ingestion Summary]" in sections.analysis_report
    assert (
        "[結構化驗證事件 / Structured Authentication Incident]" in sections.analysis_report
    )


def test_english_log_and_auth_titles_still_parse() -> None:
    text = "\n\n".join(
        [
            "[Log Ingestion Summary]\nFile: demo_logs/x.log\nTotal Lines: 33",
            "[Structured Authentication Incident]\nRisk Level: HIGH\nDecision: MONITOR",
        ]
    )

    sections = parse_report_sections(text)

    assert "[Log Ingestion Summary]" in sections.log_ingestion_summary
    assert "[Structured Authentication Incident]" in sections.structured_authentication_incident
    assert "Risk Level: HIGH" in sections.analysis_report


def test_empty_text_still_returns_empty_sections() -> None:
    sections = parse_report_sections("plain text without known report headings")

    assert sections.security_triage_report == ""
    assert sections.analysis_report == ""
    assert sections.approved_similar_cases == ""
    assert sections.graph_relationship_explanation == ""


def test_report_section_helpers_do_not_import_streamlit() -> None:
    source = Path("modules/ui/report_sections.py").read_text(encoding="utf-8")

    assert "streamlit" not in source
    assert "streamlit" not in sys.modules
