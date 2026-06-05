"""Lightweight section parsing for existing Sentinel report output.

This module does not import Streamlit or backend runtime components. It only
splits already-rendered text so UI tests stay deterministic and fast.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

SECURITY_TRIAGE_REPORT = "[Security Triage Report]"
LOG_INGESTION_SUMMARY = "[Log Ingestion Summary]"
STRUCTURED_AUTHENTICATION_INCIDENT = "[Structured Authentication Incident]"
APPROVED_SIMILAR_CASES = "[Approved Similar Cases]"
GRAPH_RELATIONSHIP_TITLE = "Graph-Grounded Relationship Explanation:"
SIMULATION_NOTICE_TITLE = "5. Simulation Notice"

KNOWN_TOP_LEVEL_MARKERS = (
    SECURITY_TRIAGE_REPORT,
    LOG_INGESTION_SUMMARY,
    STRUCTURED_AUTHENTICATION_INCIDENT,
    APPROVED_SIMILAR_CASES,
)

DEFAULT_SAFETY_BOUNDARY_TEXT = "\n".join(
    [
        "BLOCK / MONITOR / ALLOW are simulated decisions.",
        (
            "Historical approved cases are advisory references only. They do not override "
            "the current event's deterministic Risk Level or Decision, and they do not "
            "prove compromise or successful execution in the current event."
        ),
        (
            "No real firewall, WAF, EDR, account, password reset, monitoring deployment, "
            "or enforcement action was executed."
        ),
    ]
)

_NUMBERED_SECTION_RE = re.compile(r"^\d+\.\s+")
_CASE_HEADING_RE = re.compile(r"^\d+\.\s+CASE-")


@dataclass(frozen=True)
class ParsedReportSections:
    """Named text slices used by the Streamlit console."""

    security_triage_report: str = ""
    log_ingestion_summary: str = ""
    structured_authentication_incident: str = ""
    approved_similar_cases: str = ""
    graph_relationship_explanation: str = ""
    safety_boundary: str = ""

    @property
    def analysis_report(self) -> str:
        """Return primary analysis sections in display order."""

        return _join_blocks(
            [
                self.security_triage_report,
                self.log_ingestion_summary,
                self.structured_authentication_incident,
            ]
        )


def parse_report_sections(text: str) -> ParsedReportSections:
    """Parse all known display sections from already-rendered backend text."""

    return ParsedReportSections(
        security_triage_report=extract_security_triage_report(text),
        log_ingestion_summary=extract_log_ingestion_summary(text),
        structured_authentication_incident=extract_structured_authentication_incident(text),
        approved_similar_cases=extract_approved_similar_cases(text),
        graph_relationship_explanation=extract_graph_relationship_explanation(text),
        safety_boundary=extract_safety_boundary(text),
    )


def extract_security_triage_report(text: str) -> str:
    return extract_top_level_section(text, SECURITY_TRIAGE_REPORT)


def extract_log_ingestion_summary(text: str) -> str:
    return extract_top_level_section(text, LOG_INGESTION_SUMMARY)


def extract_structured_authentication_incident(text: str) -> str:
    return extract_top_level_section(text, STRUCTURED_AUTHENTICATION_INCIDENT)


def extract_approved_similar_cases(text: str) -> str:
    return extract_top_level_section(text, APPROVED_SIMILAR_CASES)


def extract_top_level_section(text: str, marker: str) -> str:
    """Extract a bracketed top-level section until the next known marker."""

    lines = _lines(text)
    start = _find_line_containing(lines, marker)
    if start is None:
        return ""

    block = [_line_from_marker(lines[start], marker)]
    for line in lines[start + 1 :]:
        if _contains_other_top_level_marker(line, marker):
            break
        block.append(line.rstrip())
    return _strip_block(block)


def extract_graph_relationship_explanation(text: str) -> str:
    """Extract one or more nested graph-grounded relationship blocks."""

    lines = _lines(text)
    blocks: list[str] = []
    for index, line in enumerate(lines):
        if GRAPH_RELATIONSHIP_TITLE.casefold() not in line.casefold():
            continue
        block = [_line_from_marker(line, GRAPH_RELATIONSHIP_TITLE)]
        for following in lines[index + 1 :]:
            stripped = following.strip()
            if not stripped:
                break
            if _is_graph_block_boundary(stripped):
                break
            block.append(following.rstrip())
        rendered = _strip_block(block)
        if rendered:
            blocks.append(rendered)
    return _join_blocks(blocks)


def extract_safety_boundary(text: str) -> str:
    """Extract simulation and advisory boundary text that already exists in output."""

    blocks = [extract_simulation_notice(text)]
    boundary_lines = [line.strip() for line in _lines(text) if _is_safety_boundary_line(line)]
    blocks.extend(_dedupe(boundary_lines))
    return _join_blocks(blocks)


def extract_simulation_notice(text: str) -> str:
    """Extract the numbered Simulation Notice section when present."""

    lines = _lines(text)
    start = _find_line_containing(lines, SIMULATION_NOTICE_TITLE)
    if start is None:
        return ""

    block = [_line_from_marker(lines[start], SIMULATION_NOTICE_TITLE)]
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if _contains_any_top_level_marker(line):
            break
        if _NUMBERED_SECTION_RE.match(stripped) and not stripped.startswith(SIMULATION_NOTICE_TITLE):
            break
        block.append(line.rstrip())
    return _strip_block(block)


def build_safety_boundary_text(text: str) -> str:
    """Return parsed safety text plus the UI's always-visible safety boundary."""

    return _join_blocks([extract_safety_boundary(text), DEFAULT_SAFETY_BOUNDARY_TEXT])


