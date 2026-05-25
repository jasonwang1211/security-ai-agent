"""Serialization-only helpers for in-memory GraphSnapshot objects.

No save/load helpers, file persistence, nodes.jsonl, or edges.jsonl are
provided here.
"""

from modules.graph.types import GraphSnapshot


def graph_snapshot_to_dict(snapshot: GraphSnapshot) -> dict[str, object]:
    """Return a JSON-mode dict aligned exactly with GraphSnapshot."""

    return snapshot.model_dump(mode="json")


def graph_snapshot_to_json(snapshot: GraphSnapshot) -> str:
    """Return the GraphSnapshot as a JSON string without writing files."""

    return snapshot.model_dump_json()
