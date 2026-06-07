"""Pure visual relationship graph display helpers for the analyst console."""

from __future__ import annotations

from dataclasses import dataclass
import re

from modules.ui.console_state import ActiveContextSummary

EMPTY_RELATIONSHIP_GRAPH_MESSAGE = (
    "No relationship graph is available yet. Run an analysis and retrieve similar cases first."
)

RELATIONSHIP_GRAPH_NOTES = (
    "Graph is derived from current active context and approved similar-case output.",
    "Graph is advisory only.",
    "Graph does not override Risk Level or Decision.",
    "No real enforcement is executed.",
)

CURRENT_CONTEXT_KIND = "current_context"
ATTACK_TYPE_KIND = "attack_type"
RULE_ID_KIND = "rule_id"
EVIDENCE_TYPE_KIND = "evidence_type"
FINDING_TYPE_KIND = "finding_type"
RISK_LEVEL_KIND = "risk_level"
DECISION_KIND = "decision"
SIMILAR_CASE_KIND = "similar_case"
BOUNDARY_KIND = "boundary"

HAS_ATTACK_TYPE = "has_attack_type"
MATCHED_RULE = "matched_rule"
HAS_EVIDENCE = "has_evidence"
HAS_FINDING = "has_finding"
HAS_RISK = "has_risk"
HAS_DECISION = "has_decision"
SIMILAR_TO = "similar_to"
SHARES_ATTACK_TYPE = "shares_attack_type"
SHARES_RULE = "shares_rule"
SHARES_EVIDENCE = "shares_evidence"
SHARES_FINDING = "shares_finding"
SHARES_DECISION = "shares_decision"

_CASE_ID_RE = re.compile(r"\bCASE-SEED-\d+\b")
_CASE_BLOCK_RE = re.compile(
    r"(?ms)^\s*\d+\.\s+(?P<case_id>CASE-SEED-\d+)\b(?P<body>.*?)(?=^\s*\d+\.\s+CASE-SEED-\d+\b|\Z)"
)
_REASON_END = (
    r"(?=,\s*(?:matched attack_types|matched rule_ids|matched finding_types|"
    r"matched evidence_types|supporting risk_level match|supporting decision match):|\n|$)"
)
_REASON_PATTERNS = {
    ATTACK_TYPE_KIND: re.compile(r"matched attack_types:\s*(.*?)" + _REASON_END, re.I | re.S),
    RULE_ID_KIND: re.compile(r"matched rule_ids:\s*(.*?)" + _REASON_END, re.I | re.S),
    FINDING_TYPE_KIND: re.compile(r"matched finding_types:\s*(.*?)" + _REASON_END, re.I | re.S),
    EVIDENCE_TYPE_KIND: re.compile(r"matched evidence_types:\s*(.*?)" + _REASON_END, re.I | re.S),
    DECISION_KIND: re.compile(
        r"supporting decision match:\s*(.*?)" + _REASON_END,
        re.I | re.S,
    ),
}
_SHARED_PATTERNS = {
    ATTACK_TYPE_KIND: re.compile(
        r"shares attack type (?P<value>.+?) with (?P<case_id>CASE-SEED-\d+)",
        re.I,
    ),
    RULE_ID_KIND: re.compile(
        r"shares rule ID (?P<value>.+?) with (?P<case_id>CASE-SEED-\d+)",
        re.I,
    ),
    FINDING_TYPE_KIND: re.compile(
        r"shares finding type (?P<value>.+?) with (?P<case_id>CASE-SEED-\d+)",
        re.I,
    ),
    EVIDENCE_TYPE_KIND: re.compile(
        r"shares evidence type (?P<value>.+?) with (?P<case_id>CASE-SEED-\d+)",
        re.I,
    ),
    DECISION_KIND: re.compile(
        r"shares simulated Decision (?P<value>.+?) with (?P<case_id>CASE-SEED-\d+)",
        re.I,
    ),
}


@dataclass(frozen=True)
class RelationshipGraphNode:
    node_id: str
    label: str
    kind: str


@dataclass(frozen=True)
class RelationshipGraphEdge:
    source: str
    target: str
    label: str


@dataclass(frozen=True)
class RelationshipGraphDisplay:
    nodes: tuple[RelationshipGraphNode, ...]
    edges: tuple[RelationshipGraphEdge, ...]
    dot: str
    empty_message: str
    notes: tuple[str, ...]

    @property
    def has_graph(self) -> bool:
        return bool(self.nodes and self.edges)