def has_graph_relationship_explanation(text: str) -> bool:
    return bool(extract_graph_relationship_explanation(text))


def has_approved_similar_cases(text: str) -> bool:
    return bool(extract_approved_similar_cases(text))


def _lines(text: str) -> list[str]:
    return str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _find_line_containing(lines: list[str], marker: str) -> int | None:
    needle = marker.casefold()
    for index, line in enumerate(lines):
        if needle in line.casefold():
            return index
    return None


def _line_from_marker(line: str, marker: str) -> str:
    lowered = line.casefold()
    marker_lowered = marker.casefold()
    start = lowered.find(marker_lowered)
    if start == -1:
        return line.strip()
    return f"{marker}{line[start + len(marker):]}".rstrip()


def _contains_other_top_level_marker(line: str, current_marker: str) -> bool:
    lowered = line.casefold()
    return any(
        marker != current_marker and marker.casefold() in lowered
        for marker in KNOWN_TOP_LEVEL_MARKERS
    )


def _contains_any_top_level_marker(line: str) -> bool:
    lowered = line.casefold()
    return any(marker.casefold() in lowered for marker in KNOWN_TOP_LEVEL_MARKERS)


def _is_graph_block_boundary(stripped_line: str) -> bool:
    if _contains_any_top_level_marker(stripped_line):
        return True
    if _CASE_HEADING_RE.match(stripped_line):
        return True
    return stripped_line.startswith(
        (
            "Analyst conclusion:",
            "Outcome note:",
            "Source:",
            "Similarity reasons:",
            "Key differences / missing evidence to check:",
        )
    )


def _is_safety_boundary_line(line: str) -> bool:
    lowered = line.casefold()
    terms = (
        "simulated decision",
        "simulated decisions",
        "historical approved cases are advisory references only",
        "do not override",
        "do not prove compromise",
        "do not prove account compromise",
        "do not prove current command execution",
        "failure-then-success authentication is suspicious",
        "no real firewall",
        "no real monitoring deployment",
        "no real enforcement",
        "no real blocking",
        "password reset",
        "account disablement",
    )
    return any(term in lowered for term in terms)


def _strip_block(lines: list[str]) -> str:
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def _join_blocks(blocks: list[str]) -> str:
    return "\n\n".join(block.strip() for block in blocks if block and block.strip())


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
