import re
import sys
from pathlib import Path

from modules.ui.console_state import ActiveContextSummary
from modules.ui.interactive_relationship_graph_view import (
    _HEADER_Y,
    _TOP,
    _fmt,
    build_interactive_relationship_graph_display,
)


def _chips_region(html: str) -> str:
    match = re.search(r'<div class="sentinel-graph-chips">(.*?)</div>', html, re.DOTALL)
    return match.group(1) if match else ""


def _script_region(html: str) -> str:
    match = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    return match.group(1) if match else ""


def _event_summary(
    *,
    attack_type: str = "Command Injection",
    rule_ids: str = "CMD-001",
    risk_level: str = "HIGH",
    decision: str = "BLOCK",
) -> ActiveContextSummary:
    return ActiveContextSummary(
        kind="event",
        title="Payload/Event",
        risk_level=risk_level,
        decision=decision,
        details=(f"Attack Type: {attack_type}", f"Rule IDs: {rule_ids}"),
    )


def _auth_summary() -> ActiveContextSummary:
    return ActiveContextSummary(
        kind="incident",
        title="Authentication Incident",
        risk_level="HIGH",
        decision="MONITOR",
        details=(
            "Incident ID: INC-20260605-001",
            "Attack Type: Possible Account Compromise",
            "Evidence IDs: EV-001, EV-003",
        ),
    )


def _empty_summary() -> ActiveContextSummary:
    return ActiveContextSummary(
        kind="", title="No active context", risk_level="", decision="", details=()
    )


_SIMILAR_CMD = "\n".join(
    [
        "[Approved Similar Cases]",
        "1. CASE-SEED-001 - Command Injection Payload",
        (
            "   Similarity reasons: matched attack_types: Command Injection, "
            "matched rule_ids: CMD-001, supporting decision match: BLOCK"
        ),
    ]
)
_SIMILAR_AUTH = "\n".join(
    [
        "[Approved Similar Cases]",
        "1. CASE-SEED-002 - Authentication Success After Failures",
        (
            "   Similarity reasons: matched attack_types: Possible Account Compromise, "
            "matched finding_types: possible_account_compromise, "
            "supporting decision match: MONITOR"
        ),
    ]
)


def test_interactive_graph_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/interactive_relationship_graph_view.py").read_text(encoding="utf-8")

    assert "import streamlit" not in source.lower()
    assert "streamlit" not in sys.modules


def test_empty_active_context_returns_no_graph() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_empty_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
    )

    assert display.has_graph is False
    assert display.html == ""
    assert display.empty_message


def test_command_injection_context_produces_expected_graph_html() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
    )

    assert display.has_graph is True
    for token in ("Current Event", "Command Injection", "CMD-001", "HIGH", "BLOCK"):
        assert token in display.html


def test_similar_case_output_produces_case_node_and_similar_edge() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
    )

    assert "CASE-SEED-001" in display.html
    assert "case-node" in display.html
    # similar relationship marker (zh-TW default edge label) or edge class.
    assert ("相似" in display.html) and ("graph-edge" in display.html)


def test_auth_incident_context_produces_incident_and_similar_case_nodes() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_auth_summary(),
        approved_similar_cases_text=_SIMILAR_AUTH,
        graph_relationship_text="",
    )

    assert ("Current Incident" in display.html) or ("Authentication Incident" in display.html)
    assert "Possible Account Compromise" in display.html
    assert "CASE-SEED-002" in display.html


def test_html_escapes_unsafe_labels() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(attack_type="<script>alert(1)</script>"),
        approved_similar_cases_text="",
        graph_relationship_text="",
    )

    assert "<script>alert(1)</script>" not in display.html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in display.html


def test_zh_tw_mode_contains_chinese_labels() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
        language="zh-TW",
    )

    assert "目前事件" in display.html  # group header
    assert any(label in display.html for label in ("攻擊", "規則", "風險", "決策", "相似"))


def test_en_mode_contains_english_labels_and_no_chinese_ui_edge_labels() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
        language="en",
    )

    assert "Current Event" in display.html
    for english_label in ("attack", "rule", "risk", "decision", "similar"):
        assert english_label in display.html
    for chinese_label in ("攻擊", "規則", "證據", "風險", "決策", "相似", "目前事件", "核准相似案例"):
        assert chinese_label not in display.html


def test_bilingual_mode_contains_both_chinese_and_english_labels() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
        language="bilingual",
    )

    assert "Current Event" in display.html  # english (group header + node)
    assert "目前事件" in display.html  # chinese (group header)
    assert "相似" in display.html  # chinese edge label


