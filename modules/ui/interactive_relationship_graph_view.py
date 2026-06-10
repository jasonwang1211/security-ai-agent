"""Pure interactive (HTML/SVG) relationship graph builder for the console.

This view renders the relationship map as deterministic inline HTML/SVG in two
layouts built from the *same* graph data:

- a compact **preview** SVG (overview, fewer visible edge labels), shown in page
  with relationship chips beneath it, and
- a spacious **detail** SVG (wider lanes, more vertical room, all edge labels
  readable, the similar-case edge routed as a top rail), shown in the fullscreen
  lightbox and used for Copy SVG / Download SVG / Download PNG.

It is presentation only:

- It reuses the existing pure ``build_relationship_graph_display`` for all data
  extraction, so it cannot change detection, risk, decision, retrieval, draft,
  or any backend semantics.
- It must not import any UI rendering framework.
- It escapes all dynamic labels before embedding them in HTML.
- The generated HTML is deterministic and exposes node/edge CSS classes for
  testing. The original DOT graph is preserved as ``fallback_dot``.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass

from modules.ui.console_state import ActiveContextSummary
from modules.ui.i18n import DEFAULT_LANGUAGE, normalize_language
from modules.ui.relationship_graph_view import (
    ATTACK_TYPE_KIND,
    CURRENT_CONTEXT_KIND,
    DECISION_KIND,
    EVIDENCE_TYPE_KIND,
    FINDING_TYPE_KIND,
    HAS_DECISION,
    HAS_RISK,
    RISK_LEVEL_KIND,
    RULE_ID_KIND,
    SHARES_ATTACK_TYPE,
    SHARES_DECISION,
    SHARES_EVIDENCE,
    SHARES_FINDING,
    SHARES_RULE,
    SIMILAR_CASE_KIND,
    SIMILAR_TO,
    RelationshipGraphEdge,
    RelationshipGraphNode,
    build_relationship_graph_display,
    edge_display_label,
    node_display_label,
)
from modules.ui.visual_style import decision_color, severity_color

# Node CSS classes (also asserted by tests).
CURRENT_NODE_CLASS = "current-node"
CASE_NODE_CLASS = "case-node"
ENTITY_NODE_CLASS = "entity-node"
RISK_NODE_CLASS = "risk-node"
DECISION_NODE_CLASS = "decision-node"
EDGE_CLASS = "graph-edge"
EDGE_RAIL_CLASS = "graph-edge-rail"

PREVIEW_SVG_ID = "sentinel-graph-preview-svg"
DETAIL_SVG_ID = "sentinel-graph-detail-svg"

_CURRENT_ACCENT = "#38BDF8"
_CASE_ACCENT = "#22C55E"
_ENTITY_ACCENT = "#64748B"
_NODE_FILL = "#161D26"
# Dark SOC background painted inside every SVG so standalone copies/downloads
# render with the same dark surface as the HTML shell.
_SVG_BG_COLOR = "#0d1117"

# Lane assignment for the four SOC relationship groups.
_LANE_CURRENT = 0
_LANE_RISK_DECISION = 1
_LANE_SHARED = 2
_LANE_CASES = 3

_LANE_BY_KIND = {
    CURRENT_CONTEXT_KIND: _LANE_CURRENT,
    RISK_LEVEL_KIND: _LANE_RISK_DECISION,
    DECISION_KIND: _LANE_RISK_DECISION,
    ATTACK_TYPE_KIND: _LANE_SHARED,
    RULE_ID_KIND: _LANE_SHARED,
    EVIDENCE_TYPE_KIND: _LANE_SHARED,
    FINDING_TYPE_KIND: _LANE_SHARED,
    SIMILAR_CASE_KIND: _LANE_CASES,
}

_NODE_CLASS_BY_KIND = {
    CURRENT_CONTEXT_KIND: CURRENT_NODE_CLASS,
    RISK_LEVEL_KIND: RISK_NODE_CLASS,
    DECISION_KIND: DECISION_NODE_CLASS,
    ATTACK_TYPE_KIND: ENTITY_NODE_CLASS,
    RULE_ID_KIND: ENTITY_NODE_CLASS,
    EVIDENCE_TYPE_KIND: ENTITY_NODE_CLASS,
    FINDING_TYPE_KIND: ENTITY_NODE_CLASS,
    SIMILAR_CASE_KIND: CASE_NODE_CLASS,
}

_LANE_HEADERS = {
    _LANE_CURRENT: {
        "zh-TW": "目前事件",
        "en": "Current Event",
        "bilingual": "目前事件 / Current Event",
    },
    _LANE_RISK_DECISION: {
        "zh-TW": "風險與決策",
        "en": "Risk & Decision",
        "bilingual": "風險與決策 / Risk & Decision",
    },
    _LANE_SHARED: {
        "zh-TW": "共享關係欄位",
        "en": "Shared Fields",
        "bilingual": "共享關係欄位 / Shared Fields",
    },
    _LANE_CASES: {
        "zh-TW": "核准相似案例",
        "en": "Approved Cases",
        "bilingual": "核准相似案例 / Approved Cases",
    },
}

_ADVISORY_FOOTERS = {
    "zh-TW": "圖形僅供參考，不會覆蓋 Risk Level 或 Decision；未執行任何真實防護動作。",
    "en": "Graph is advisory only; it does not override Risk Level or Decision. No real enforcement is executed.",
    "bilingual": (
        "圖形僅供參考 / Graph is advisory only; it does not override Risk Level or Decision. "
        "No real enforcement is executed."
    ),
}

# Edge labels shown in the compact preview; all others are hidden in preview and
# carried instead by the relationship chips below the graph.
_PREVIEW_LABEL_WHITELIST = frozenset({HAS_RISK, HAS_DECISION, SIMILAR_TO})

_SHARES_LABELS = frozenset(
    {SHARES_ATTACK_TYPE, SHARES_RULE, SHARES_EVIDENCE, SHARES_FINDING, SHARES_DECISION}
)


def _edge_label_style(raw_label: str) -> tuple[str, float]:
    """Return (css modifier, vertical nudge) so a label sits off its line."""

    if raw_label == HAS_RISK:
        return ("ge-risk", -14.0)
    if raw_label == HAS_DECISION:
        return ("ge-decision", 16.0)
    if raw_label == SIMILAR_TO:
        return ("ge-similar", -16.0)
    if raw_label in _SHARES_LABELS:
        return ("ge-shares", 14.0)
    return ("ge-default", -12.0)


@dataclass(frozen=True)
class _GraphGeometry:
    """Deterministic layout parameters for one SVG layout (preview or detail)."""

    svg_id: str
    svg_class: str
    canvas_w: int
    lane_center_x: tuple[int, int, int, int]
    node_w: tuple[int, int, int, int]
    node_h: int
    row_gap: int
    top: int
    bottom: int
    header_y: int
    node_pad_left: int
    dot_r: int
    dot_text_gap: int
    node_font: int
    header_font: int
    edge_font: int
    show_all_edge_labels: bool
    rail_similar: bool

    def lane_left(self, lane: int) -> float:
        return self.lane_center_x[lane] - self.node_w[lane] / 2

    def lane_right(self, lane: int) -> float:
        return self.lane_center_x[lane] + self.node_w[lane] / 2


_PREVIEW_GEOMETRY = _GraphGeometry(
    svg_id=PREVIEW_SVG_ID,
    svg_class="sentinel-graph-preview-svg",
    canvas_w=980,
    lane_center_x=(110, 340, 590, 850),
    node_w=(170, 150, 220, 170),
    node_h=46,
    row_gap=26,
    top=74,
    bottom=40,
    header_y=38,
    node_pad_left=14,
    dot_r=4,
    dot_text_gap=10,
    node_font=12,
    header_font=13,
    edge_font=11,
    show_all_edge_labels=False,
    rail_similar=False,
)

_DETAIL_GEOMETRY = _GraphGeometry(
    svg_id=DETAIL_SVG_ID,
    svg_class="sentinel-graph-detail-svg",
    canvas_w=1600,
    lane_center_x=(200, 620, 1010, 1460),
    node_w=(260, 230, 330, 250),
    node_h=64,
    row_gap=76,
    top=132,
    bottom=90,
    header_y=60,
    node_pad_left=20,
    dot_r=5,
    dot_text_gap=12,
    node_font=18,
    header_font=22,
    edge_font=15,
    show_all_edge_labels=True,
    rail_similar=True,
)

# Back-compat aliases for previously exported preview geometry constants.
_TOP = _PREVIEW_GEOMETRY.top
_HEADER_Y = _PREVIEW_GEOMETRY.header_y


@dataclass(frozen=True)
class InteractiveGraphDisplay:
    """Pure display model for the interactive relationship graph."""

    has_graph: bool
    html: str
    fallback_dot: str
    legend: tuple[str, ...] = ()
    summary: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    empty_message: str = ""
    preview_svg: str = ""
    detail_svg: str = ""


@dataclass
class _NodePosition:
    lane: int
    left_x: float
    top_y: float
    width: float
    center_x: float
    center_y: float
    css_class: str
    accent: str
    label: str


def build_interactive_relationship_graph_display(
    *,
    active_context_summary: ActiveContextSummary,
    approved_similar_cases_text: str,
    graph_relationship_text: str,
    language: str = DEFAULT_LANGUAGE,
) -> InteractiveGraphDisplay:
    """Build a deterministic interactive HTML/SVG relationship graph.

    Data extraction is delegated to the existing pure relationship-graph
    builder; this function only renders that data as inline HTML/SVG.
    """

    selected_language = normalize_language(language)
    base = build_relationship_graph_display(
        active_context_summary=active_context_summary,
        approved_similar_cases_text=approved_similar_cases_text,
        graph_relationship_text=graph_relationship_text,
        language=selected_language,
    )

    if not base.has_graph:
        return InteractiveGraphDisplay(
            has_graph=False,
            html="",
            fallback_dot=base.dot,
            legend=base.legend,
            summary=base.summary,
            notes=base.notes,
            empty_message=base.empty_message,
        )

    preview_svg = _build_svg(base.nodes, base.edges, selected_language, _PREVIEW_GEOMETRY)
    detail_svg = _build_svg(base.nodes, base.edges, selected_language, _DETAIL_GEOMETRY)
    chips_html = _build_chips(base.nodes, base.edges, selected_language)
    graph_html = _build_graph_html(preview_svg, detail_svg, chips_html, selected_language)
    return InteractiveGraphDisplay(
        has_graph=True,
        html=graph_html,
        fallback_dot=base.dot,
        legend=base.legend,
        summary=base.summary,
        notes=base.notes,
        empty_message=base.empty_message,
        preview_svg=preview_svg,
        detail_svg=detail_svg,
    )


def _build_svg(
    nodes: tuple[RelationshipGraphNode, ...],
    edges: tuple[RelationshipGraphEdge, ...],
    language: str,
    geometry: _GraphGeometry,
) -> str:
    positions, canvas_h = _layout_nodes(nodes, geometry)
    header_svg = _build_lane_headers_svg(positions, language, geometry)
    edges_svg = _build_edges_svg(positions, edges, language, geometry)
    nodes_svg = "".join(_build_node_svg(position, geometry) for position in positions.values())

    # Self-contained SVG: carries xmlns and its own <style> so the markup can be
    # copied or downloaded as a standalone, styled SVG file.
    # Background rect lives inside the SVG so the standalone (copied/downloaded)
    # markup renders with the dark SOC background even outside the HTML shell.
    background = (
        f'<rect class="graph-bg" x="0" y="0" width="{geometry.canvas_w}" '
        f'height="{canvas_h}" fill="{_SVG_BG_COLOR}"></rect>'
    )

    return (
        f'<svg id="{geometry.svg_id}" class="sentinel-graph-svg {geometry.svg_class}" '
        'xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {geometry.canvas_w} {canvas_h}" width="100%" height="{canvas_h}" '
        'preserveAspectRatio="xMidYMin meet" role="img" aria-label="Relationship graph">'
        f"<style>{_SVG_CSS}</style>"
        f"{background}"
        f'<g class="graph-headers">{header_svg}</g>'
        f'<g class="graph-edges">{edges_svg}</g>'
        f'<g class="graph-nodes">{nodes_svg}</g>'
        "</svg>"
    )


def _build_graph_html(
    preview_svg: str,
    detail_svg: str,
    chips_html: str,
    language: str,
) -> str:
    advisory = html.escape(_ADVISORY_FOOTERS.get(language, _ADVISORY_FOOTERS[DEFAULT_LANGUAGE]))
    labels = _toolbar_labels(language)

    toolbar = (
        '<div class="sentinel-graph-toolbar">'
        '<button type="button" class="sentinel-graph-btn" data-action="fullscreen">'
        f'{html.escape(labels["fullscreen"])}</button>'
        '<button type="button" class="sentinel-graph-btn" data-action="copy">'
        f'{html.escape(labels["copy"])}</button>'
        '<button type="button" class="sentinel-graph-btn" data-action="download">'
        f'{html.escape(labels["download"])}</button>'
        '<button type="button" class="sentinel-graph-btn" data-action="png">'
        f'{html.escape(labels["download_png"])}</button>'
        '<span class="sentinel-graph-status" role="status" aria-live="polite"></span>'
        "</div>"
    )

    modal = (
        '<div class="sentinel-graph-modal" role="dialog" aria-modal="true">'
        '<div class="sentinel-graph-modal-head">'
        '<button type="button" class="sentinel-graph-btn" data-action="close">'
        f'{html.escape(labels["close"])}</button>'
        "</div>"
        '<div class="sentinel-graph-modal-body"></div>'
        "</div>"
    )

    # The detail SVG is embedded (visually hidden) so the viewer script can clone
    # it into the modal and read its markup for Copy / Download.
    detail_host = f'<div class="sentinel-graph-detail-host" hidden>{detail_svg}</div>'

    return (
        '<div class="sentinel-graph-shell">'
        f"<style>{_SHELL_CSS}</style>"
        f"{toolbar}"
        f'<div class="sentinel-graph-preview">{preview_svg}</div>'
        f"{chips_html}"
        f"{detail_host}"
        f'<div class="graph-advisory">{advisory}</div>'
        f"{modal}"
        f"{_build_graph_script(labels)}"
        "</div>"
    )


def _build_chips(
    nodes: tuple[RelationshipGraphNode, ...],
    edges: tuple[RelationshipGraphEdge, ...],
    language: str,
) -> str:
    node_by_id = {node.node_id: node for node in nodes}
    seen: set[tuple[str, str]] = set()
    chips: list[str] = []
    for edge in edges:
        chip_key = _CHIP_EDGE_KEYS.get(edge.label)
        if chip_key is None:
            continue
        target = node_by_id.get(edge.target)
        if target is None:
            continue
        value = node_display_label(target.label)
        dedupe = (chip_key, value)
        if dedupe in seen:
            continue
        seen.add(dedupe)
        chips.append(
            '<span class="sentinel-graph-chip">'
            f'<span class="chip-label">{html.escape(_chip_label(chip_key, language))}</span>'
            f'<span class="chip-value">{html.escape(value)}</span>'
            "</span>"
        )

    if not chips:
        return ""
    return '<div class="sentinel-graph-chips">' + "".join(chips) + "</div>"


def _toolbar_labels(language: str) -> dict[str, str]:
    return {
        key: variants.get(language) or variants[DEFAULT_LANGUAGE]
        for key, variants in _TOOLBAR_LABELS.items()
    }


def _chip_label(chip_key: str, language: str) -> str:
    variants = _CHIP_LABELS.get(chip_key, {})
    return variants.get(language) or variants.get(DEFAULT_LANGUAGE) or chip_key


def _build_graph_script(labels: dict[str, str]) -> str:
    """Build the inline viewer script (fullscreen lightbox + copy/download/PNG).

    Only static, language-aware status strings are interpolated, each encoded
    with json.dumps so they are safe JS string literals. No backend or
    user-supplied text is embedded in the script. Copy / Download / PNG all
    operate on the detail SVG.
    """

    msg_ok = json.dumps(labels["copied"])
    msg_fail = json.dumps(labels["copy_failed"])
    msg_dl = json.dumps(labels["downloaded"])
    msg_png_ok = json.dumps(labels["downloaded_png"])
    msg_png_fail = json.dumps(labels["png_failed"])
    detail_id = json.dumps(DETAIL_SVG_ID)
    return (
        "<script>(function(){"
        "var root=document.currentScript.parentNode;"
        f"var DETAIL_ID={detail_id};"
        f"var MSG_OK={msg_ok},MSG_FAIL={msg_fail},MSG_DL={msg_dl},"
        f"MSG_PNG_OK={msg_png_ok},MSG_PNG_FAIL={msg_png_fail};"
        "var detail=root.querySelector('#'+DETAIL_ID);"
        "var modal=root.querySelector('.sentinel-graph-modal');"
        "var body=root.querySelector('.sentinel-graph-modal-body');"
        "var statusEl=root.querySelector('.sentinel-graph-status');"
        "function setStatus(m){if(statusEl){statusEl.textContent=m;}}"
        "function detailText(){return detail?detail.outerHTML:'';}"
        "function sizedDetail(){if(!detail){return null;}var c=detail.cloneNode(true);"
        "var vb=(detail.getAttribute('viewBox')||'').split(/\\s+/);"
        "var w=vb.length===4?parseFloat(vb[2]):1200;var h=vb.length===4?parseFloat(vb[3]):700;"
        "c.removeAttribute('id');c.setAttribute('width',w);c.setAttribute('height',h);"
        "return {markup:new XMLSerializer().serializeToString(c),w:w,h:h};}"
        "function openModal(){if(!modal||!detail){return;}body.innerHTML='';"
        "var c=detail.cloneNode(true);c.removeAttribute('id');"
        "c.setAttribute('class','sentinel-graph-svg sentinel-graph-svg-full');"
        "body.appendChild(c);modal.classList.add('is-open');"
        "try{if(modal.requestFullscreen){modal.requestFullscreen();}}catch(e){}}"
        "function closeModal(){if(!modal){return;}modal.classList.remove('is-open');"
        "try{if(document.fullscreenElement&&document.exitFullscreen){document.exitFullscreen();}}catch(e){}}"
        "function fallbackCopy(t){try{var ta=document.createElement('textarea');"
        "ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);"
        "ta.focus();ta.select();var ok=document.execCommand('copy');document.body.removeChild(ta);"
        "setStatus(ok?MSG_OK:MSG_FAIL);}catch(e){setStatus(MSG_FAIL);}}"
        "function copySvg(){var t=detailText();if(!t){setStatus(MSG_FAIL);return;}"
        "if(navigator.clipboard&&navigator.clipboard.writeText){"
        "navigator.clipboard.writeText(t).then(function(){setStatus(MSG_OK);},function(){fallbackCopy(t);});}"
        "else{fallbackCopy(t);}}"
        "function downloadSvg(){var t=detailText();if(!t){setStatus(MSG_FAIL);return;}"
        "try{var blob=new Blob([t],{type:'image/svg+xml;charset=utf-8'});"
        "var url=URL.createObjectURL(blob);var a=document.createElement('a');"
        "a.href=url;a.download='relationship-graph.svg';document.body.appendChild(a);a.click();"
        "document.body.removeChild(a);setTimeout(function(){URL.revokeObjectURL(url);},1000);"
        "setStatus(MSG_DL);}catch(e){setStatus(MSG_FAIL);}}"
        "function downloadPng(){var d=sizedDetail();if(!d){setStatus(MSG_PNG_FAIL);return;}"
        "try{var blob=new Blob([d.markup],{type:'image/svg+xml;charset=utf-8'});"
        "var url=URL.createObjectURL(blob);var img=new Image();"
        "img.onload=function(){try{var scale=2;var canvas=document.createElement('canvas');"
        "canvas.width=d.w*scale;canvas.height=d.h*scale;var ctx=canvas.getContext('2d');"
        "if(!ctx||!canvas.toBlob){URL.revokeObjectURL(url);setStatus(MSG_PNG_FAIL);return;}"
        "ctx.scale(scale,scale);ctx.fillStyle='#0d1117';ctx.fillRect(0,0,d.w,d.h);"
        "ctx.drawImage(img,0,0,d.w,d.h);URL.revokeObjectURL(url);"
        "canvas.toBlob(function(b){if(!b){setStatus(MSG_PNG_FAIL);return;}"
        "var purl=URL.createObjectURL(b);var a=document.createElement('a');"
        "a.href=purl;a.download='relationship-graph.png';document.body.appendChild(a);a.click();"
        "document.body.removeChild(a);setTimeout(function(){URL.revokeObjectURL(purl);},1000);"
        "setStatus(MSG_PNG_OK);},'image/png');}catch(e){setStatus(MSG_PNG_FAIL);}};"
        "img.onerror=function(){URL.revokeObjectURL(url);setStatus(MSG_PNG_FAIL);};"
        "img.src=url;}catch(e){setStatus(MSG_PNG_FAIL);}}"
        "function on(sel,fn){var el=root.querySelector(sel);if(el){el.addEventListener('click',fn);}}"
        "on('[data-action=\"fullscreen\"]',openModal);"
        "on('[data-action=\"copy\"]',copySvg);"
        "on('[data-action=\"download\"]',downloadSvg);"
        "on('[data-action=\"png\"]',downloadPng);"
        "on('[data-action=\"close\"]',closeModal);"
        "if(modal){modal.addEventListener('click',function(e){if(e.target===modal){closeModal();}});}"
        "document.addEventListener('keydown',function(e){if(e.key==='Escape'){closeModal();}});"
        "})();</script>"
    )


def _layout_nodes(
    nodes: tuple[RelationshipGraphNode, ...],
    geometry: _GraphGeometry,
) -> tuple[dict[str, _NodePosition], int]:
    lanes: dict[int, list[RelationshipGraphNode]] = {0: [], 1: [], 2: [], 3: []}
    for node in nodes:
        lane = _LANE_BY_KIND.get(node.kind, _LANE_SHARED)
        lanes[lane].append(node)

    max_rows = max((len(items) for items in lanes.values()), default=1) or 1
    content_h = max_rows * geometry.node_h + (max_rows - 1) * geometry.row_gap
    canvas_h = int(geometry.top + content_h + geometry.bottom)

    positions: dict[str, _NodePosition] = {}
    for lane, items in lanes.items():
        if not items:
            continue
        # Top-align every lane so the first row starts at the same y, giving an
        # even, consistent gap between the lane titles and the first node row.
        start_y = float(geometry.top)
        width = geometry.node_w[lane]
        center_x = geometry.lane_center_x[lane]
        left_x = center_x - width / 2
        for index, node in enumerate(items):
            top_y = start_y + index * (geometry.node_h + geometry.row_gap)
            positions[node.node_id] = _NodePosition(
                lane=lane,
                left_x=left_x,
                top_y=top_y,
                width=width,
                center_x=center_x,
                center_y=top_y + geometry.node_h / 2,
                css_class=_NODE_CLASS_BY_KIND.get(node.kind, ENTITY_NODE_CLASS),
                accent=_node_accent(node),
                label=node_display_label(node.label),
            )
    return positions, canvas_h


def _node_accent(node: RelationshipGraphNode) -> str:
    if node.kind == CURRENT_CONTEXT_KIND:
        return _CURRENT_ACCENT
    if node.kind == SIMILAR_CASE_KIND:
        return _CASE_ACCENT
    if node.kind == RISK_LEVEL_KIND:
        return severity_color(node.label)
    if node.kind == DECISION_KIND:
        return decision_color(node.label)
    return _ENTITY_ACCENT


def _build_lane_headers_svg(
    positions: dict[str, _NodePosition],
    language: str,
    geometry: _GraphGeometry,
) -> str:
    used_lanes = sorted({position.lane for position in positions.values()})
    parts: list[str] = []
    for lane in used_lanes:
        label = html.escape(_lane_header(lane, language))
        center_x = geometry.lane_center_x[lane]
        parts.append(
            f'<text class="graph-group-header" x="{_fmt(center_x)}" y="{_fmt(geometry.header_y)}" '
            f'style="font-size:{geometry.header_font}px" text-anchor="middle">{label}</text>'
        )
    return "".join(parts)


def _build_edges_svg(
    positions: dict[str, _NodePosition],
    edges: tuple[RelationshipGraphEdge, ...],
    language: str,
    geometry: _GraphGeometry,
) -> str:
    parts: list[str] = []
    for edge in edges:
        source = positions.get(edge.source)
        target = positions.get(edge.target)
        if source is None or target is None:
            continue
        parts.append(_edge_svg(source, target, edge.label, language, geometry))
    return "".join(parts)


def _edge_svg(
    source: _NodePosition,
    target: _NodePosition,
    raw_label: str,
    language: str,
    geometry: _GraphGeometry,
) -> str:
    show_label = geometry.show_all_edge_labels or raw_label in _PREVIEW_LABEL_WHITELIST
    modifier, dy = _edge_label_style(raw_label)

    if geometry.rail_similar and raw_label == SIMILAR_TO:
        return _similar_rail_svg(source, target, raw_label, language, geometry, modifier)

    forward = source.lane <= target.lane
    x1 = source.left_x + source.width if forward else source.left_x
    x2 = target.left_x if forward else target.left_x + target.width
    y1 = source.center_y
    y2 = target.center_y

    span = abs(x2 - x1)
    control = max(36.0, span * 0.4)
    cx1 = x1 + control if forward else x1 - control
    cx2 = x2 - control if forward else x2 + control
    path = (
        f'<path class="{EDGE_CLASS}" d="M {_fmt(x1)} {_fmt(y1)} C {_fmt(cx1)} {_fmt(y1)}, '
        f'{_fmt(cx2)} {_fmt(y2)}, {_fmt(x2)} {_fmt(y2)}"></path>'
    )
    if not show_label:
        return path

    label_cx, label_cy = _label_anchor(source, target, geometry)
    return path + _edge_label_svg(raw_label, language, modifier, label_cx, label_cy + dy, geometry)


def _similar_rail_svg(
    source: _NodePosition,
    target: _NodePosition,
    raw_label: str,
    language: str,
    geometry: _GraphGeometry,
    modifier: str,
) -> str:
    # Route the similar-case edge as a top rail so it does not cut through the
    # center of the graph.
    rail_y = geometry.top - 40
    sx = source.center_x
    tx = target.center_x
    path = (
        f'<path class="{EDGE_CLASS} {EDGE_RAIL_CLASS}" d="M {_fmt(sx)} {_fmt(source.top_y)} '
        f'C {_fmt(sx)} {_fmt(rail_y)}, {_fmt(tx)} {_fmt(rail_y)}, {_fmt(tx)} {_fmt(target.top_y)}"></path>'
    )
    label_cx = (sx + tx) / 2
    return path + _edge_label_svg(raw_label, language, modifier, label_cx, rail_y - 2, geometry)


def _label_anchor(
    source: _NodePosition,
    target: _NodePosition,
    geometry: _GraphGeometry,
) -> tuple[float, float]:
    """Anchor a label in the inter-lane gap adjacent to the target node.

    This keeps labels in clean vertical channels aligned to the target row,
    instead of at the geometric midpoint where they would overlap nodes in a
    skipped lane.
    """

    if source.lane < target.lane:
        prev_lane = target.lane - 1
        left = geometry.lane_right(prev_lane) if prev_lane >= 0 else source.left_x + source.width
        right = geometry.lane_left(target.lane)
        return (left + right) / 2, target.center_y
    if source.lane > target.lane:
        next_lane = target.lane + 1
        left = geometry.lane_right(target.lane)
        right = geometry.lane_left(next_lane) if next_lane <= 3 else source.left_x
        # Shift the label slightly away from the source (e.g. the case node)
        # toward the target lane so shares_* labels do not crowd the case side.
        return left + (right - left) * 0.38, target.center_y
    return (source.center_x + target.center_x) / 2, (source.center_y + target.center_y) / 2


def _edge_label_svg(
    raw_label: str,
    language: str,
    modifier: str,
    label_cx: float,
    label_cy: float,
    geometry: _GraphGeometry,
) -> str:
    display_label = edge_display_label(raw_label, language)
    label = html.escape(display_label)
    char_w = geometry.edge_font * 0.62
    label_w = max(geometry.edge_font * 2.6, len(display_label) * char_w + 14.0)
    label_h = geometry.edge_font + 9
    rect_x = label_cx - label_w / 2
    rect_y = label_cy - label_h / 2
    return (
        f'<rect class="graph-edge-label-bg" x="{_fmt(rect_x)}" y="{_fmt(rect_y)}" '
        f'width="{_fmt(label_w)}" height="{_fmt(label_h)}" rx="5"></rect>'
        f'<text class="graph-edge-label {modifier}" x="{_fmt(label_cx)}" '
        f'y="{_fmt(label_cy + geometry.edge_font * 0.34)}" '
        f'style="font-size:{geometry.edge_font}px" text-anchor="middle">{label}</text>'
    )


def _build_node_svg(position: _NodePosition, geometry: _GraphGeometry) -> str:
    label = html.escape(position.label)
    accent = position.accent
    # Accent dot is vertically centered at a stable left padding; text is left
    # aligned at a fixed dot-to-text gap and vertically centered on the node.
    dot_cx = position.left_x + geometry.node_pad_left
    text_x = position.left_x + geometry.node_pad_left + geometry.dot_r + geometry.dot_text_gap
    return (
        f'<g class="graph-node {position.css_class}">'
        f"<title>{label}</title>"
        f'<rect x="{_fmt(position.left_x)}" y="{_fmt(position.top_y)}" '
        f'width="{_fmt(position.width)}" height="{geometry.node_h}" rx="10" '
        f'style="fill:{_NODE_FILL};stroke:{accent};stroke-width:2"></rect>'
        f'<circle cx="{_fmt(dot_cx)}" cy="{_fmt(position.center_y)}" '
        f'r="{geometry.dot_r}" fill="{accent}"></circle>'
        f'<text x="{_fmt(text_x)}" y="{_fmt(position.center_y + geometry.node_font * 0.34)}" '
        f'style="font-size:{geometry.node_font}px" text-anchor="start">{label}</text>'
        "</g>"
    )


def _lane_header(lane: int, language: str) -> str:
    labels = _LANE_HEADERS.get(lane, {})
    return labels.get(language) or labels.get(DEFAULT_LANGUAGE) or ""


def _fmt(value: float) -> str:
    rounded = round(float(value), 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.1f}"


# Language-aware toolbar / status labels (graph-internal, kept compact).
_TOOLBAR_LABELS = {
    "fullscreen": {
        "zh-TW": "全螢幕檢視",
        "en": "Open Fullscreen",
        "bilingual": "全螢幕 / Fullscreen",
    },
    "copy": {
        "zh-TW": "複製 SVG",
        "en": "Copy SVG",
        "bilingual": "複製 SVG / Copy SVG",
    },
    "download": {
        "zh-TW": "下載 SVG",
        "en": "Download SVG",
        "bilingual": "下載 SVG / Download SVG",
    },
    "download_png": {
        "zh-TW": "下載 PNG",
        "en": "Download PNG",
        "bilingual": "下載 PNG / Download PNG",
    },
    "close": {
        "zh-TW": "關閉",
        "en": "Close",
        "bilingual": "關閉 / Close",
    },
    "copied": {
        "zh-TW": "已複製 SVG",
        "en": "SVG copied",
        "bilingual": "已複製 SVG / SVG copied",
    },
    "copy_failed": {
        "zh-TW": "複製失敗",
        "en": "Copy failed",
        "bilingual": "複製失敗 / Copy failed",
    },
    "downloaded": {
        "zh-TW": "已下載 SVG",
        "en": "SVG downloaded",
        "bilingual": "已下載 SVG / SVG downloaded",
    },
    "downloaded_png": {
        "zh-TW": "已下載 PNG",
        "en": "PNG downloaded",
        "bilingual": "已下載 PNG / PNG downloaded",
    },
    "png_failed": {
        "zh-TW": "PNG 轉換失敗",
        "en": "PNG export failed",
        "bilingual": "PNG 失敗 / PNG export failed",
    },
}

# Language-aware relationship-chip labels (static text only).
_CHIP_LABELS = {
    "risk": {"zh-TW": "風險", "en": "Risk", "bilingual": "風險 / Risk"},
    "decision": {"zh-TW": "決策", "en": "Decision", "bilingual": "決策 / Decision"},
    "shared_attack": {
        "zh-TW": "共享攻擊",
        "en": "Shared attack",
        "bilingual": "共享攻擊 / Shared attack",
    },
    "shared_rule": {
        "zh-TW": "共享規則",
        "en": "Shared rule",
        "bilingual": "共享規則 / Shared rule",
    },
    "shared_evidence": {
        "zh-TW": "共享證據",
        "en": "Shared evidence",
        "bilingual": "共享證據 / Shared evidence",
    },
    "shared_finding": {
        "zh-TW": "共享發現",
        "en": "Shared finding",
        "bilingual": "共享發現 / Shared finding",
    },
    "shared_decision": {
        "zh-TW": "共享決策",
        "en": "Shared decision",
        "bilingual": "共享決策 / Shared decision",
    },
    "similar_case": {
        "zh-TW": "相似案例",
        "en": "Similar case",
        "bilingual": "相似案例 / Similar case",
    },
}

_CHIP_EDGE_KEYS = {
    HAS_RISK: "risk",
    HAS_DECISION: "decision",
    SHARES_ATTACK_TYPE: "shared_attack",
    SHARES_RULE: "shared_rule",
    SHARES_EVIDENCE: "shared_evidence",
    SHARES_FINDING: "shared_finding",
    SHARES_DECISION: "shared_decision",
    SIMILAR_TO: "similar_case",
}

# Styles that live INSIDE the <svg> so copied/downloaded markup is self-contained.
_SVG_CSS = (
    ".graph-group-header{fill:#9aa7b8;font-size:13px;font-weight:600;"
    "letter-spacing:0.3px;}"
    ".graph-edge{stroke:#475569;stroke-width:1.6;fill:none;opacity:0.85;}"
    ".graph-edge-rail{stroke:#5b6b86;stroke-dasharray:6 4;opacity:0.95;}"
    ".graph-edge-label-bg{fill:#0d1117;opacity:0.92;stroke:#243042;stroke-width:1;}"
    ".graph-edge-label{fill:#cbd5e1;font-size:11px;}"
    ".graph-node{cursor:default;transition:filter 120ms ease;}"
    ".graph-node:hover{filter:brightness(1.3);}"
    ".graph-node text{fill:#e5edf5;font-size:12px;font-weight:600;"
    "dominant-baseline:middle;}"
)

# Shell-level styles: container, toolbar, buttons, status, preview, chips, modal.
_SHELL_CSS = (
    ".sentinel-graph-shell{position:relative;background:#0d1117;"
    "border:1px solid #243042;border-radius:12px;padding:10px 12px;"
    'font-family:ui-sans-serif,system-ui,"Segoe UI",Arial,sans-serif;}'
    ".sentinel-graph-svg{display:block;width:100%;height:auto;}"
    ".sentinel-graph-preview{max-height:320px;overflow:auto;}"
    ".sentinel-graph-toolbar{position:absolute;top:8px;right:10px;display:flex;"
    "gap:6px;align-items:center;z-index:5;}"
    ".sentinel-graph-btn{background:#1b2430;color:#cbd5e1;border:1px solid #2f3b4d;"
    "border-radius:6px;padding:4px 9px;font-size:11px;font-weight:600;cursor:pointer;}"
    ".sentinel-graph-btn:hover{filter:brightness(1.25);}"
    ".sentinel-graph-status{color:#7c8aa0;font-size:11px;margin-left:4px;min-width:64px;}"
    ".sentinel-graph-chips{display:flex;flex-wrap:wrap;gap:6px;padding:8px 2px 2px;}"
    ".sentinel-graph-chip{display:inline-flex;align-items:center;gap:6px;"
    "background:#161d26;border:1px solid #2f3b4d;border-radius:999px;"
    "padding:3px 10px;font-size:11px;}"
    ".sentinel-graph-chip .chip-label{color:#9aa7b8;}"
    ".sentinel-graph-chip .chip-value{color:#e5edf5;font-weight:600;}"
    ".graph-advisory{color:#7c8aa0;font-size:11px;padding:8px 4px 2px;}"
    ".sentinel-graph-modal{display:none;position:fixed;inset:0;"
    "background:rgba(3,7,12,0.94);z-index:50;padding:22px;box-sizing:border-box;"
    "overflow:auto;}"
    ".sentinel-graph-modal.is-open{display:block;}"
    ".sentinel-graph-modal-head{display:flex;justify-content:flex-end;margin-bottom:10px;}"
    ".sentinel-graph-modal-body{width:100%;}"
    ".sentinel-graph-svg-full{width:100%;height:auto;}"
)
