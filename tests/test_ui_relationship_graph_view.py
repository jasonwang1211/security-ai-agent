import sys
from pathlib import Path

from modules.ui.console_state import ActiveContextSummary
from modules.ui.relationship_graph_view import (
    EMPTY_RELATIONSHIP_GRAPH_MESSAGE,
    HAS_ATTACK_TYPE,
    HAS_DECISION,
    HAS_EVIDENCE,
    HAS_RISK,
    MATCHED_RULE,
    SHARES_ATTACK_TYPE,
    SHARES_EVIDENCE,
    SHARES_RULE,
    SIMILAR_TO,
    build_relationship_graph_display,
)


def _event_summary(
    *,
    attack_type: str = "Command Injection",
    rule_ids: str = "CMD-001",
    risk_level: str = "HIGH",
    decision: str = "BLOCK",
) -> ActiveContextSummary:
    return ActiveContextSummary(
        kind="event",
        title="Payload/Event",
        risk_level=risk_level,
        decision=decision,
        details=(f"Attack Type: {attack_type}", f"Rule IDs: {rule_ids}"),
    )


def _auth_summary() -> ActiveContextSummary:
    return ActiveContextSummary(
        kind="incident",
        title="Authentication Incident",
        risk_level="HIGH",
        decision="MONITOR",
        details=(
            "Incident ID: INC-20260605-001",
            "Attack Type: Possible Account Compromise",
            "Evidence IDs: EV-001, EV-003",
        ),
    )


def _labels(display) -> set[str]:
    return {node.label for node in display.nodes}


def _edge_labels(display) -> set[str]:
    return {edge.label for edge in display.edges}


def test_no_active_context_returns_empty_graph_with_safe_message() -> None:
    display = build_relationship_graph_display(
        active_context_summary=ActiveContextSummary(
            kind="",
            title="No active context",
            risk_level="",
            decision="",
            details=(),
        ),
        approved_similar_cases_text="",
        graph_relationship_text="",
    )

    assert display.nodes == ()
    assert display.edges == ()
    assert display.dot == ""
    assert display.empty_message == EMPTY_RELATIONSHIP_GRAPH_MESSAGE


def test_command_injection_context_creates_current_feature_nodes_and_edges() -> None:
    display = build_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
    )

    labels = _labels(display)
    assert {"Current Event", "Command Injection", "CMD-001", "HIGH", "BLOCK"}.issubset(
        labels
    )
    assert {HAS_ATTACK_TYPE, MATCHED_RULE, HAS_RISK, HAS_DECISION}.issubset(
        _edge_labels(display)
    )


def test_command_injection_similar_case_adds_case_and_shared_feature_edges() -> None:
    similar_cases_text = "\n".join(
        [
            "[Approved Similar Cases]",
            "1. CASE-SEED-001 - Command Injection Payload",
            (
                "   Similarity reasons: matched attack_types: Command Injection, "
                "matched rule_ids: CMD-001, matched evidence_types: "
                "shell_metacharacter_payload, supporting decision match: BLOCK"
            ),
        ]
    )
    graph_text = "\n".join(
        [
            "Graph-Grounded Relationship Explanation:",
            "Current context shares attack type Command Injection with CASE-SEED-001.",
            "Current context shares rule ID CMD-001 with CASE-SEED-001.",
            (
                "Current context shares evidence type shell_metacharacter_payload "
                "with CASE-SEED-001."
            ),
        ]
    )

    display = build_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=similar_cases_text,
        graph_relationship_text=graph_text,
    )

    labels = _labels(display)
    assert "CASE-SEED-001" in labels
    assert "shell_metacharacter_payload" in labels
    assert {SIMILAR_TO, SHARES_ATTACK_TYPE, SHARES_RULE, SHARES_EVIDENCE}.issubset(
        _edge_labels(display)
    )
    assert HAS_EVIDENCE in _edge_labels(display)


def test_auth_incident_context_creates_incident_finding_evidence_and_decision_nodes() -> None:
    similar_cases_text = "\n".join(
        [
            "[Approved Similar Cases]",
            "1. CASE-SEED-002 - Authentication Success After Failures",
            (
                "   Similarity reasons: matched attack_types: Possible Account Compromise, "
                "matched finding_types: possible_account_compromise, matched evidence_types: "
                "auth_failure_sequence, success_after_failures, supporting decision match: MONITOR"
            ),
        ]
    )

    display = build_relationship_graph_display(
        active_context_summary=_auth_summary(),
        approved_similar_cases_text=similar_cases_text,
        graph_relationship_text="",
    )

    labels = _labels(display)
    assert "Current Incident" in labels
    assert "Possible Account Compromise" in labels
    assert "possible_account_compromise" in labels
    assert "success_after_failures" in labels
    assert "MONITOR" in labels
    assert "CASE-SEED-002" in labels


def test_dot_output_contains_expected_graph_syntax_and_labels() -> None:
    display = build_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="1. CASE-SEED-001 - Command Injection Payload",
        graph_relationship_text="",
    )

    assert "digraph RelationshipGraph" in display.dot
    assert "rankdir=LR" in display.dot
    assert 'label="Current Event"' in display.dot
    assert 'label="CASE-SEED-001"' in display.dot


def test_dot_output_escapes_quotes_safely() -> None:
    display = build_relationship_graph_display(
        active_context_summary=_event_summary(attack_type='Command "Injection"'),
        approved_similar_cases_text="",
        graph_relationship_text="",
    )

    assert 'label="Command \\"Injection\\""' in display.dot


def test_graph_notes_include_advisory_no_override_and_no_enforcement_boundaries() -> None:
    display = build_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
    )

    notes = " ".join(display.notes).casefold()
    assert "advisory" in notes
    assert "does not override" in notes
    assert "no real enforcement" in notes


def test_relationship_graph_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/relationship_graph_view.py").read_text(encoding="utf-8")

    assert "import streamlit" not in source.lower()
    assert "streamlit" not in sys.modules
