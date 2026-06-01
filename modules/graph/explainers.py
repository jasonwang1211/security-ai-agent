"""Graph-backed explanations over explicit in-memory GraphSnapshot edges.

This module follows existing graph nodes and edges only. It does not perform
Graph RAG retrieval, call LLM/vector systems, execute tools, or change Risk
Level / Decision.
"""

from modules.graph.lookup import get_incident_context, get_node
from modules.graph.types import GraphEdge, GraphEdgeKind, GraphNode, GraphNodeKind, GraphSnapshot
from modules.rag.types import AnswerWithSources, CitationKind, SourceCitation, make_insufficient_answer


_INSUFFICIENT_GRAPH_SOURCE = SourceCitation(
    source="insufficient_graph_context",
    kind="knowledge_doc",
    heading="Graph explanation limitation",
    identifier="graph_context",
)


def explain_graph_reference(snapshot: GraphSnapshot, reference_id: str) -> AnswerWithSources:
    """Explain exact graph references using explicit 1-hop edges only."""

    normalized_id = _normalize_reference_id(reference_id)
    if normalized_id.startswith("EV-"):
        return _explain_evidence(snapshot, normalized_id)
    if normalized_id.startswith("F-"):
        return _explain_finding(snapshot, normalized_id)
    if normalized_id.startswith("INC-"):
        return _explain_incident(snapshot, normalized_id)
    return _explain_rule(snapshot, normalized_id)


def _explain_evidence(snapshot: GraphSnapshot, evidence_id: str) -> AnswerWithSources:
    evidence = get_node(snapshot, evidence_id)
    if evidence is None:
        return _missing_reference(evidence_id)
    if evidence.kind != GraphNodeKind.EVIDENCE:
        return _wrong_kind(evidence_id, evidence.kind)

    support_edges = _edges_for(snapshot, kind=GraphEdgeKind.SUPPORTED_BY, target=evidence_id)
    finding_nodes = _nodes_for_edges(snapshot, support_edges, use_source=True, kind=GraphNodeKind.FINDING)
    if not finding_nodes:
        return _disconnected_reference(evidence, "No explicit Finding is supported by this Evidence.")

    finding_text = _join_node_labels(finding_nodes)
    answer = (
        f"{evidence.id} explicitly supports finding(s): {finding_text}. "
        "This graph-backed explanation follows SUPPORTED_BY edges only and does not change Risk Level or Decision."
    )
    return AnswerWithSources(
        answer=answer,
        sources=_citations_for_edges(snapshot, support_edges),
        evidence_ids=[evidence.id],
        finding_ids=[node.id for node in finding_nodes],
        confidence="HIGH",
        limitations=["Graph explanation uses explicit in-memory graph edges only."],
    )


def _explain_finding(snapshot: GraphSnapshot, finding_id: str) -> AnswerWithSources:
    finding = get_node(snapshot, finding_id)
    if finding is None:
        return _missing_reference(finding_id)
    if finding.kind != GraphNodeKind.FINDING:
        return _wrong_kind(finding_id, finding.kind)

    evidence_edges = _edges_for(snapshot, kind=GraphEdgeKind.SUPPORTED_BY, source=finding_id)
    rule_edges = _edges_for(snapshot, kind=GraphEdgeKind.MAPS_TO_RULE, source=finding_id)
    attack_edges = _edges_for(snapshot, kind=GraphEdgeKind.RELATED_TO_ATTACK, source=finding_id)
    evidence_nodes = _nodes_for_edges(snapshot, evidence_edges, use_source=False, kind=GraphNodeKind.EVIDENCE)
    rule_nodes = _nodes_for_edges(snapshot, rule_edges, use_source=False, kind=GraphNodeKind.DETECTION_RULE)
    attack_nodes = _nodes_for_edges(snapshot, attack_edges, use_source=False, kind=GraphNodeKind.ATTACK_TYPE)
    if not evidence_nodes and not rule_nodes and not attack_nodes:
        return _disconnected_reference(finding, "No explicit Evidence, DetectionRule, or AttackType relationship was found.")

    parts = [f"{finding.id} has explicit graph relationships:"]
    if evidence_nodes:
        parts.append(f"Evidence: {_join_node_labels(evidence_nodes)}.")
    if rule_nodes:
        parts.append(f"Rules: {_join_node_labels(rule_nodes)}.")
    if attack_nodes:
        parts.append(f"Attack types: {_join_node_labels(attack_nodes)}.")
    parts.append("Only existing graph edges were used; no relationship was inferred.")
    edges = [*evidence_edges, *rule_edges, *attack_edges]
    return AnswerWithSources(
        answer=" ".join(parts),
        sources=_citations_for_edges(snapshot, edges),
        evidence_ids=[node.id for node in evidence_nodes],
        finding_ids=[finding.id],
        rule_ids=_rule_ids_from_nodes(rule_nodes),
        confidence="HIGH",
        limitations=["Graph explanation uses explicit in-memory graph edges only."],
    )


