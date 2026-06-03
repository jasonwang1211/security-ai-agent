import subprocess
import sys
from pathlib import Path

from modules.detection_rules import DetectionRule
from modules.evidence_correlator import correlate_auth_sequence
from modules.graph.knowledge_doc_seed import build_knowledge_doc_seed
from modules.graph.types import GraphEdge, GraphEdgeKind, GraphNode, GraphNodeKind, GraphSnapshot
from modules.rag_metadata import KnowledgeDocMetadata
from modules.rag_types import AnswerWithSources, SourceCitation
from modules.report_followup import (
    ProtectedExplanationResult,
    answer_report_followup,
    combine_hybrid_explanation_protected,
    extract_evidence_ids,
    extract_finding_ids,
    explain_graph_followup_protected,
    explain_report_followup_protected,
    explain_rule_followup_protected,
    classify_followup_intent,
    lookup_evidence,
    lookup_finding,
    protect_answer_with_guardrails,
    suggest_followups,
)
from modules.types import Incident


def make_auth_event(event_type: str, timestamp: str) -> dict:
    return {
        "event_type": event_type,
        "source_ip": "10.0.0.5",
        "target": "/login",
        "user": "admin",
        "timestamp": timestamp,
        "raw": f"{timestamp} {event_type} src_ip=10.0.0.5 user=admin endpoint=/login",
    }


def make_incident() -> Incident:
    events = [
        make_auth_event("auth_failure", "2026-05-01T10:00:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:01:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:02:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:03:00Z"),
        make_auth_event("auth_failure", "2026-05-01T10:04:00Z"),
        make_auth_event("auth_success", "2026-05-01T10:04:30Z"),
    ]
    incident = correlate_auth_sequence(events, failure_threshold=5, window_minutes=5)
    assert incident is not None
    return incident


def make_source() -> SourceCitation:
    return SourceCitation(source="knowledge/example.md", kind="knowledge_doc")


def make_internal_safety_source() -> SourceCitation:
    return SourceCitation(
        source="internal/answer_guardrails",
        kind="knowledge_doc",
        heading="Protected fallback",
        identifier="answer_guardrails",
    )


def make_answer(
    text: str,
    *,
    sources: list[SourceCitation] | None = None,
    rule_ids: list[str] | None = None,
    limitations: list[str] | None = None,
) -> AnswerWithSources:
    return AnswerWithSources(
        answer=text,
        sources=sources or [make_source()],
        rule_ids=rule_ids or [],
        confidence="MEDIUM",
        limitations=limitations or [],
    )


def make_auth_hybrid_graph_answer(text: str = "EV-003 explicitly supports F-001.") -> AnswerWithSources:
    return AnswerWithSources(
        answer=text,
        sources=[
            SourceCitation(
                source="graph:EDGE:SUPPORTED_BY:F-001->EV-003",
                kind="incident_evidence",
                heading="SUPPORTED_BY",
                identifier="EDGE:SUPPORTED_BY:F-001->EV-003",
            )
        ],
        evidence_ids=["EV-003"],
        finding_ids=["F-001"],
        confidence="HIGH",
        limitations=["Graph explanation uses explicit in-memory graph edges only."],
    )


def make_auth_hybrid_knowledge_answer(
    text: str = "Curated KB explains success_after_failures and the simulated MONITOR boundary.",
) -> AnswerWithSources:
    return AnswerWithSources(
        answer=text,
        sources=[
            SourceCitation(
                source="knowledge/blue_team/report_explainer/success_after_failures.md",
                kind="knowledge_doc",
                identifier="report.success_after_failures",
            )
        ],
        confidence="MEDIUM",
        limitations=["Curated knowledge source context only."],
    )