def test_graph_html_contains_required_node_and_edge_css_classes() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
    )

    for css_class in (
        "current-node",
        "case-node",
        "entity-node",
        "risk-node",
        "decision-node",
        "graph-edge",
    ):
        assert css_class in display.html


def test_advisory_notes_are_present() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
        language="en",
    )

    joined = " ".join(display.notes).casefold()
    assert "advisory" in joined
    assert "does not override" in joined
    assert "no real enforcement" in joined
    # advisory footer is also embedded in the rendered graph html
    assert "advisory" in display.html.casefold()


def test_fallback_dot_is_preserved() -> None:
    display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
    )

    assert "digraph RelationshipGraph" in display.fallback_dot
    assert 'label="Current Event"' in display.fallback_dot


def test_unknown_language_falls_back_to_default() -> None:
    default_display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
    )
    unknown_display = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
        language="unknown",
    )

    assert unknown_display.html == default_display.html
    assert unknown_display.fallback_dot == default_display.fallback_dot


# --- v2.6-M polish pass focused tests ---------------------------------------


def _cmd_with_similar_display(language: str = "zh-TW"):
    return build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="\n".join(
            [
                "[Approved Similar Cases]",
                "1. CASE-SEED-001 - Command Injection Payload",
                (
                    "   Similarity reasons: matched attack_types: Command Injection, "
                    "matched rule_ids: CMD-001, matched evidence_types: "
                    "shell_metacharacter_payload, supporting decision match: BLOCK"
                ),
            ]
        ),
        graph_relationship_text=(
            "Graph-Grounded Relationship Explanation:\n"
            "Current context shares attack type Command Injection with CASE-SEED-001.\n"
            "Current context shares rule ID CMD-001 with CASE-SEED-001.\n"
            "Current context shares evidence type shell_metacharacter_payload with CASE-SEED-001."
        ),
        language=language,
    )


def test_edge_labels_use_per_type_offset_modifier_classes() -> None:
    html = _cmd_with_similar_display().html

    # risk above, decision below, similar lifted, shares_* shifted, others default.
    for modifier in ("ge-risk", "ge-decision", "ge-similar", "ge-shares", "ge-default"):
        assert modifier in html


def test_risk_and_decision_labels_are_offset_on_opposite_sides_of_the_line() -> None:
    html = _cmd_with_similar_display().html

    risk = re.search(r'<text class="graph-edge-label ge-risk" x="[^"]+" y="([0-9.]+)"', html)
    decision = re.search(
        r'<text class="graph-edge-label ge-decision" x="[^"]+" y="([0-9.]+)"', html
    )
    assert risk is not None and decision is not None
    # Risk sits above its line and decision below, so the decision label y is larger.
    assert float(decision.group(1)) > float(risk.group(1))


def test_nodes_expose_title_tooltip_with_full_label() -> None:
    html = _cmd_with_similar_display().html

    assert "<title>Command Injection</title>" in html
    assert "<title>CASE-SEED-001</title>" in html


def test_node_text_is_left_aligned_and_edge_labels_are_centered() -> None:
    html = _cmd_with_similar_display().html

    assert 'text-anchor="start"' in html  # node text
    assert 'text-anchor="middle"' in html  # edge labels and lane headers


def test_lane_headers_share_a_consistent_baseline() -> None:
    preview = _cmd_with_similar_display().preview_svg

    header_ys = re.findall(r'<text class="graph-group-header" x="[^"]+" y="([0-9.]+)"', preview)
    assert header_ys  # headers are present
    assert set(header_ys) == {_fmt(_HEADER_Y)}  # all aligned on the same baseline


def test_lane_first_rows_are_top_aligned() -> None:
    preview = _cmd_with_similar_display().preview_svg

    node_rect_ys = re.findall(
        r'<rect x="[^"]+" y="([0-9.]+)" width="[^"]+" height="46"', preview
    )
    assert node_rect_ys
    # Top-aligned lanes start their first row at the same y, across multiple lanes.
    assert node_rect_ys.count(_fmt(float(_TOP))) >= 2


def test_bilingual_graph_labels_stay_compact() -> None:
    html = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text=_SIMILAR_CMD,
        graph_relationship_text="",
        language="bilingual",
    ).html

    # Edge labels stay single-script compact (no inline bilingual expansion).
    assert "相似" in html
    assert "相似 / similar" not in html
    # Node text keeps the raw backend value, not a bilingual-expanded form.
    assert "<title>Command Injection</title>" in html


# --- v2.6-N lightbox + copy/download UX focused tests -----------------------


