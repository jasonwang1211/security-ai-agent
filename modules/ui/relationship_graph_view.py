"""Pure visual relationship graph display helpers for the analyst console."""

from __future__ import annotations

from dataclasses import dataclass
import re

from modules.ui.console_state import ActiveContextSummary

EMPTY_RELATIONSHIP_GRAPH_MESSAGE = (
    "No relationship graph is available yet. Run an analysis and retrieve similar cases first."
)

RELATIONSHIP_GRAPH_NOTES = (
    "圖形由目前脈絡與核准相似案例輸出產生。 | Graph is derived from current active context and approved similar-case output.",
    "圖形僅供參考。 | Graph is advisory only.",
    "圖形不會覆蓋 Risk Level 或 Decision。 | Graph does not override Risk Level or Decision.",
    "未執行任何真實防護動作。 | No real enforcement is executed.",
)

RELATIONSHIP_GRAPH_LEGEND = (
    "藍色方塊 = 目前事件 / 事件脈絡 | Blue box = Current event / incident",
    "綠色方塊 = 核准相似案例 | Green box = Approved similar case",
    "橢圓 = 共享欄位 / 實體 | Ellipse = Shared field / entity",
    "紅色菱形 = 風險等級 | Red diamond = Risk level",
    "黃色菱形 = 模擬決策 | Yellow diamond = Simulated decision",
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

_EDGE_DISPLAY_LABELS = {
    HAS_ATTACK_TYPE: "攻擊",
    MATCHED_RULE: "規則",
    HAS_EVIDENCE: "證據",
    HAS_FINDING: "發現",
    HAS_RISK: "風險",
    HAS_DECISION: "決策",
    SIMILAR_TO: "相似",
    SHARES_ATTACK_TYPE: "共享攻擊",
    SHARES_RULE: "共享規則",
    SHARES_EVIDENCE: "共享證據",
    SHARES_FINDING: "共享發現",
    SHARES_DECISION: "共享決策",
}

_DISPLAY_LABEL_REPLACEMENTS = {
    "shell_metacharacter_payload": "shell metachar payload",
}

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
    legend: tuple[str, ...]
    summary: tuple[str, ...]

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
            legend=RELATIONSHIP_GRAPH_LEGEND,
            summary=(),
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
        legend=RELATIONSHIP_GRAPH_LEGEND,
        summary=_build_summary(nodes, edges),
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
    node_lines = [_format_node(node) for node in nodes]
    node_line_by_id = {node.node_id: line for node, line in zip(nodes, node_lines)}
    current_node_ids = tuple(
        node.node_id
        for node in nodes
        if node.kind in {CURRENT_CONTEXT_KIND, RISK_LEVEL_KIND, DECISION_KIND}
    )
    shared_node_ids = tuple(
        node.node_id
        for node in nodes
        if node.kind in {ATTACK_TYPE_KIND, RULE_ID_KIND, EVIDENCE_TYPE_KIND, FINDING_TYPE_KIND}
    )
    case_node_ids = tuple(node.node_id for node in nodes if node.kind == SIMILAR_CASE_KIND)
    clustered_node_ids = set(current_node_ids + shared_node_ids + case_node_ids)

    lines = [
        "digraph RelationshipGraph {",
        "  rankdir=LR;",
        "  splines=true;",
        "  concentrate=false;",
        "  nodesep=0.55;",
        "  ranksep=1.0;",
        '  graph [fontname="Arial", bgcolor="#ffffff", fontcolor="#0f172a", pad="0.25"];',
        '  node [fontname="Arial", fontcolor="#0f172a", style="rounded,filled", color="#64748b", penwidth=1.4];',
        '  edge [fontname="Arial", color="#475569", fontcolor="#0f172a", arrowsize=0.75, fontsize=11];',
        "",
    ]
    lines.extend(_format_cluster("cluster_current", "Current Context", current_node_ids, node_line_by_id))
    lines.extend(
        _format_cluster(
            "cluster_shared",
            "Shared Relationship Fields",
            shared_node_ids,
            node_line_by_id,
        )
    )
    lines.extend(
        _format_cluster(
            "cluster_cases",
            "Approved Similar Cases",
            case_node_ids,
            node_line_by_id,
        )
    )
    for node in nodes:
        if node.node_id not in clustered_node_ids:
            lines.append(node_line_by_id[node.node_id])
    if nodes and edges:
        lines.append("")
    for edge in edges:
        lines.append(
            f'  "{_dot_escape(edge.source)}" -> "{_dot_escape(edge.target)}" '
            f'[label="{_dot_escape(_edge_display_label(edge.label))}"];'
        )
    lines.append("}")
    return "\n".join(lines)


def _format_cluster(
    cluster_id: str,
    label: str,
    node_ids: tuple[str, ...],
    node_line_by_id: dict[str, str],
) -> list[str]:
    if not node_ids:
        return []
    lines = [
        f"  subgraph {cluster_id} {{",
        f'    label="{_dot_escape(label)}";',
        '    color="#cbd5e1";',
        '    fontcolor="#0f172a";',
        '    fontsize="14";',
        '    style="rounded,dashed";',
        "",
    ]
    for node_id in node_ids:
        lines.append(f"  {node_line_by_id[node_id]}")
    lines.extend(["  }", ""])
    return lines


def _format_node(node: RelationshipGraphNode) -> str:
    style = _node_style(node.kind)
    return (
        f'  "{_dot_escape(node.node_id)}" '
        f'[label="{_dot_escape(_display_label(node.label))}", shape={style["shape"]}, '
        f'fillcolor="{style["fillcolor"]}", color="{style["color"]}"];'
    )


def _node_style(kind: str) -> dict[str, str]:
    styles = {
        CURRENT_CONTEXT_KIND: {"shape": "box", "fillcolor": "#bfdbfe", "color": "#2563eb"},
        SIMILAR_CASE_KIND: {"shape": "box", "fillcolor": "#bbf7d0", "color": "#16a34a"},
        RISK_LEVEL_KIND: {"shape": "diamond", "fillcolor": "#fecaca", "color": "#dc2626"},
        DECISION_KIND: {"shape": "diamond", "fillcolor": "#fde68a", "color": "#d97706"},
        BOUNDARY_KIND: {"shape": "note", "fillcolor": "#f8fafc", "color": "#64748b"},
    }
    return styles.get(kind, {"shape": "ellipse", "fillcolor": "#f8fafc", "color": "#64748b"})


def _build_summary(
    nodes: tuple[RelationshipGraphNode, ...],
    edges: tuple[RelationshipGraphEdge, ...],
) -> tuple[str, ...]:
    node_by_id = {node.node_id: node for node in nodes}
    current = node_by_id.get("current")
    if current is None:
        return ()

    lines: list[str] = []
    for edge in edges:
        if edge.source == "current" and edge.label == SIMILAR_TO:
            case = node_by_id.get(edge.target)
            if case is not None:
                lines.append(
                    f"{_zh_current_label(current.label)}與 {case.label} 相似。 | "
                    f"{current.label} is similar to {case.label}."
                )

    shared_templates = {
        SHARES_ATTACK_TYPE: "兩者共享攻擊類型：{value}。 | Both share attack type: {value}.",
        SHARES_RULE: "兩者關聯規則 ID：{value}。 | Both are associated with rule ID: {value}.",
        SHARES_EVIDENCE: "兩者共享證據類型：{value}。 | Both share evidence type: {value}.",
        SHARES_FINDING: "兩者共享發現類型：{value}。 | Both share finding type: {value}.",
        SHARES_DECISION: "兩者共享模擬決策：{value}。 | Both share simulated decision: {value}.",
    }
    for edge in edges:
        template = shared_templates.get(edge.label)
        target = node_by_id.get(edge.target)
        if template is not None and target is not None:
            lines.append(template.format(value=_display_label(target.label)))

    return tuple(dict.fromkeys(lines))


def _current_context_label(summary: ActiveContextSummary) -> str:
    if summary.kind == "incident":
        return "Current Incident"
    if summary.kind == "event":
        return "Current Event"
    return summary.title or "Current Context"


def _zh_current_label(label: str) -> str:
    if label == "Current Incident":
        return "目前事件脈絡"
    if label == "Current Event":
        return "目前事件"
    return "目前脈絡"


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


def _display_label(value: str) -> str:
    cleaned = _clean_value(value)
    replacement = _DISPLAY_LABEL_REPLACEMENTS.get(cleaned)
    if replacement is not None:
        return replacement
    return cleaned.replace("_", " ")


def _edge_display_label(value: str) -> str:
    return _EDGE_DISPLAY_LABELS.get(value, value.replace("_", " "))


def _dot_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')