def make_command_hybrid_graph_answer(text: str = "KnowledgeDoc seed maps CMD-001 to Command Injection.") -> AnswerWithSources:
    return AnswerWithSources(
        answer=text,
        sources=[
            SourceCitation(
                source="graph:EDGE:MAPS_TO_RULE:KNOWLEDGE_DOC:report.command_injection_explainer->DETECTION_RULE:CMD-001",
                kind="knowledge_doc",
                heading="MAPS_TO_RULE",
                identifier="EDGE:MAPS_TO_RULE:KNOWLEDGE_DOC:report.command_injection_explainer->DETECTION_RULE:CMD-001",
            )
        ],
        rule_ids=["CMD-001"],
        confidence="HIGH",
        limitations=["KnowledgeDoc seed uses reviewed metadata and supplied DetectionRule objects only."],
    )


def make_command_hybrid_knowledge_answer(
    text: str = "Curated KB explains CMD-001; BLOCK remains simulated.",
) -> AnswerWithSources:
    return AnswerWithSources(
        answer=text,
        sources=[
            SourceCitation(
                source="knowledge/blue_team/report_explainer/command_injection_explainer.md",
                kind="knowledge_doc",
                identifier="report.command_injection_explainer",
            )
        ],
        rule_ids=["CMD-001"],
        confidence="MEDIUM",
        limitations=["Curated knowledge source context only."],
    )


def make_answer_without_sources(text: str) -> AnswerWithSources:
    return AnswerWithSources.model_construct(
        answer=text,
        sources=[],
        evidence_ids=[],
        finding_ids=[],
        rule_ids=[],
        confidence="MEDIUM",
        limitations=[],
    )


def make_report_metadata() -> KnowledgeDocMetadata:
    return KnowledgeDocMetadata(
        doc_id="report.risk_level_decision",
        doc_type="report_explainer",
        applies_to=["Security Triage Report"],
        keywords=["decision", "monitor", "risk"],
        source_path="knowledge/blue_team/report_explainer/risk_level_decision.md",
    )


def make_rule_metadata(rule_id: str = "CMD-001") -> KnowledgeDocMetadata:
    return KnowledgeDocMetadata(
        doc_id=f"rule.{rule_id.lower()}",
        doc_type="detection_rule",
        keywords=["command injection", "rule"],
        rule_ids=[rule_id],
        source_path="detections/blue_team/command_injection.yml",
    )


def make_command_injection_doc_metadata() -> KnowledgeDocMetadata:
    return KnowledgeDocMetadata(
        doc_id="report.command_injection_explainer",
        doc_type="report_explainer",
        title="Command Injection 攻擊判讀",
        review_status="approved_for_runtime_promotion",
        attack_types=["Command Injection"],
        rule_ids=["CMD-001"],
        source_path="knowledge/blue_team/report_explainer/command_injection_explainer.md",
    )


def make_command_injection_rule() -> DetectionRule:
    return DetectionRule(
        id="CMD-001",
        title="Basic Command Injection Indicators",
        attack_type="Command Injection",
        severity="HIGH",
        confidence=0.9,
        patterns=["; rm "],
        source_path="detections/blue_team/command_injection/command_injection_basic.yml",
    )


def make_graph_snapshot() -> GraphSnapshot:
    return GraphSnapshot(
        nodes=[
            GraphNode(id="EV-003", kind=GraphNodeKind.EVIDENCE, label="Successful login"),
            GraphNode(id="F-001", kind=GraphNodeKind.FINDING, label="Possible account compromise"),
            GraphNode(id="DETECTION_RULE:CMD-001", kind=GraphNodeKind.DETECTION_RULE, label="Command injection rule"),
            GraphNode(id="ATTACK_TYPE:Command Injection", kind=GraphNodeKind.ATTACK_TYPE, label="Command Injection"),
            GraphNode(id="RISK_LEVEL:HIGH", kind=GraphNodeKind.RISK_LEVEL, label="HIGH"),
            GraphNode(id="DECISION:MONITOR", kind=GraphNodeKind.DECISION, label="MONITOR"),
        ],
        edges=[
            GraphEdge(
                id="EDGE:SUPPORTED_BY:F-001->EV-003",
                kind=GraphEdgeKind.SUPPORTED_BY,
                source_node_id="F-001",
                target_node_id="EV-003",
            ),
            GraphEdge(
                id="EDGE:MAPS_TO_RULE:F-001->DETECTION_RULE:CMD-001",
                kind=GraphEdgeKind.MAPS_TO_RULE,
                source_node_id="F-001",
                target_node_id="DETECTION_RULE:CMD-001",
            ),
            GraphEdge(
                id="EDGE:DETECTS:DETECTION_RULE:CMD-001->ATTACK_TYPE:Command Injection",
                kind=GraphEdgeKind.DETECTS,
                source_node_id="DETECTION_RULE:CMD-001",
                target_node_id="ATTACK_TYPE:Command Injection",
            )
        ],
    )