def _explain_rule(snapshot: GraphSnapshot, rule_id: str) -> AnswerWithSources:
    graph_rule_id = _rule_node_id(rule_id)
    stable_rule_id = _stable_rule_id(rule_id)
    rule = get_node(snapshot, graph_rule_id)
    if rule is None:
        return _missing_reference(rule_id)
    if rule.kind != GraphNodeKind.DETECTION_RULE:
        return _wrong_kind(rule_id, rule.kind)

    finding_edges = _edges_for(snapshot, kind=GraphEdgeKind.MAPS_TO_RULE, target=graph_rule_id)
    attack_edges = _edges_for(snapshot, kind=GraphEdgeKind.DETECTS, source=graph_rule_id)
    finding_nodes = _nodes_for_edges(snapshot, finding_edges, use_source=True, kind=GraphNodeKind.FINDING)
    attack_nodes = _nodes_for_edges(snapshot, attack_edges, use_source=False, kind=GraphNodeKind.ATTACK_TYPE)
    if not finding_nodes and not attack_nodes:
        return _disconnected_reference(rule, "No explicit Finding or AttackType relationship was found.")

    parts = [f"{rule_id} resolves to {rule.id}."]
    if finding_nodes:
        parts.append(f"Mapped findings: {_join_node_labels(finding_nodes)}.")
    if attack_nodes:
        parts.append(f"Detected attack types: {_join_node_labels(attack_nodes)}.")
    parts.append("Only MAPS_TO_RULE and DETECTS edges were used.")
    return AnswerWithSources(
        answer=" ".join(parts),
        sources=_citations_for_edges(snapshot, [*finding_edges, *attack_edges]),
        finding_ids=[node.id for node in finding_nodes],
        rule_ids=[stable_rule_id],
        confidence="HIGH",
        limitations=["Graph explanation uses explicit in-memory graph edges only."],
    )


def _explain_incident(snapshot: GraphSnapshot, incident_id: str) -> AnswerWithSources:
    context = get_incident_context(snapshot, incident_id)
    incident = context["incident"]
    if incident is None:
        return _missing_reference(incident_id)

    evidence_nodes = context["evidence"]
    finding_nodes = context["findings"]
    rule_nodes = context["rules"]
    attack_nodes = context["attack_types"]
    risk_node = context["risk_level"]
    decision_node = context["decision"]
    edges = [
        edge
        for edge in snapshot.edges
        if edge.source_node_id == incident_id
        or edge.source_node_id in {node.id for node in finding_nodes}
        or edge.source_node_id in {node.id for node in rule_nodes}
    ]
    parts = [
        f"{incident.id} has {len(evidence_nodes)} explicit evidence node(s) and {len(finding_nodes)} explicit finding node(s)."
    ]
    if risk_node is not None:
        parts.append(f"Risk Level node: {risk_node.label}.")
    if decision_node is not None:
        parts.append(f"Decision node: {decision_node.label}; decisions remain simulated.")
    if rule_nodes:
        parts.append(f"Related rules: {_join_node_labels(rule_nodes)}.")
    if attack_nodes:
        parts.append(f"Related attack types: {_join_node_labels(attack_nodes)}.")
    parts.append("This summary follows explicit incident graph edges only.")
    citations = _citations_for_edges(snapshot, edges) or [_citation_for_node(incident)]
    return AnswerWithSources(
        answer=" ".join(parts),
        sources=citations,
        evidence_ids=[node.id for node in evidence_nodes],
        finding_ids=[node.id for node in finding_nodes],
        rule_ids=_rule_ids_from_nodes(rule_nodes),
        confidence="HIGH",
        limitations=["Graph explanation uses explicit in-memory graph edges only."],
    )


def _normalize_reference_id(reference_id: str) -> str:
    normalized = str(reference_id or "").strip()
    if not normalized:
        raise ValueError("reference id must not be empty")
    return normalized.upper()


def _missing_reference(reference_id: str) -> AnswerWithSources:
    return make_insufficient_answer(
        f"{reference_id} was not found in the supplied GraphSnapshot.",
        source=_INSUFFICIENT_GRAPH_SOURCE,
    )


def _wrong_kind(reference_id: str, kind: GraphNodeKind) -> AnswerWithSources:
    return AnswerWithSources(
        answer=f"{reference_id} exists in the graph as {kind.value}, but not as the requested reference type.",
        sources=[_INSUFFICIENT_GRAPH_SOURCE],
        confidence="LOW",
        limitations=["Graph reference type did not match the requested explanation path."],
    )


