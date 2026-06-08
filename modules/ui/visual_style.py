"""Pure visual-style helpers for the SOC analyst console.

This module is presentation-only and framework-light. It returns plain
strings (color codes, HTML badge fragments, and a CSS block) so the UI layer
can inject them. It must not import any UI rendering framework, must not
change backend detection, risk scoring, or decision logic, and must not
perform any real enforcement action.
"""

from __future__ import annotations

import html
import re

SEVERITY_COLORS: dict[str, str] = {
    "HIGH": "#E14B4B",
    "MEDIUM": "#F5A623",
    "LOW": "#10B981",
    "INFO": "#6B7280",
}

DECISION_COLORS: dict[str, str] = {
    "BLOCK": "#E14B4B",
    "MONITOR": "#F5A623",
    "ALLOW": "#10B981",
}

DETERMINISTIC_COLOR = "#3B82F6"
ADVISORY_COLOR = "#8B5CF6"
NEUTRAL_COLOR = SEVERITY_COLORS["INFO"]

_HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")


def severity_color(value: str | None) -> str:
    """Return the standardized color for a severity / risk level value.

    Matching is case-insensitive. Unknown or blank values return the neutral
    INFO color so the UI degrades safely instead of raising.
    """

    key = str(value or "").strip().upper()
    return SEVERITY_COLORS.get(key, NEUTRAL_COLOR)


def decision_color(value: str | None) -> str:
    """Return the standardized color for a simulated decision value.

    Matching is case-insensitive. Unknown or blank values return the neutral
    INFO color. Decisions remain simulated; color is presentation only.
    """

    key = str(value or "").strip().upper()
    return DECISION_COLORS.get(key, NEUTRAL_COLOR)


def safe_color(value: str | None) -> str:
    """Return a validated hex color, falling back to the neutral color.

    This guards inline-style injection: only well-formed hex colors are
    allowed; anything else degrades to the neutral color.
    """

    text = str(value or "").strip()
    return text if _HEX_COLOR_PATTERN.match(text) else NEUTRAL_COLOR


def badge_html(label: str, color: str, *, title: str | None = None) -> str:
    """Return an inline HTML pill badge with escaped label and title text.

    Label and optional title are HTML-escaped to prevent markup injection,
    and the color is validated to a safe hex value.
    """

    safe_label = html.escape(str(label))
    color_value = safe_color(color)
    title_attr = ""
    if title is not None:
        safe_title = html.escape(str(title), quote=True)
        title_attr = f' title="{safe_title}"'
    return (
        f'<span class="sentinel-pill"{title_attr} '
        f'style="background:{color_value};">{safe_label}</span>'
    )


def apply_console_css() -> str:
    """Return the console CSS block as text.

    The caller is responsible for injecting this string. The CSS defines a
    small, maintainable set of ``sentinel-*`` classes and intentionally does
    not aggressively override framework-internal DOM classes.
    """

    return """
:root {
  --sentinel-high: #E14B4B;
  --sentinel-medium: #F5A623;
  --sentinel-low: #10B981;
  --sentinel-info: #6B7280;
  --sentinel-deterministic: #3B82F6;
  --sentinel-advisory: #8B5CF6;
  --sentinel-surface: #11161d;
  --sentinel-surface-alt: #161d26;
  --sentinel-border: #243042;
  --sentinel-text-muted: #9aa7b8;
}
.sentinel-status-bar {
  background: var(--sentinel-surface);
  border: 1px solid var(--sentinel-border);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 8px;
}
.sentinel-status-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin: 2px 0;
}
.sentinel-status-row + .sentinel-status-row {
  margin-top: 8px;
  border-top: 1px solid var(--sentinel-border);
  padding-top: 8px;
}
.sentinel-status-title {
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: 0.2px;
}
.sentinel-card {
  background: var(--sentinel-surface);
  border: 1px solid var(--sentinel-border);
  border-radius: 10px;
  padding: 14px 16px;
}
.sentinel-hero-card {
  background: var(--sentinel-surface-alt);
  border: 1px solid var(--sentinel-border);
  border-radius: 12px;
  padding: 16px 18px;
}
.sentinel-hero-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0 0 4px 0;
}
.sentinel-hero-sub {
  color: var(--sentinel-text-muted);
  font-size: 0.85rem;
  margin-bottom: 10px;
}
.sentinel-pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  color: #0b0f14;
  font-weight: 600;
  font-size: 0.8rem;
  line-height: 1.5;
}
.sentinel-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 8px;
  border: 1px solid var(--sentinel-border);
  background: var(--sentinel-surface-alt);
  color: var(--sentinel-text-muted);
  font-size: 0.8rem;
}
.sentinel-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: #0d1117;
  border: 1px solid var(--sentinel-border);
  border-radius: 6px;
  padding: 6px 10px;
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.85rem;
}
.sentinel-muted {
  color: var(--sentinel-text-muted);
  font-size: 0.85rem;
}
.sentinel-kv {
  display: inline-flex;
  flex-direction: column;
  gap: 2px;
  margin-right: 22px;
}
.sentinel-kv-label {
  color: var(--sentinel-text-muted);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.sentinel-kv-value {
  font-weight: 600;
  font-size: 0.95rem;
}
.sentinel-severity-left-high { border-left: 4px solid var(--sentinel-high); }
.sentinel-severity-left-medium { border-left: 4px solid var(--sentinel-medium); }
.sentinel-severity-left-low { border-left: 4px solid var(--sentinel-low); }
.sentinel-deterministic {
  border-left: 3px solid var(--sentinel-deterministic);
  padding-left: 10px;
}
.sentinel-advisory {
  border-left: 3px solid var(--sentinel-advisory);
  padding-left: 10px;
}
.sentinel-empty-card {
  border: 1px dashed var(--sentinel-border);
  border-radius: 12px;
  padding: 18px;
  color: var(--sentinel-text-muted);
  text-align: center;
}
""".strip()


def severity_left_class(value: str | None) -> str:
    """Return the severity-colored left-border class for a risk level value."""

    key = str(value or "").strip().upper()
    if key == "HIGH":
        return "sentinel-severity-left-high"
    if key == "MEDIUM":
        return "sentinel-severity-left-medium"
    if key == "LOW":
        return "sentinel-severity-left-low"
    return ""
