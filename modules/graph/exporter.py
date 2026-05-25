from modules.graph.types import GraphSnapshot


def graph_snapshot_to_dict(snapshot: GraphSnapshot) -> dict[str, object]:
    return snapshot.model_dump(mode="json")


def graph_snapshot_to_json(snapshot: GraphSnapshot) -> str:
    return snapshot.model_dump_json()