def test_preview_html_contains_toolbar_buttons() -> None:
    html = _cmd_with_similar_display().html

    assert 'class="sentinel-graph-toolbar"' in html
    assert 'data-action="fullscreen"' in html
    assert 'data-action="copy"' in html
    assert 'data-action="download"' in html


def test_fullscreen_modal_container_and_close_button_exist() -> None:
    html = _cmd_with_similar_display().html

    assert 'class="sentinel-graph-modal"' in html
    assert 'class="sentinel-graph-modal-body"' in html
    assert 'data-action="close"' in html


def test_copy_and_download_buttons_exist() -> None:
    html = _cmd_with_similar_display().html

    assert html.count('class="sentinel-graph-btn"') >= 3  # fullscreen, copy, download (+close)
    # viewer script wires copy + download behavior.
    assert "navigator.clipboard" in html
    assert "execCommand('copy')" in html
    assert "URL.createObjectURL" in html
    assert "relationship-graph.svg" in html


def test_svg_markup_is_self_contained_for_copy_and_download() -> None:
    display = _cmd_with_similar_display()

    assert 'id="sentinel-graph-preview-svg"' in display.html
    assert 'id="sentinel-graph-detail-svg"' in display.html
    assert display.html.count('xmlns="http://www.w3.org/2000/svg"') >= 2
    # in-svg style keeps the copied/downloaded markup styled and standalone.
    assert ".graph-node text{" in display.detail_svg


def test_escape_key_and_status_toast_are_wired() -> None:
    html = _cmd_with_similar_display().html

    assert "Escape" in html  # ESC closes the modal
    assert 'class="sentinel-graph-status"' in html  # copy/download status toast


def test_preview_container_present() -> None:
    html = _cmd_with_similar_display().html

    assert 'class="sentinel-graph-preview"' in html


def test_toolbar_labels_render_for_zh_tw() -> None:
    html = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
        language="zh-TW",
    ).html

    assert "全螢幕檢視" in html
    assert "複製 SVG" in html
    assert "下載 SVG" in html


def test_toolbar_labels_render_for_en() -> None:
    html = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
        language="en",
    ).html

    assert "Open Fullscreen" in html
    assert "Copy SVG" in html
    assert "Download SVG" in html


def test_toolbar_labels_render_for_bilingual() -> None:
    html = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
        language="bilingual",
    ).html

    assert "全螢幕 / Fullscreen" in html
    assert "複製 SVG / Copy SVG" in html
    assert "下載 SVG / Download SVG" in html


def test_fallback_dot_still_preserved_with_toolbar() -> None:
    display = _cmd_with_similar_display()

    assert "digraph RelationshipGraph" in display.fallback_dot
    assert 'label="Current Event"' in display.fallback_dot


# --- v2.6-N preview vs detail layout focused tests --------------------------


def _viewbox(svg: str) -> tuple[float, float]:
    match = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', svg)
    assert match is not None
    return float(match.group(1)), float(match.group(2))


def test_html_contains_both_preview_and_detail_svgs_with_distinct_ids() -> None:
    display = _cmd_with_similar_display()

    assert 'id="sentinel-graph-preview-svg"' in display.html
    assert 'id="sentinel-graph-detail-svg"' in display.html
    assert "sentinel-graph-preview-svg" in display.preview_svg
    assert "sentinel-graph-detail-svg" in display.detail_svg


def test_preview_and_detail_svgs_are_not_identical() -> None:
    display = _cmd_with_similar_display()

    assert display.preview_svg
    assert display.detail_svg
    assert display.preview_svg != display.detail_svg


def test_detail_svg_has_larger_canvas_than_preview() -> None:
    display = _cmd_with_similar_display()

    preview_w, preview_h = _viewbox(display.preview_svg)
    detail_w, detail_h = _viewbox(display.detail_svg)
    assert detail_w > preview_w
    assert detail_h > preview_h


def test_fullscreen_copy_and_download_use_the_detail_svg() -> None:
    html = _cmd_with_similar_display().html

    # The viewer script binds the detail SVG id for modal clone, copy, download.
    assert '"sentinel-graph-detail-svg"' in html
    assert "var detail=root.querySelector('#'+DETAIL_ID);" in html
    assert "function detailText(){return detail?detail.outerHTML:'';}" in html
    # the script never targets the preview svg id for copy/clone.
    assert "sentinel-graph-preview-svg" not in _script_region(html)


def test_download_png_button_and_js_path_exist() -> None:
    html = _cmd_with_similar_display().html

    assert 'data-action="png"' in html
    assert "function downloadPng()" in html
    assert "canvas.toBlob(" in html
    assert "'image/png'" in html
    assert "relationship-graph.png" in html


