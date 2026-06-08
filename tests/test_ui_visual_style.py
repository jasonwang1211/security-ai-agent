import sys
from pathlib import Path

from modules.ui.visual_style import (
    ADVISORY_COLOR,
    DETERMINISTIC_COLOR,
    NEUTRAL_COLOR,
    apply_console_css,
    badge_html,
    decision_color,
    safe_color,
    severity_color,
    severity_left_class,
)


def test_severity_color_high_uses_standard_red() -> None:
    assert severity_color("HIGH") == "#E14B4B"


def test_severity_color_is_case_insensitive() -> None:
    assert severity_color("medium") == "#F5A623"
    assert severity_color("low") == "#10B981"


def test_unknown_severity_returns_neutral_color() -> None:
    assert severity_color("definitely-not-a-level") == NEUTRAL_COLOR
    assert severity_color(None) == NEUTRAL_COLOR
    assert severity_color("") == NEUTRAL_COLOR


def test_decision_color_block_uses_standard_red() -> None:
    assert decision_color("BLOCK") == "#E14B4B"
    assert decision_color("monitor") == "#F5A623"
    assert decision_color("allow") == "#10B981"


def test_unknown_decision_returns_neutral_color() -> None:
    assert decision_color("escalate") == NEUTRAL_COLOR
    assert decision_color(None) == NEUTRAL_COLOR


def test_badge_html_escapes_unsafe_label_text() -> None:
    badge = badge_html("<script>alert(1)</script>", DETERMINISTIC_COLOR)

    assert "<script>" not in badge
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in badge
    assert "sentinel-pill" in badge


def test_badge_html_includes_and_escapes_title_when_provided() -> None:
    badge = badge_html("LABEL", ADVISORY_COLOR, title='evil" onmouseover="x')

    assert 'title="' in badge
    assert "evil&quot; onmouseover=&quot;x" in badge
    assert 'onmouseover="x"' not in badge


def test_badge_html_omits_title_attribute_when_not_provided() -> None:
    badge = badge_html("LABEL", DETERMINISTIC_COLOR)

    assert "title=" not in badge


def test_badge_html_rejects_unsafe_color_and_falls_back_to_neutral() -> None:
    badge = badge_html("LABEL", "red; background:url(javascript:alert(1))")

    assert "javascript:" not in badge
    assert NEUTRAL_COLOR in badge


def test_safe_color_validates_hex_values() -> None:
    assert safe_color("#3B82F6") == "#3B82F6"
    assert safe_color("#fff") == "#fff"
    assert safe_color("not-a-color") == NEUTRAL_COLOR
    assert safe_color(None) == NEUTRAL_COLOR


def test_severity_left_class_maps_levels() -> None:
    assert severity_left_class("HIGH") == "sentinel-severity-left-high"
    assert severity_left_class("medium") == "sentinel-severity-left-medium"
    assert severity_left_class("LOW") == "sentinel-severity-left-low"
    assert severity_left_class("unknown") == ""


def test_apply_console_css_contains_required_class_names() -> None:
    css = apply_console_css()

    for class_name in (
        ".sentinel-status-bar",
        ".sentinel-status-row",
        ".sentinel-card",
        ".sentinel-hero-card",
        ".sentinel-pill",
        ".sentinel-code",
        ".sentinel-muted",
        ".sentinel-severity-left-high",
        ".sentinel-severity-left-medium",
        ".sentinel-severity-left-low",
        ".sentinel-deterministic",
        ".sentinel-advisory",
    ):
        assert class_name in css


def test_apply_console_css_includes_v2_6t_cyber_classes() -> None:
    css = apply_console_css()

    for class_name in (
        ".stApp",
        ".sentinel-panel-heading",
        ".sentinel-chip",
        ".sentinel-empty-card",
        "--sentinel-cyan",
    ):
        assert class_name in css


def test_apply_console_css_includes_v2_6u_dashboard_density_classes() -> None:
    css = apply_console_css()

    for class_name in (
        ".sentinel-section-title",
        ".sentinel-demo-body",
        ".sentinel-demo-title",
        ".sentinel-meta-row",
        ".sentinel-pill-outline",
        ".sentinel-stat-grid",
        ".sentinel-stat-value",
        ".sentinel-hero-badges",
    ):
        assert class_name in css


def test_apply_console_css_avoids_keyframe_animations() -> None:
    # Subtle hover transitions are allowed; full keyframe animations are not,
    # to avoid restarting effects on every Streamlit rerun.
    css = apply_console_css()

    assert "@keyframes" not in css
    assert "animation:" not in css


def test_apply_console_css_returns_only_style_text() -> None:
    css = apply_console_css()

    assert "<style>" not in css
    assert "<script" not in css


def test_visual_style_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/visual_style.py").read_text(encoding="utf-8")

    assert "streamlit" not in source.lower()
    assert "streamlit" not in sys.modules