def test_extract_evidence_ids_preserves_order_and_removes_duplicates():
    assert extract_evidence_ids("EV-003 是什麼？EV-001 和 EV-003") == [
        "EV-003",
        "EV-001",
    ]


def test_extract_finding_ids_normalizes_lowercase():
    assert extract_finding_ids("f-001 是什麼？") == ["F-001"]


def test_classify_followup_intent_detects_explain_evidence():
    assert classify_followup_intent("EV-003 是什麼意思？") == "explain_evidence"


def test_classify_followup_intent_detects_why_decision():
    assert classify_followup_intent("為什麼是 MONITOR 不是 BLOCK？") == "why_decision"


def test_classify_followup_intent_detects_next_steps():
    assert classify_followup_intent("我接下來要查什麼？") == "next_steps"


def test_lookup_evidence_returns_item():
    incident = make_incident()

    evidence = lookup_evidence(incident, "EV-003")

    assert evidence is not None
    assert evidence.type == "success_after_failures"


def test_lookup_evidence_returns_none_for_missing_id():
    assert lookup_evidence(make_incident(), "EV-999") is None


def test_lookup_finding_returns_finding():
    finding = lookup_finding(make_incident(), "F-001")

    assert finding is not None
    assert finding.finding_type == "possible_account_compromise"


def test_answer_report_followup_for_evidence_id():
    incident = make_incident()
    original_decision = incident.decision

    response = answer_report_followup("EV-003 是什麼意思？", incident)

    assert "EV-003" in str(response["answer"])
    assert "EV-003" in response["referenced_evidence"]
    assert response["confidence"] in ("high", "medium")
    assert incident.decision == original_decision


def test_answer_report_followup_for_why_monitor():
    response = answer_report_followup("為什麼是 MONITOR 不是 BLOCK？", make_incident())

    assert "MONITOR" in str(response["answer"])
    assert "analyst review" in str(response["answer"]) or "simulated" in str(response["answer"])
    assert any("risk_level_decision.md" in doc for doc in response["referenced_docs"])


def test_answer_report_followup_for_next_steps():
    response = answer_report_followup("我接下來要查什麼？", make_incident())
    answer = str(response["answer"]).lower()

    assert any(term in answer for term in ("check", "review", "log", "source_ip", "user"))
    assert any("investigation_checklist.md" in doc for doc in response["referenced_docs"])


def test_answer_report_followup_for_unknown_evidence_id():
    response = answer_report_followup("EV-999 是什麼？", make_incident())

    assert response["confidence"] in ("insufficient", "low")
    assert "找不到 EV-999" in str(response["answer"])


def test_suggest_followups_returns_static_suggestions():
    suggestions = suggest_followups("why_decision")

    assert suggestions
    assert any("BLOCK" in suggestion for suggestion in suggestions)


def test_protect_answer_with_guardrails_returns_original_safe_answer():
    answer = make_answer(
        "MONITOR is a simulated decision selected by deterministic policy for review."
    )

    result = protect_answer_with_guardrails(answer)

    assert isinstance(result, ProtectedExplanationResult)
    assert result.answer is answer
    assert not result.was_fallback
    assert not result.safety_report.has_errors()
    assert not any(source.source == "internal/answer_guardrails" for source in result.answer.sources)


