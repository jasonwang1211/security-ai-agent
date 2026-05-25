from typing import TypedDict

from modules.graph.types import GraphEdge, GraphEdgeKind, GraphNode, GraphNodeKind, GraphSnapshot


class IncidentContext(TypedDict):
    incident: GraphNode | None
    evidence: list[GraphNode]
    findings: list[GraphNode]
    risk_level: GraphNode | None
    decision: GraphNode | None
    rules: list[GraphNode]
    attack_types: list[GraphNode]


def get_node(snapshot: GraphSnapshot, node_id: str) -> GraphNode | None:
    _require_non_blank_id(node_id)
    for node in snapshot.nodes:
        if node.id == node_id:
            return node
    return None


def get_neighbors(snapshot: GraphSnapshot, node_id: str) -> list[GraphNode]:
    _require_non_blank_id(node_id)
    node_ids: list[str] = []
    for edge in snapshot.edges:
        if edge.source_node_id == node_id:
            _append_unique(node_ids, edge.target_node_id)
        if edge.target_node_id == node_id:
            _append_unique(node_ids, edge.source_node_id)
    return _nodes_by_ids(snapshot, node_ids)


def get_edges_for_node(snapshot: GraphSnapshot, node_id: str) -> list[GraphEdge]:
    _require_non_blank_id(node_id)
    return [
        edge
        for edge in snapshot.edges
        if edge.source_node_id == node_id or edge.target_node_id == node_id
    ]


def find_nodes_by_kind(snapshot: GraphSnapshot, kind: GraphNodeKind) -> list[GraphNode]:
    return [node for node in snapshot.nodes if node.kind == kind]


def get_related_findings(snapshot: GraphSnapshot, evidence_id: str) -> list[GraphNode]:
    _require_non_blank_id(evidence_id)
    finding_ids = [
        edge.source_node_id
        for edge in snapshot.edges
        if edge.kind == GraphEdgeKind.SUPPORTED_BY and edge.target_node_id == evidence_id
    ]
    return _nodes_by_ids(snapshot, finding_ids, kind=GraphNodeKind.FINDING)


def get_related_rules(snapshot: GraphSnapshot, finding_id: str) -> list[GraphNode]:
    _require_non_blank_id(finding_id)
    rule_ids = [
        edge.target_node_id
        for edge in snapshot.edges
        if edge.kind == GraphEdgeKind.MAPS_TO_RULE and edge.source_node_id == finding_id
    ]
    return _nodes_by_ids(snapshot, rule_ids, kind=GraphNodeKind.DETECTION_RULE)


def get_incident_context(snapshot: GraphSnapshot, incident_id: str) -> IncidentContext:
    _require_non_blank_id(incident_id)
    incident = get_node(snapshot, incident_id)
    evidence_ids: list[str] = []
    finding_ids: list[str] = []
    risk_level_id: str | None = None
    decision_id: str | None = None

    for edge in snapshot.edges:
        if edge.source_node_id != incident_id:
            continue
        if edge.kind == GraphEdgeKind.HAS_EVIDENCE:
            _append_unique(evidence_ids, edge.target_node_id)
        elif edge.kind == GraphEdgeKind.HAS_FINDING:
            _append_unique(finding_ids, edge.target_node_id)
        elif edge.kind == GraphEdgeKind.HAS_RISK_LEVEL and risk_level_id is None:
            risk_level_id = edge.target_node_id
        elif edge.kind == GraphEdgeKind.HAS_DECISION and decision_id is None:
            decision_id = edge.target_node_id

    evidence = _nodes_by_ids(snapshot, evidence_ids, kind=GraphNodeKind.EVIDENCE)
    findings = _nodes_by_ids(snapshot, finding_ids, kind=GraphNodeKind.FINDING)
    rules = _rules_for_findings(snapshot, [node.id for node in findings])
    attack_types = _attack_types_for_context(snapshot, [node.id for node in findings], [node.id for node in rules])

    return {
        "incident": incident,
        "evidence": evidence,
        "findings": findings,
        "risk_level": get_node(snapshot, risk_level_id) if risk_level_id else None,
        "decision": get_node(snapshot, decision_id) if decision_id else None,
        "rules": rules,
        "attack_types": attack_types,
    }


def _rules_for_findings(snapshot: GraphSnapshot, finding_ids: list[str]) -> list[GraphNode]:
    rule_ids: list[str] = []
    for edge in snapshot.edges:
        if edge.kind == GraphEdgeKind.MAPS_TO_RULE and edge.source_node_id in finding_ids:
            _append_unique(rule_ids, edge.target_node_id)
    return _nodes_by_ids(snapshot, rule_ids, kind=GraphNodeKind.DETECTION_RULE)


def _attack_types_for_context(
    snapshot: GraphSnapshot,
    finding_ids: list[str],
    rule_ids: list[str],
) -> list[GraphNode]:
    attack_type_ids: list[str] = []
    for edge in snapshot.edges:
        if (
            edge.kind == GraphEdgeKind.RELATED_TO_ATTACK
            and edge.source_node_id in finding_ids
        ) or (edge.kind == GraphEdgeKind.DETECTS and edge.source_node_id in rule_ids):
            _append_unique(attack_type_ids, edge.target_node_id)
    return _nodes_by_ids(snapshot, attack_type_ids, kind=GraphNodeKind.ATTACK_TYPE)


def _nodes_by_ids(
    snapshot: GraphSnapshot,
    node_ids: list[str],
    kind: GraphNodeKind | None = None,
) -> list[GraphNode]:
    wanted_ids = set(node_ids)
    ordered_nodes: list[GraphNode] = []
    for node in snapshot.nodes:
        if node.id in wanted_ids and (kind is None or node.kind == kind):
            ordered_nodes.append(node)
    return sorted(ordered_nodes, key=lambda node: node_ids.index(node.id))


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _require_non_blank_id(value: str) -> None:
    if not value.strip():
        raise ValueError("node id must not be empty")
