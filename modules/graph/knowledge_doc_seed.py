"""Deterministic KnowledgeDoc graph seed from reviewed metadata only."""

from collections.abc import Sequence

from modules.detection_rules import DetectionRule
from modules.graph.types import (
    GraphEdge,
    GraphEdgeKind,
    GraphNode,
    GraphNodeKind,
    GraphSnapshot,
    GraphSourceRef,
)
from modules.rag.metadata import KnowledgeDocMetadata


def build_knowledge_doc_seed(
    metadata_items: Sequence[KnowledgeDocMetadata],
    detection_rules: Sequence[DetectionRule],
) -> GraphSnapshot:
    """Build KnowledgeDoc seed edges from explicit metadata and supplied rules."""

    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}
    rule_index = {rule.id: rule for rule in detection_rules}

    for metadata in metadata_items:
        attack_types = list(metadata.attack_types)
        rule_ids = list(metadata.rule_ids)
        if not attack_types and not rule_ids:
            continue
        _validate_seed_candidate(metadata, attack_types, rule_ids, rule_index)
        _add_seed_candidate(nodes, edges, metadata, attack_types, rule_ids, rule_index)

    return GraphSnapshot(nodes=list(nodes.values()), edges=list(edges.values()))


def _validate_seed_candidate(
    metadata: KnowledgeDocMetadata,
    attack_types: list[str],
    rule_ids: list[str],
    rule_index: dict[str, DetectionRule],
) -> None:
    if attack_types and not rule_ids:
        raise ValueError(f"{metadata.doc_id} has attack_types but no rule_ids")
    if rule_ids and not attack_types:
        raise ValueError(f"{metadata.doc_id} has rule_ids but no attack_types")
    if metadata.review_status != "approved_for_runtime_promotion":
        raise ValueError(f"{metadata.doc_id} is not approved for graph seed promotion")

    matched_rules: list[DetectionRule] = []
    for rule_id in rule_ids:
        rule = rule_index.get(rule_id)
        if rule is None:
            raise ValueError(f"{metadata.doc_id} references unknown rule_id {rule_id}")
        if rule.attack_type not in attack_types:
            raise ValueError(
                f"{metadata.doc_id} rule_id {rule_id} attack_type {rule.attack_type!r} "
                "does not match reviewed attack_types"
            )
        matched_rules.append(rule)

    matched_attack_types = {rule.attack_type for rule in matched_rules}
    missing_attack_types = [attack_type for attack_type in attack_types if attack_type not in matched_attack_types]
    if missing_attack_types:
        raise ValueError(
            f"{metadata.doc_id} attack_types lack matching DetectionRule objects: "
            f"{', '.join(missing_attack_types)}"
        )


def _add_seed_candidate(
    nodes: dict[str, GraphNode],
    edges: dict[str, GraphEdge],
    metadata: KnowledgeDocMetadata,
    attack_types: list[str],
    rule_ids: list[str],
    rule_index: dict[str, DetectionRule],
) -> None:
    knowledge_doc_id = _knowledge_doc_node_id(metadata.doc_id)
    _add_node(nodes, _knowledge_doc_node(metadata))

    for attack_type in attack_types:
        attack_node_id = _attack_node_id(attack_type)
        _add_node(nodes, _attack_node(metadata, attack_type))
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.RELATED_TO_ATTACK, knowledge_doc_id, attack_node_id),
                kind=GraphEdgeKind.RELATED_TO_ATTACK,
                source_node_id=knowledge_doc_id,
                target_node_id=attack_node_id,
                label="related to attack",
                sources=[
                    _source_ref(
                        metadata.doc_id,
                        "frontmatter.attack_types",
                        "KnowledgeDoc reviewed metadata explicitly declares this attack type.",
                    )
                ],
            ),
        )

    for rule_id in rule_ids:
        rule = rule_index[rule_id]
        rule_node_id = _rule_node_id(rule.id)
        _add_node(nodes, _rule_node(rule))
        _add_edge(
            edges,
            GraphEdge(
                id=_edge_id(GraphEdgeKind.MAPS_TO_RULE, knowledge_doc_id, rule_node_id),
                kind=GraphEdgeKind.MAPS_TO_RULE,
                source_node_id=knowledge_doc_id,
                target_node_id=rule_node_id,
                label="maps to rule",
                sources=[
                    _source_ref(
                        metadata.doc_id,
                        "frontmatter.rule_ids",
                        "KnowledgeDoc reviewed metadata explicitly references this rule ID.",
                    )
                ],
            ),
        )


def _knowledge_doc_node(metadata: KnowledgeDocMetadata) -> GraphNode:
    return GraphNode(
        id=_knowledge_doc_node_id(metadata.doc_id),
        kind=GraphNodeKind.KNOWLEDGE_DOC,
        label=metadata.title or metadata.doc_id,
        metadata={
            "doc_id": metadata.doc_id,
            "doc_type": metadata.doc_type,
            "review_status": metadata.review_status,
            "source_path": metadata.source_path,
        },
        sources=[
            _source_ref(
                metadata.doc_id,
                "doc_id",
                "KnowledgeDoc node from already-parsed reviewed metadata.",
            )
        ],
    )


def _attack_node(metadata: KnowledgeDocMetadata, attack_type: str) -> GraphNode:
    return GraphNode(
        id=_attack_node_id(attack_type),
        kind=GraphNodeKind.ATTACK_TYPE,
        label=attack_type,
        sources=[
            _source_ref(
                metadata.doc_id,
                "frontmatter.attack_types",
                "KnowledgeDoc reviewed metadata explicitly declares this attack type.",
            )
        ],
    )


def _rule_node(rule: DetectionRule) -> GraphNode:
    return GraphNode(
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
            GraphSourceRef(
                source_type="detection_rule",
                source_id=rule.id,
                field_path="id",
                reason="Detection rule node from explicitly provided DetectionRule object.",
            )
        ],
    )


def _source_ref(source_id: str, field_path: str, reason: str) -> GraphSourceRef:
    return GraphSourceRef(
        source_type="knowledge_doc",
        source_id=source_id,
        field_path=field_path,
        reason=reason,
    )


def _add_node(nodes: dict[str, GraphNode], node: GraphNode) -> None:
    nodes.setdefault(node.id, node)


def _add_edge(edges: dict[str, GraphEdge], edge: GraphEdge) -> None:
    edges.setdefault(edge.id, edge)


def _edge_id(kind: GraphEdgeKind, source_node_id: str, target_node_id: str) -> str:
    return f"EDGE:{kind.value}:{source_node_id}->{target_node_id}"


def _knowledge_doc_node_id(doc_id: str) -> str:
    return f"KNOWLEDGE_DOC:{doc_id}"


def _attack_node_id(attack_type: str) -> str:
    return f"ATTACK_TYPE:{attack_type}"


def _rule_node_id(rule_id: str) -> str:
    return f"DETECTION_RULE:{rule_id}"