def test_protect_answer_with_guardrails_returns_fallback_for_real_enforcement_claim():
    answer = make_answer("The firewall blocked the attacker in production.")

    result = protect_answer_with_guardrails(answer)

    assert result.was_fallback
    assert result.safety_report.has_errors()
    assert "未通過安全檢查" in result.answer.answer


def test_protected_fallback_has_limitations():
    answer = make_answer("The firewall blocked the attacker in production.")

    result = protect_answer_with_guardrails(answer)

    assert result.answer.limitations
    assert any("AnswerGuardrails" in limitation for limitation in result.answer.limitations)


def test_protected_fallback_appends_internal_safety_citation_when_original_sources_exist():
    answer = make_answer("The firewall blocked the attacker in production.")

    result = protect_answer_with_guardrails(answer)

    assert result.answer.sources[0].source == "knowledge/example.md"
    assert any(
        source.source == "internal/answer_guardrails"
        and source.identifier == "answer_guardrails"
        and source.heading == "Protected fallback"
        for source in result.answer.sources
    )


def test_protected_fallback_uses_internal_safety_citation_when_sources_are_absent():
    answer = make_answer_without_sources("The firewall blocked the attacker in production.")

    result = protect_answer_with_guardrails(answer)

    assert [source.source for source in result.answer.sources] == ["internal/answer_guardrails"]
    assert result.answer.sources[0].identifier == "answer_guardrails"


def test_protected_fallback_does_not_duplicate_internal_safety_citation():
    answer = make_answer(
        "The firewall blocked the attacker in production.",
        sources=[make_source(), make_internal_safety_source()],
    )

    result = protect_answer_with_guardrails(answer)

    assert [
        source.source for source in result.answer.sources
        if source.source == "internal/answer_guardrails"
    ] == ["internal/answer_guardrails"]


def test_protected_fallback_uses_conservative_wording():
    answer = make_answer("The firewall blocked the attacker in production.")

    result = protect_answer_with_guardrails(answer)

    assert "保守說明" in result.answer.answer
    assert "原始報告證據" in result.answer.answer
    assert "人工複核" in result.answer.answer


def test_protected_fallback_does_not_claim_real_enforcement():
    answer = make_answer("The firewall blocked the attacker in production.")

    result = protect_answer_with_guardrails(answer)

    assert "firewall blocked" not in result.answer.answer.casefold()
    assert "real firewall" not in result.answer.answer.casefold()
    assert "production enforcement action was performed" not in result.answer.answer.casefold()
    assert "confirmed compromise" not in result.answer.answer.casefold()
    assert "rag detected" not in result.answer.answer.casefold()
    assert "llm changed" not in result.answer.answer.casefold()


def test_protected_fallback_preserves_safety_report_error_findings():
    answer = make_answer("The firewall blocked the attacker in production.")

    result = protect_answer_with_guardrails(answer)

    assert result.was_fallback
    assert result.safety_report.findings_by_rule("real_enforcement_claim")
    assert result.safety_report.findings_by_rule("real_enforcement_claim")[0].severity == "ERROR"


def test_explain_graph_followup_protected_returns_result():
    result = explain_graph_followup_protected(make_graph_snapshot(), "EV-003")

    assert isinstance(result, ProtectedExplanationResult)
    assert isinstance(result.answer, AnswerWithSources)


def test_explain_graph_followup_protected_safe_answer_does_not_fallback():
    result = explain_graph_followup_protected(make_graph_snapshot(), "EV-003")

    assert not result.was_fallback
    assert result.safety_report.is_safe
    assert "F-001" in result.answer.answer