def test_preview_hides_noisy_shared_labels() -> None:
    display = _cmd_with_similar_display(language="en")

    for noisy in ("shares attack", "shares rule", "shares evidence"):
        assert noisy not in display.preview_svg
    # but the detail layout shows them where there is room.
    for noisy in ("shares attack", "shares rule", "shares evidence"):
        assert noisy in display.detail_svg


def test_similar_edge_is_routed_as_a_rail_in_detail_only() -> None:
    display = _cmd_with_similar_display()

    # the rail class is applied to an edge path only in the detail layout.
    assert 'class="graph-edge graph-edge-rail"' in display.detail_svg
    assert 'class="graph-edge graph-edge-rail"' not in display.preview_svg


def test_relationship_chips_include_expected_values() -> None:
    html = _cmd_with_similar_display().html

    chips = _chips_region(html)
    assert chips  # chips block exists
    for value in ("HIGH", "BLOCK", "Command Injection", "CMD-001", "shell metachar payload", "CASE-SEED-001"):
        assert value in chips


def test_chip_labels_follow_selected_language() -> None:
    zh = _chips_region(
        build_interactive_relationship_graph_display(
            active_context_summary=_event_summary(),
            approved_similar_cases_text=_SIMILAR_CMD,
            graph_relationship_text="",
            language="zh-TW",
        ).html
    )
    en = _chips_region(
        build_interactive_relationship_graph_display(
            active_context_summary=_event_summary(),
            approved_similar_cases_text=_SIMILAR_CMD,
            graph_relationship_text="",
            language="en",
        ).html
    )
    assert "風險" in zh and "決策" in zh
    assert "Risk" in en and "Decision" in en
    assert "風險" not in en


def test_preview_svg_contains_graph_bg_rect() -> None:
    preview = _cmd_with_similar_display().preview_svg

    match = re.search(
        r'<rect class="graph-bg" x="0" y="0" width="([0-9.]+)" '
        r'height="([0-9.]+)" fill="#0d1117"></rect>',
        preview,
    )
    assert match is not None
    # the background rect covers the full viewBox.
    width, height = _viewbox(preview)
    assert float(match.group(1)) == width
    assert float(match.group(2)) == height


def test_detail_svg_contains_graph_bg_rect() -> None:
    detail = _cmd_with_similar_display().detail_svg

    match = re.search(
        r'<rect class="graph-bg" x="0" y="0" width="([0-9.]+)" '
        r'height="([0-9.]+)" fill="#0d1117"></rect>',
        detail,
    )
    assert match is not None
    width, height = _viewbox(detail)
    assert float(match.group(1)) == width
    assert float(match.group(2)) == height


def test_graph_bg_rect_appears_before_headers_edges_and_nodes() -> None:
    display = _cmd_with_similar_display()

    for svg in (display.preview_svg, display.detail_svg):
        bg_pos = svg.find('<rect class="graph-bg"')
        headers_pos = svg.find('<g class="graph-headers"')
        edges_pos = svg.find('<g class="graph-edges"')
        nodes_pos = svg.find('<g class="graph-nodes"')
        assert 0 <= bg_pos < headers_pos < edges_pos < nodes_pos


def test_copy_and_download_use_detail_svg_with_embedded_dark_background() -> None:
    display = _cmd_with_similar_display()

    # Copy/Download both read detail.outerHTML in the viewer script, and the
    # detail SVG carries its own background so standalone files stay dark.
    assert "function detailText(){return detail?detail.outerHTML:'';}" in display.html
    assert "'#0d1117'" in display.detail_svg or 'fill="#0d1117"' in display.detail_svg


def test_detail_svg_remains_self_contained_with_xmlns_style_and_background() -> None:
    detail = _cmd_with_similar_display().detail_svg

    assert 'xmlns="http://www.w3.org/2000/svg"' in detail
    assert "<style>" in detail
    assert 'class="graph-bg"' in detail


def test_fallback_dot_is_unchanged_after_background_correction() -> None:
    display = _cmd_with_similar_display()

    # The DOT graph is still generated by the base relationship_graph builder
    # and must not be touched by the SVG background correction.
    assert "digraph RelationshipGraph" in display.fallback_dot
    assert 'label="Current Event"' in display.fallback_dot
    assert 'label="CASE-SEED-001"' in display.fallback_dot
    assert "graph-bg" not in display.fallback_dot


def test_download_png_label_follows_language() -> None:
    zh = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
        language="zh-TW",
    ).html
    en = build_interactive_relationship_graph_display(
        active_context_summary=_event_summary(),
        approved_similar_cases_text="",
        graph_relationship_text="",
        language="en",
    ).html
    assert "下載 PNG" in zh
    assert "Download PNG" in en
