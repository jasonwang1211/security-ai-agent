from collections.abc import Sequence
from typing import Any

from modules.detection_rules import DetectionRule
from modules.graph.types import (
    GraphEdge,
    GraphEdgeKind,
    GraphNode,
    GraphNodeKind,
    GraphSnapshot,
    GraphSourceRef,
)
from modules.types import EvidenceItem, Finding, Incident


def build_graph_snapshot(
    incident: Incident,
    detection_rules: Sequence[DetectionRule] | None = None,
) -> GraphSnapshot:
    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}
    rule_index = {rule.id: rule for rule in detection_rules or []}

    _add_node(
        nodes,
        GraphNode(
            id=incident.id,
            kind=GraphNodeKind.INCIDENT,
            label=incident.title,
            metadata={
                "status": incident.status,
                "risk_level": incident.risk_level,
                "decision": incident.decision,
            },
            sources=[
                _source_ref(
                    "incident",
                    incident.id,
                    "id",
                    "Incident node from structured Incident object.",
                )
            ],
        ),
    )

    evidence_by_id = {item.id: item for item in incident.evidence_bundle.items}
    for evidence in incident.evidence_bundle.items:
        _add_evidence_node(nodes, evidence)
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.HAS_EVIDENCE, incident.id, evidence.id),
                kind=GraphEdgeKind.HAS_EVIDENCE,
                source_node_id=incident.id,
                target_node_id=evidence.id,
                label="has evidence",
                sources=[
                    _source_ref(
                        "incident",
                        incident.id,
                        "evidence_bundle.items",
                        "Incident evidence bundle explicitly includes this evidence item.",
                    )
                ],
            ),
        )

    for finding in incident.findings:
        _add_finding_node(nodes, finding)
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.HAS_FINDING, incident.id, finding.id),
                kind=GraphEdgeKind.HAS_FINDING,
                source_node_id=incident.id,
                target_node_id=finding.id,
                label="has finding",
                sources=[
                    _source_ref(
                        "incident",
                        incident.id,
                        "findings",
                        "Incident findings explicitly include this finding.",
                    )
                ],
            ),
        )
        _add_finding_edges(nodes, edges, finding, evidence_by_id, rule_index)

    _add_risk_level(nodes, edges, incident)
    _add_decision(nodes, edges, incident)

    for rule in detection_rules or []:
        _add_rule_node(nodes, rule)
        _add_attack_node(
            nodes,
            rule.attack_type,
            _source_ref(
                "detection_rule",
                rule.id,
                "attack_type",
                "Detection rule explicitly declares this attack type.",
            ),
        )
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.DETECTS, _rule_node_id(rule.id), _attack_node_id(rule.attack_type)),
                kind=GraphEdgeKind.DETECTS,
                source_node_id=_rule_node_id(rule.id),
                target_node_id=_attack_node_id(rule.attack_type),
                label="detects",
                sources=[
                    _source_ref(
                        "detection_rule",
                        rule.id,
                        "attack_type",
                        "Detection rule explicitly declares the attack type it detects.",
                    )
                ],
            ),
        )

    return GraphSnapshot(nodes=list(nodes.values()), edges=list(edges.values()))


def _add_finding_edges(
    nodes: dict[str, GraphNode],
    edges: dict[str, GraphEdge],
    finding: Finding,
    evidence_by_id: dict[str, EvidenceItem],
    rule_index: dict[str, DetectionRule],
) -> None:
    for evidence_id in finding.evidence_ids:
        if evidence_id not in evidence_by_id:
            continue
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.SUPPORTED_BY, finding.id, evidence_id),
                kind=GraphEdgeKind.SUPPORTED_BY,
                source_node_id=finding.id,
                target_node_id=evidence_id,
                label="supported by",
                sources=[
                    _source_ref(
                        "finding",
                        finding.id,
                        "evidence_ids",
                        "Finding explicitly references this evidence ID.",
                    )
                ],
            ),
        )

    if finding.attack_type:
        _add_attack_node(
            nodes,
            finding.attack_type,
            _source_ref(
                "finding",
                finding.id,
                "attack_type",
                "Finding explicitly declares this attack type.",
            ),
        )
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.RELATED_TO_ATTACK, finding.id, _attack_node_id(finding.attack_type)),
                kind=GraphEdgeKind.RELATED_TO_ATTACK,
                source_node_id=finding.id,
                target_node_id=_attack_node_id(finding.attack_type),
                label="related to attack",
                sources=[
                    _source_ref(
                        "finding",
                        finding.id,
                        "attack_type",
                        "Finding explicitly declares this attack type.",
                    )
                ],
            ),
        )

    for rule_id in _explicit_rule_ids(finding.metadata):
        rule = rule_index.get(rule_id)
        if rule is None:
            continue
        _add_rule_node(nodes, rule)
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.MAPS_TO_RULE, finding.id, _rule_node_id(rule.id)),
                kind=GraphEdgeKind.MAPS_TO_RULE,
                source_node_id=finding.id,
                target_node_id=_rule_node_id(rule.id),
                label="maps to rule",
                sources=[
                    _source_ref(
                        "finding",
                        finding.id,
                        "metadata.rule_id",
                        "Finding metadata explicitly references this rule ID.",
                    )
                ],
            ),
        )