def test_explain_graph_followup_protected_accepts_prefixed_rule_reference():
    result = explain_graph_followup_protected(make_graph_snapshot(), "DETECTION_RULE:CMD-001")

    assert not result.was_fallback
    assert result.safety_report.is_safe
    assert result.answer.rule_ids == ["CMD-001"]
    assert "F-001" in result.answer.answer
    assert "Command Injection" in result.answer.answer


def test_existing_guardrails_still_fallback_for_unsafe_graph_like_answer():
    answer = AnswerWithSources(
        answer="Graph context says the firewall blocked the attacker in production.",
        sources=[SourceCitation(source="graph:EDGE-1", kind="incident_evidence")],
        evidence_ids=["EV-999"],
        confidence="MEDIUM",
    )

    result = protect_answer_with_guardrails(answer, known_evidence_ids={"EV-003"})

    assert result.was_fallback
    assert result.safety_report.findings_by_rule("real_enforcement_claim")
    assert result.safety_report.findings_by_rule("invented_evidence_id")


def test_graph_followup_does_not_mutate_risk_or_decision_nodes():
    snapshot = make_graph_snapshot()
    before = snapshot.model_dump(mode="json")

    explain_graph_followup_protected(snapshot, "EV-003")

    assert snapshot.model_dump(mode="json") == before
    assert [node.label for node in snapshot.nodes if node.kind == GraphNodeKind.RISK_LEVEL] == ["HIGH"]
    assert [node.label for node in snapshot.nodes if node.kind == GraphNodeKind.DECISION] == ["MONITOR"]


def test_explain_report_followup_protected_returns_result():
    result = explain_report_followup_protected(
        "Why is the decision MONITOR?",
        [make_report_metadata()],
    )

    assert isinstance(result, ProtectedExplanationResult)
    assert isinstance(result.answer, AnswerWithSources)


def test_explain_report_followup_protected_has_source_citations():
    result = explain_report_followup_protected(
        "Why is the decision MONITOR?",
        [make_report_metadata()],
    )

    assert result.answer.sources
    assert result.answer.sources[0].identifier == "report.risk_level_decision"


def test_explain_report_followup_protected_passes_guardrails_for_monitor_question():
    result = explain_report_followup_protected(
        "Why is the decision MONITOR?",
        [make_report_metadata()],
    )

    assert not result.was_fallback
    assert result.safety_report.is_safe
    assert not result.safety_report.has_errors()


def test_explain_rule_followup_protected_returns_result():
    result = explain_rule_followup_protected(
        "Explain CMD-001.",
        [make_rule_metadata()],
    )

    assert isinstance(result, ProtectedExplanationResult)
    assert isinstance(result.answer, AnswerWithSources)


def test_explain_rule_followup_protected_preserves_rule_ids_when_metadata_is_provided():
    result = explain_rule_followup_protected(
        "Explain CMD-001.",
        [make_rule_metadata()],
        rule_metadata={"CMD-001": {"attack_type": "Command Injection"}},
        known_rule_ids={"CMD-001"},
    )

    assert not result.was_fallback
    assert result.answer.rule_ids == ["CMD-001"]


def test_explain_rule_followup_protected_fallback_for_invented_rule_id():
    result = explain_rule_followup_protected(
        "Explain CMD-999.",
        [make_rule_metadata("CMD-999")],
        rule_metadata={"CMD-999": {"attack_type": "Command Injection"}},
        known_rule_ids={"CMD-001"},
    )

    assert result.was_fallback
    assert result.safety_report.findings_by_rule("invented_rule_id")
    assert result.answer.rule_ids == []


def test_combine_hybrid_explanation_protected_combines_graph_and_knowledge_answers():
    result = combine_hybrid_explanation_protected(
        make_auth_hybrid_graph_answer(),
        make_auth_hybrid_knowledge_answer(),
        known_evidence_ids={"EV-003"},
        known_finding_ids={"F-001"},
    )

    assert isinstance(result, ProtectedExplanationResult)
    assert not result.was_fallback
    assert "明確圖譜脈絡" in result.answer.answer
    assert "整理後知識脈絡" in result.answer.answer
    assert result.answer.evidence_ids == ["EV-003"]
    assert result.answer.finding_ids == ["F-001"]
    assert result.answer.rule_ids == []