def _disconnected_reference(node: GraphNode, message: str) -> AnswerWithSources:
    return AnswerWithSources(
        answer=f"{node.id} exists in the graph. {message}",
        sources=[_citation_for_node(node)],
        evidence_ids=[node.id] if node.kind == GraphNodeKind.EVIDENCE else [],
        finding_ids=[node.id] if node.kind == GraphNodeKind.FINDING else [],
        rule_ids=_rule_ids_from_nodes([node]) if node.kind == GraphNodeKind.DETECTION_RULE else [],
        confidence="LOW",
        limitations=["No explicit relevant graph relationship was present."],
    )


def _edges_for(
    snapshot: GraphSnapshot,
    *,
    kind: GraphEdgeKind,
    source: str | None = None,
    target: str | None = None,
) -> list[GraphEdge]:
    return [
        edge
        for edge in snapshot.edges
        if edge.kind == kind
        and (source is None or edge.source_node_id == source)
        and (target is None or edge.target_node_id == target)
    ]


def _nodes_for_edges(
    snapshot: GraphSnapshot,
    edges: list[GraphEdge],
    *,
    use_source: bool,
    kind: GraphNodeKind,
) -> list[GraphNode]:
    nodes: list[GraphNode] = []
    seen: set[str] = set()
    for edge in edges:
        node_id = edge.source_node_id if use_source else edge.target_node_id
        node = get_node(snapshot, node_id)
        if node is not None and node.kind == kind and node.id not in seen:
            nodes.append(node)
            seen.add(node.id)
    return nodes


def _citations_for_edges(snapshot: GraphSnapshot, edges: list[GraphEdge]) -> list[SourceCitation]:
    citations: list[SourceCitation] = []
    seen: set[str] = set()
    for edge in edges:
        if edge.id in seen:
            continue
        source_node = get_node(snapshot, edge.source_node_id)
        target_node = get_node(snapshot, edge.target_node_id)
        citations.append(_citation_for_edge(edge, source_node, target_node))
        seen.add(edge.id)
    return citations


def _citation_for_edge(
    edge: GraphEdge,
    source_node: GraphNode | None,
    target_node: GraphNode | None,
) -> SourceCitation:
    citation_node = target_node or source_node
    return SourceCitation(
        source=f"graph:{edge.id}",
        kind=_citation_kind(citation_node),
        heading=edge.kind.value,
        identifier=edge.id,
        metadata={
            "edge": _edge_metadata(edge),
            "source_node": _node_metadata(source_node),
            "target_node": _node_metadata(target_node),
        },
    )


def _citation_for_node(node: GraphNode) -> SourceCitation:
    return SourceCitation(
        source=f"graph:{node.id}",
        kind=_citation_kind(node),
        heading=node.kind.value,
        identifier=node.id,
        metadata={"node": _node_metadata(node)},
    )


def _citation_kind(node: GraphNode | None) -> CitationKind:
    if node is None:
        return "knowledge_doc"
    if node.kind == GraphNodeKind.EVIDENCE:
        return "incident_evidence"
    if node.kind == GraphNodeKind.FINDING:
        return "incident_finding"
    if node.kind == GraphNodeKind.DETECTION_RULE:
        return "detection_rule"
    return "knowledge_doc"


def _node_metadata(node: GraphNode | None) -> dict[str, object] | None:
    if node is None:
        return None
    return {
        "id": node.id,
        "kind": node.kind.value,
        "label": node.label,
        "metadata": node.metadata,
        "sources": [source.model_dump(mode="json") for source in node.sources],
    }


def _edge_metadata(edge: GraphEdge) -> dict[str, object]:
    return {
        "id": edge.id,
        "kind": edge.kind.value,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "label": edge.label,
        "metadata": edge.metadata,
        "sources": [source.model_dump(mode="json") for source in edge.sources],
    }


def _join_node_labels(nodes: list[GraphNode]) -> str:
    return ", ".join(f"{node.id} ({node.label})" for node in nodes)


def _rule_node_id(rule_id: str) -> str:
    return rule_id if rule_id.startswith("DETECTION_RULE:") else f"DETECTION_RULE:{rule_id}"


def _stable_rule_id(rule_id: str) -> str:
    return rule_id.removeprefix("DETECTION_RULE:")


def _rule_ids_from_nodes(nodes: list[GraphNode]) -> list[str]:
    return [
        _stable_rule_id(node.id)
        for node in nodes
        if node.kind == GraphNodeKind.DETECTION_RULE
    ]
