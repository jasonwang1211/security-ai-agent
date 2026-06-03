from pathlib import Path

from modules.evidence_correlator import correlate_auth_sequence
from modules.graph.builder import build_graph_snapshot
from modules.graph.explainers import explain_graph_reference
from modules.incident_exporter import (
    incident_to_json_dict,
    incident_to_json_string,
    validate_incident_json_dict,
)
from modules.llm_assist import LLMAssist
from modules.log_pipeline import normalize_event, parse_log_line
from modules.rag_types import AnswerWithSources, SourceCitation
from modules.report_followup import answer_report_followup, combine_hybrid_explanation_protected


SCENARIO_A_LOG = Path("demo_logs/scenario_a_mixed_auth.log")


def test_scenario_a_mixed_auth_log_end_to_end():
    lines = [
        line.strip()
        for line in SCENARIO_A_LOG.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    events = [normalize_event(parse_log_line(line)) for line in lines]

    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)

    assert incident is not None
    assert incident.id.startswith("INC-")
    assert incident.status == "SUSPICIOUS"
    assert incident.risk_level == "HIGH"
    assert incident.decision == "MONITOR"
    assert incident.attack_type == "Possible Account Compromise"
    assert incident.findings[0].finding_type == "possible_account_compromise"
    assert {"EV-001", "EV-002", "EV-003"}.issubset(incident.evidence_bundle.available_ids)
    assert incident.evidence_bundle.get("EV-003") is not None
    assert incident.evidence_bundle.get("EV-003").type == "success_after_failures"

    exported = incident_to_json_dict(incident)
    json_output = incident_to_json_string(incident)

    assert validate_incident_json_dict(exported) is True
    assert incident.id in json_output
    assert "possible_account_compromise" in json_output

    evidence_answer = answer_report_followup("EV-003 是什麼意思？", incident)

    assert "EV-003" in evidence_answer["referenced_evidence"]
    assert "EV-003" in str(evidence_answer["answer"])

    graph_snapshot = build_graph_snapshot(incident)
    graph_answer = explain_graph_reference(graph_snapshot, "EV-003")

    assert "EV-003" in graph_answer.answer
    assert "F-001" in graph_answer.answer
    assert "EV-003" in graph_answer.evidence_ids
    assert "F-001" in graph_answer.finding_ids
    assert any("EV-003" in str(source.model_dump(mode="json")) for source in graph_answer.sources)

    decision_answer = answer_report_followup("為什麼是 MONITOR？", incident)

    assert "MONITOR" in str(decision_answer["answer"])
    assert any("risk_level_decision.md" in doc for doc in decision_answer["referenced_docs"])

    assessment, guardrail_result = LLMAssist().assess_evidence_with_guardrails(
        incident.evidence_bundle,
        incident.findings[0],
    )

    assert assessment.metadata["advisory_only"] is True
    assert guardrail_result.valid is True
    assert incident.decision == "MONITOR"


def test_scenario_a_hybrid_graph_and_curated_auth_context_stays_monitor():
    lines = [
        line.strip()
        for line in SCENARIO_A_LOG.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    events = [normalize_event(parse_log_line(line)) for line in lines]
    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)
    assert incident is not None
    before_incident = incident.model_dump(mode="json")

    graph_snapshot = build_graph_snapshot(incident)
    graph_answer = explain_graph_reference(graph_snapshot, "EV-003")
    knowledge_answer = AnswerWithSources(
        answer=(
            "Curated authentication KB explains success_after_failures as suspicious "
            "but still requiring analyst review; MONITOR remains a simulated decision."
        ),
        sources=[
            SourceCitation(
                source="knowledge/blue_team/report_explainer/success_after_failures.md",
                kind="knowledge_doc",
                identifier="report.success_after_failures",
            )
        ],
        confidence="MEDIUM",
        limitations=["Curated authentication knowledge source context only."],
    )
    assert knowledge_answer.evidence_ids == []
    assert knowledge_answer.finding_ids == []

    result = combine_hybrid_explanation_protected(
        graph_answer,
        knowledge_answer,
        known_evidence_ids=set(incident.evidence_bundle.available_ids),
        known_finding_ids={finding.id for finding in incident.findings},
    )

    assert not result.was_fallback
    assert any(source.source.startswith("graph:") for source in result.answer.sources)
    assert any(source.identifier == "report.success_after_failures" for source in result.answer.sources)
    assert result.answer.evidence_ids == ["EV-003"]
    assert result.answer.finding_ids == ["F-001"]
    assert "MONITOR" in result.answer.answer
    assert incident.decision == "MONITOR"
    assert incident.model_dump(mode="json") == before_incident
    assert not any(
        (
            edge.source_node_id.startswith("KNOWLEDGE_DOC:")
            and (edge.target_node_id.startswith("EV-") or edge.target_node_id.startswith("F-"))
        )
        or (
            edge.target_node_id.startswith("KNOWLEDGE_DOC:")
            and (edge.source_node_id.startswith("EV-") or edge.source_node_id.startswith("F-"))
        )
        for edge in graph_snapshot.edges
    )