def test_combine_hybrid_explanation_protected_retains_both_citation_types():
    result = combine_hybrid_explanation_protected(
        make_auth_hybrid_graph_answer(),
        make_auth_hybrid_knowledge_answer(),
        known_evidence_ids={"EV-003"},
        known_finding_ids={"F-001"},
    )

    assert [source.source for source in result.answer.sources] == [
        "graph:EDGE:SUPPORTED_BY:F-001->EV-003",
        "knowledge/blue_team/report_explainer/success_after_failures.md",
    ]


def test_combine_hybrid_explanation_protected_deduplicates_rule_ids():
    result = combine_hybrid_explanation_protected(
        make_command_hybrid_graph_answer(),
        make_command_hybrid_knowledge_answer(),
        known_rule_ids={"CMD-001"},
    )

    assert result.answer.rule_ids == ["CMD-001"]


def test_combine_hybrid_explanation_protected_fallbacks_for_unsafe_combined_answer():
    result = combine_hybrid_explanation_protected(
        make_auth_hybrid_graph_answer(),
        make_auth_hybrid_knowledge_answer("The firewall blocked the attacker in production."),
        known_evidence_ids={"EV-003"},
        known_finding_ids={"F-001"},
    )

    assert result.was_fallback
    assert result.safety_report.findings_by_rule("real_enforcement_claim")
    assert "firewall blocked" not in result.answer.answer.casefold()


def test_combine_hybrid_explanation_protected_does_not_mutate_inputs():
    graph_answer = make_auth_hybrid_graph_answer()
    knowledge_answer = make_auth_hybrid_knowledge_answer()
    before_graph = graph_answer.model_dump(mode="json")
    before_knowledge = knowledge_answer.model_dump(mode="json")

    combine_hybrid_explanation_protected(
        graph_answer,
        knowledge_answer,
        known_evidence_ids={"EV-003"},
        known_finding_ids={"F-001"},
    )

    assert graph_answer.model_dump(mode="json") == before_graph
    assert knowledge_answer.model_dump(mode="json") == before_knowledge


def test_combine_hybrid_explanation_protected_is_assembly_only_boundary():
    result = combine_hybrid_explanation_protected(
        make_auth_hybrid_graph_answer("Graph context says Decision remains simulated MONITOR."),
        make_auth_hybrid_knowledge_answer("Curated KB says MONITOR is simulated only."),
        known_evidence_ids={"EV-003"},
        known_finding_ids={"F-001"},
    )

    assert not result.was_fallback
    assert "不會自行檢索資料，也不會改變 Risk Level 或 Decision" in result.answer.answer
    assert "firewall blocked" not in result.answer.answer.casefold()
    assert "production enforcement" not in result.answer.answer.casefold()