def build_relationship_graph_display(
    *,
    active_context_summary: ActiveContextSummary,
    approved_similar_cases_text: str,
    graph_relationship_text: str,
) -> RelationshipGraphDisplay:
    """Build a deterministic DOT graph from already available UI display text."""

    builder = _RelationshipGraphBuilder()
    if not active_context_summary.has_context:
        return RelationshipGraphDisplay(
            nodes=(),
            edges=(),
            dot="",
            empty_message=EMPTY_RELATIONSHIP_GRAPH_MESSAGE,
            notes=RELATIONSHIP_GRAPH_NOTES,
        )

    current_label = _current_context_label(active_context_summary)
    builder.add_node("current", current_label, CURRENT_CONTEXT_KIND)
    _add_current_context_features(builder, active_context_summary)

    similar_text = str(approved_similar_cases_text or "")
    relationship_text = str(graph_relationship_text or "")
    _add_similar_case_blocks(builder, similar_text)
    _add_shared_relationships(builder, similar_text)
    _add_shared_relationships(builder, relationship_text)

    nodes = builder.nodes
    edges = builder.edges
    return RelationshipGraphDisplay(
        nodes=nodes,
        edges=edges,
        dot=_build_dot(nodes, edges) if edges else "",
        empty_message=EMPTY_RELATIONSHIP_GRAPH_MESSAGE,
        notes=RELATIONSHIP_GRAPH_NOTES,
    )


class _RelationshipGraphBuilder:
    def __init__(self) -> None:
        self._nodes: dict[str, RelationshipGraphNode] = {}
        self._edges: dict[tuple[str, str, str], RelationshipGraphEdge] = {}

    @property
    def nodes(self) -> tuple[RelationshipGraphNode, ...]:
        return tuple(self._nodes.values())

    @property
    def edges(self) -> tuple[RelationshipGraphEdge, ...]:
        return tuple(self._edges.values())

    def add_node(self, node_id: str, label: str, kind: str) -> str:
        clean_label = _clean_value(label)
        clean_id = _safe_node_id(node_id)
        if not clean_label or clean_label.casefold() in {"none", "n/a"}:
            return ""
        self._nodes.setdefault(
            clean_id,
            RelationshipGraphNode(node_id=clean_id, label=clean_label, kind=kind),
        )
        return clean_id

    def add_edge(self, source: str, target: str, label: str) -> None:
        if not source or not target or source == target:
            return
        edge = RelationshipGraphEdge(source=source, target=target, label=label)
        self._edges.setdefault((source, target, label), edge)


def _add_current_context_features(
    builder: _RelationshipGraphBuilder,
    summary: ActiveContextSummary,
) -> None:
    for value in _detail_values(summary.details, "Attack Type"):
        node_id = builder.add_node(_kind_id(ATTACK_TYPE_KIND, value), value, ATTACK_TYPE_KIND)
        builder.add_edge("current", node_id, HAS_ATTACK_TYPE)

    for value in _detail_values(summary.details, "Rule IDs"):
        node_id = builder.add_node(_kind_id(RULE_ID_KIND, value), value, RULE_ID_KIND)
        builder.add_edge("current", node_id, MATCHED_RULE)

    for value in _detail_values(summary.details, "Evidence IDs"):
        node_id = builder.add_node(_kind_id(EVIDENCE_TYPE_KIND, value), value, EVIDENCE_TYPE_KIND)
        builder.add_edge("current", node_id, HAS_EVIDENCE)

    if summary.risk_level:
        node_id = builder.add_node(
            _kind_id(RISK_LEVEL_KIND, summary.risk_level),
            summary.risk_level,
            RISK_LEVEL_KIND,
        )
        builder.add_edge("current", node_id, HAS_RISK)

    if summary.decision:
        node_id = builder.add_node(
            _kind_id(DECISION_KIND, summary.decision),
            summary.decision,
            DECISION_KIND,
        )
        builder.add_edge("current", node_id, HAS_DECISION)


def _add_similar_case_blocks(builder: _RelationshipGraphBuilder, text: str) -> None:
    seen_case_ids: set[str] = set()
    for match in _CASE_BLOCK_RE.finditer(text):
        case_id = match.group("case_id")
        body = match.group("body")
        _add_case_node(builder, case_id)
        seen_case_ids.add(case_id)
        _add_reason_relationships(builder, case_id, body)

    for case_id in _case_ids(text):
        if case_id not in seen_case_ids:
            _add_case_node(builder, case_id)


def _add_case_node(builder: _RelationshipGraphBuilder, case_id: str) -> str:
    node_id = builder.add_node(_kind_id(SIMILAR_CASE_KIND, case_id), case_id, SIMILAR_CASE_KIND)
    builder.add_edge("current", node_id, SIMILAR_TO)
    return node_id


def _add_reason_relationships(
    builder: _RelationshipGraphBuilder,
    case_id: str,
    text: str,
) -> None:
    for kind, pattern in _REASON_PATTERNS.items():
        for match in pattern.finditer(text):
            for value in _split_values(match.group(1)):
                _add_shared_feature(builder, case_id, kind, value)


