"""Advisory relationship graph derived from a structured similar-case result.

This adapter turns an already-computed ``SimilarCaseResult`` into a structured
``GraphSnapshot`` that relates the current context to its approved similar cases.
It is built only from structured fields (never by parsing display text), it does
not call the graph builder, retrieval, or any lookup, and the resulting graph is
advisory context only: it never acts as a detection source and never overrides
the official Risk Level or Decision.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from modules.graph.types import GraphEdge, GraphEdgeKind, GraphNode, GraphNodeKind, GraphSnapshot

if TYPE_CHECKING:
    from modules.controller.approved_case_retrieval import SimilarCaseResult

CURRENT_CONTEXT_NODE_ID = "current_context"
_ADVISORY_EDGE_LABEL = "advisory relationship: current context resembles approved case"


def build_similar_case_graph_snapshot(
    similar_case_result: SimilarCaseResult | Any | None,
) -> GraphSnapshot | None:
    """Return an advisory ``GraphSnapshot`` linking the current context to matches.

    Returns ``None`` when there is no result or no matches, so callers can omit
    graph context cleanly. The snapshot is derived from the structured
    ``SimilarCaseResult`` only; no display text is parsed.
    """

    if similar_case_result is None:
        return None
    matches = list(getattr(similar_case_result, "matches", ()) or ())
    if not matches:
        return None

    current = getattr(similar_case_result, "current", None)
    nodes: list[GraphNode] = [
        GraphNode(
            id=CURRENT_CONTEXT_NODE_ID,
            kind=GraphNodeKind.INCIDENT,
            label=_current_context_label(current),
        )
    ]
    edges: list[GraphEdge] = []
    seen_case_ids: set[str] = set()

    for match in matches:
        seed = getattr(match, "seed", None)
        case_id = str(getattr(seed, "case_id", "") or "").strip()
        if not case_id or case_id in seen_case_ids:
            continue
        seen_case_ids.add(case_id)
        title = str(getattr(seed, "title", "") or "").strip()
        nodes.append(
            GraphNode(
                id=case_id,
                kind=GraphNodeKind.INCIDENT,
                label=f"{case_id} - {title}" if title else case_id,
            )
        )
        edges.append(
            GraphEdge(
                id=f"{CURRENT_CONTEXT_NODE_ID}->{case_id}",
                kind=GraphEdgeKind.RELATED_TO,
                source_node_id=CURRENT_CONTEXT_NODE_ID,
                target_node_id=case_id,
                label=_ADVISORY_EDGE_LABEL,
            )
        )

    if not edges:
        return None
    return GraphSnapshot(nodes=nodes, edges=edges)


def _current_context_label(current: Any | None) -> str:
    if current is None:
        return "Current Context"
    context_kind = str(getattr(current, "context_kind", "") or "").strip()
    if context_kind == "active_auth_incident":
        return "Current Incident"
    if context_kind == "active_event":
        return "Current Event"
    return context_kind or "Current Context"


__all__ = ["CURRENT_CONTEXT_NODE_ID", "build_similar_case_graph_snapshot"]