def test_command_injection_seed_and_hybrid_answer_keep_simulated_block_boundary():
    seed = build_knowledge_doc_seed(
        [make_command_injection_doc_metadata()],
        [make_command_injection_rule()],
    )

    assert {node.id for node in seed.nodes} == {
        "KNOWLEDGE_DOC:report.command_injection_explainer",
        "ATTACK_TYPE:Command Injection",
        "DETECTION_RULE:CMD-001",
    }
    assert {
        (edge.kind, edge.source_node_id, edge.target_node_id)
        for edge in seed.edges
    } == {
        (
            GraphEdgeKind.RELATED_TO_ATTACK,
            "KNOWLEDGE_DOC:report.command_injection_explainer",
            "ATTACK_TYPE:Command Injection",
        ),
        (
            GraphEdgeKind.MAPS_TO_RULE,
            "KNOWLEDGE_DOC:report.command_injection_explainer",
            "DETECTION_RULE:CMD-001",
        ),
    }

    rule_edge = next(edge for edge in seed.edges if edge.kind == GraphEdgeKind.MAPS_TO_RULE)
    graph_answer = AnswerWithSources(
        answer="KnowledgeDoc seed maps CMD-001 to Command Injection. Decision remains simulated BLOCK.",
        sources=[
            SourceCitation(
                source=f"graph:{rule_edge.id}",
                kind="knowledge_doc",
                heading=rule_edge.kind.value,
                identifier=rule_edge.id,
                metadata={"edge": rule_edge.model_dump(mode="json")},
            )
        ],
        rule_ids=["CMD-001"],
        confidence="HIGH",
        limitations=["KnowledgeDoc seed uses reviewed metadata and supplied DetectionRule objects only."],
    )
    result = combine_hybrid_explanation_protected(
        graph_answer,
        make_command_hybrid_knowledge_answer(),
        known_rule_ids={"CMD-001"},
    )

    assert not result.was_fallback
    assert any(source.source.startswith("graph:EDGE:MAPS_TO_RULE") for source in result.answer.sources)
    assert any(source.identifier == "report.command_injection_explainer" for source in result.answer.sources)
    assert "simulated BLOCK" in result.answer.answer
    assert "firewall blocked" not in result.answer.answer.casefold()


def test_protected_helpers_do_not_import_runtime_heavy_modules():
    code = """
import importlib
import json
import sys

forbidden = [
    "app",
    "modules.rag_qa",
    "chromadb",
    "ollama",
    "langchain",
    "torch",
]

importlib.import_module("modules.report_followup")

loaded = [
    name for name in forbidden
    if name in sys.modules or any(module.startswith(name + ".") for module in sys.modules)
]

print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_minimal_kb_docs_exist_and_contain_key_phrases():
    docs = [
        Path("knowledge/blue_team/report_explainer/reading_the_report.md"),
        Path("knowledge/blue_team/report_explainer/risk_level_decision.md"),
        Path("knowledge/blue_team/report_explainer/investigation_checklist.md"),
        Path("knowledge/blue_team/report_explainer/security_triage_report.md"),
        Path("knowledge/blue_team/report_explainer/evidence_interpretation.md"),
        Path("knowledge/blue_team/report_explainer/detection_source_meaning.md"),
        Path("knowledge/blue_team/report_explainer/behavior_attack_triage.md"),
        Path("knowledge/blue_team/report_explainer/simulation_notice.md"),
        Path("knowledge/blue_team/report_explainer/ai_assist_limitations.md"),
        Path("knowledge/blue_team/report_explainer/disagreement_handling.md"),
        Path("knowledge/blue_team/report_explainer/incident_response_next_steps.md"),
        Path("knowledge/blue_team/report_explainer/possible_account_compromise.md"),
        Path("knowledge/blue_team/report_explainer/success_after_failures.md"),
        Path("knowledge/blue_team/report_explainer/monitor_decision_investigation.md"),
        Path("knowledge/blue_team/report_explainer/authentication_investigation_checklist.md"),
        Path("knowledge/blue_team/report_explainer/authentication_false_positive_considerations.md"),
        Path("knowledge/blue_team/report_explainer/xss_explainer.md"),
        Path("knowledge/blue_team/report_explainer/sql_injection_explainer.md"),
        Path("knowledge/blue_team/report_explainer/path_traversal_explainer.md"),
        Path("knowledge/blue_team/report_explainer/command_injection_explainer.md"),
    ]

    assert len(docs) == 20
    for doc in docs:
        assert doc.exists()
        content = doc.read_text(encoding="utf-8")
        assert content.strip()
        assert "---" in content

    combined = "\n".join(doc.read_text(encoding="utf-8") for doc in docs)
    assert "Security Triage Report" in combined
    assert "Risk Level" in combined
    assert "possible_account_compromise" in combined or "Possible Account Compromise" in combined