def _add_shared_relationships(builder: _RelationshipGraphBuilder, text: str) -> None:
    for kind, pattern in _SHARED_PATTERNS.items():
        for match in pattern.finditer(text):
            _add_shared_feature(builder, match.group("case_id"), kind, match.group("value"))


def _add_shared_feature(
    builder: _RelationshipGraphBuilder,
    case_id: str,
    kind: str,
    value: str,
) -> None:
    clean_value = _clean_value(value)
    case_node_id = _add_case_node(builder, case_id)
    if kind == ATTACK_TYPE_KIND:
        node_id = builder.add_node(_kind_id(kind, clean_value), clean_value, kind)
        builder.add_edge("current", node_id, HAS_ATTACK_TYPE)
        builder.add_edge(case_node_id, node_id, SHARES_ATTACK_TYPE)
    elif kind == RULE_ID_KIND:
        node_id = builder.add_node(_kind_id(kind, clean_value), clean_value, kind)
        builder.add_edge("current", node_id, MATCHED_RULE)
        builder.add_edge(case_node_id, node_id, SHARES_RULE)
    elif kind == FINDING_TYPE_KIND:
        node_id = builder.add_node(_kind_id(kind, clean_value), clean_value, kind)
        builder.add_edge("current", node_id, HAS_FINDING)
        builder.add_edge(case_node_id, node_id, SHARES_FINDING)
    elif kind == EVIDENCE_TYPE_KIND:
        node_id = builder.add_node(_kind_id(kind, clean_value), clean_value, kind)
        builder.add_edge("current", node_id, HAS_EVIDENCE)
        builder.add_edge(case_node_id, node_id, SHARES_EVIDENCE)
    elif kind == DECISION_KIND:
        node_id = builder.add_node(_kind_id(kind, clean_value), clean_value, kind)
        builder.add_edge("current", node_id, HAS_DECISION)
        builder.add_edge(case_node_id, node_id, SHARES_DECISION)


def _build_dot(
    nodes: tuple[RelationshipGraphNode, ...],
    edges: tuple[RelationshipGraphEdge, ...],
) -> str:
    lines = [
        "digraph RelationshipGraph {",
        "  rankdir=LR;",
        '  graph [fontname="Arial"];',
        '  node [fontname="Arial", style="rounded,filled", color="#64748b"];',
        '  edge [fontname="Arial", color="#64748b"];',
        "",
    ]
    for node in nodes:
        style = _node_style(node.kind)
        lines.append(
            f'  "{_dot_escape(node.node_id)}" '
            f'[label="{_dot_escape(node.label)}", shape={style["shape"]}, '
            f'fillcolor="{style["fillcolor"]}"];'
        )
    if nodes and edges:
        lines.append("")
    for edge in edges:
        lines.append(
            f'  "{_dot_escape(edge.source)}" -> "{_dot_escape(edge.target)}" '
            f'[label="{_dot_escape(edge.label)}"];'
        )
    lines.append("}")
    return "\n".join(lines)


def _node_style(kind: str) -> dict[str, str]:
    styles = {
        CURRENT_CONTEXT_KIND: {"shape": "box", "fillcolor": "#dbeafe"},
        SIMILAR_CASE_KIND: {"shape": "box", "fillcolor": "#dcfce7"},
        RISK_LEVEL_KIND: {"shape": "diamond", "fillcolor": "#fee2e2"},
        DECISION_KIND: {"shape": "diamond", "fillcolor": "#fef3c7"},
        BOUNDARY_KIND: {"shape": "note", "fillcolor": "#f8fafc"},
    }
    return styles.get(kind, {"shape": "ellipse", "fillcolor": "#f8fafc"})


def _current_context_label(summary: ActiveContextSummary) -> str:
    if summary.kind == "incident":
        return "Current Incident"
    if summary.kind == "event":
        return "Current Event"
    return summary.title or "Current Context"


def _detail_values(details: tuple[str, ...], label: str) -> tuple[str, ...]:
    prefix = f"{label}:"
    for detail in details:
        if detail.startswith(prefix):
            return tuple(_split_values(detail.removeprefix(prefix)))
    return ()


def _split_values(value: str) -> tuple[str, ...]:
    parts = [_clean_value(part) for part in str(value or "").split(",")]
    return tuple(part for part in parts if part and part.casefold() not in {"none", "n/a"})


def _case_ids(text: str) -> tuple[str, ...]:
    output: list[str] = []
    for case_id in _CASE_ID_RE.findall(text):
        if case_id not in output:
            output.append(case_id)
    return tuple(output)


def _kind_id(kind: str, label: str) -> str:
    return f"{kind}_{label}"


def _safe_node_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned or "node"


def _clean_value(value: str) -> str:
    return " ".join(str(value or "").strip().rstrip(".").split())


def _dot_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')