def _add_risk_level(
    nodes: dict[str, GraphNode],
    edges: dict[str, GraphEdge],
    incident: Incident,
) -> None:
    risk_node_id = f"RISK_LEVEL:{incident.risk_level}"
    _add_node(
        nodes,
        GraphNode(
            id=risk_node_id,
            kind=GraphNodeKind.RISK_LEVEL,
            label=incident.risk_level,
            sources=[
                _source_ref(
                    "incident",
                    incident.id,
                    "risk_level",
                    "Incident explicitly includes this risk level.",
                )
            ],
        ),
    )
    _add_edge(
        edges,
        GraphEdge(
            id=_edge_id(GraphEdgeKind.HAS_RISK_LEVEL, incident.id, risk_node_id),
            kind=GraphEdgeKind.HAS_RISK_LEVEL,
            source_node_id=incident.id,
            target_node_id=risk_node_id,
            label="has risk level",
            sources=[
                _source_ref(
                    "incident",
                    incident.id,
                    "risk_level",
                    "Incident explicitly includes this risk level.",
                )
            ],
        ),
    )


def _add_decision(
    nodes: dict[str, GraphNode],
    edges: dict[str, GraphEdge],
    incident: Incident,
) -> None:
    decision_node_id = f"DECISION:{incident.decision}"
    _add_node(
        nodes,
        GraphNode(
            id=decision_node_id,
            kind=GraphNodeKind.DECISION,
            label=incident.decision,
            sources=[
                _source_ref(
                    "incident",
                    incident.id,
                    "decision",
                    "Incident explicitly includes this simulated decision.",
                )
            ],
        ),
    )
    _add_edge(
        edges,
        GraphEdge(
            id=_edge_id(GraphEdgeKind.HAS_DECISION, incident.id, decision_node_id),
            kind=GraphEdgeKind.HAS_DECISION,
            source_node_id=incident.id,
            target_node_id=decision_node_id,
            label="has decision",
            sources=[
                _source_ref(
                    "incident",
                    incident.id,
                    "decision",
                    "Incident explicitly includes this simulated decision.",
                )
            ],
        ),
    )


def _add_evidence_node(nodes: dict[str, GraphNode], evidence: EvidenceItem) -> None:
    _add_node(
        nodes,
        GraphNode(
            id=evidence.id,
            kind=GraphNodeKind.EVIDENCE,
            label=evidence.description,
            metadata={
                "type": evidence.type,
                "confidence": evidence.confidence,
            },
            sources=[
                _source_ref(
                    "evidence",
                    evidence.id,
                    "id",
                    "Evidence node from structured EvidenceItem object.",
                )
            ],
        ),
    )


def _add_finding_node(nodes: dict[str, GraphNode], finding: Finding) -> None:
    _add_node(
        nodes,
        GraphNode(
            id=finding.id,
            kind=GraphNodeKind.FINDING,
            label=finding.title,
            metadata={
                "finding_type": finding.finding_type,
                "status": finding.status,
                "risk_level": finding.risk_level,
                "decision": finding.decision,
            },
            sources=[
                _source_ref(
                    "finding",
                    finding.id,
                    "id",
                    "Finding node from structured Finding object.",
                )
            ],
        ),
    )


def _add_rule_node(nodes: dict[str, GraphNode], rule: DetectionRule) -> None:
    _add_node(
        nodes,
        GraphNode(
            id=_rule_node_id(rule.id),
            kind=GraphNodeKind.DETECTION_RULE,
            label=rule.title,
            metadata={
                "rule_id": rule.id,
                "severity": rule.severity,
                "confidence": rule.confidence,
                "source_path": rule.source_path,
            },
            sources=[
                _source_ref(
                    "detection_rule",
                    rule.id,
                    "id",
                    "Detection rule node from explicitly provided DetectionRule object.",
                )
            ],
        ),
    )


def _add_attack_node(
    nodes: dict[str, GraphNode],
    attack_type: str,
    source: GraphSourceRef,
) -> None:
    _add_node(
        nodes,
        GraphNode(
            id=_attack_node_id(attack_type),
            kind=GraphNodeKind.ATTACK_TYPE,
            label=attack_type,
            sources=[source],
        ),
    )


def _add_node(nodes: dict[str, GraphNode], node: GraphNode) -> None:
    nodes.setdefault(node.id, node)


def _add_edge(edges: dict[str, GraphEdge], edge: GraphEdge) -> None:
    edges.setdefault(edge.id, edge)


def _source_ref(source_type: str, source_id: str, field_path: str, reason: str) -> GraphSourceRef:
    return GraphSourceRef(
        source_type=source_type,
        source_id=source_id,
        field_path=field_path,
        reason=reason,
    )


def _edge_id(kind: GraphEdgeKind, source_node_id: str, target_node_id: str) -> str:
    return f"EDGE:{kind.value}:{source_node_id}->{target_node_id}"


def _attack_node_id(attack_type: str) -> str:
    return f"ATTACK_TYPE:{attack_type}"


def _rule_node_id(rule_id: str) -> str:
    return f"DETECTION_RULE:{rule_id}"


def _explicit_rule_ids(metadata: dict[str, Any]) -> list[str]:
    rule_ids: list[str] = []
    for key in ("rule_id", "rule_ids"):
        value = metadata.get(key)
        if isinstance(value, str):
            candidates = [value]
        elif isinstance(value, list):
            candidates = [item for item in value if isinstance(item, str)]
        else:
            candidates = []
        for candidate in candidates:
            if candidate and candidate not in rule_ids:
                rule_ids.append(candidate)
    return rule_ids
