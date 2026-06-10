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
  --sentinel-cyan: #22D3EE;
  --sentinel-bg: #060912;
  --sentinel-surface: rgba(20, 27, 38, 0.72);
  --sentinel-surface-alt: rgba(27, 35, 50, 0.82);
  --sentinel-border: rgba(86, 116, 156, 0.28);
  --sentinel-border-strong: rgba(34, 211, 238, 0.40);
  --sentinel-text-muted: #9aa7b8;
  --sentinel-shadow: 0 10px 30px rgba(2, 6, 14, 0.55);
  --sentinel-glow-cyan: 0 0 0 1px rgba(34, 211, 238, 0.20), 0 10px 30px rgba(2, 6, 14, 0.55);
}
/* Deep navy command-center backdrop with subtle cyan/purple corner glows. */
.stApp {
  background:
    radial-gradient(1100px 560px at 14% -8%, rgba(34, 211, 238, 0.07), transparent 60%),
    radial-gradient(1000px 700px at 100% 0%, rgba(139, 92, 246, 0.08), transparent 55%),
    linear-gradient(160deg, #0a1120 0%, #060912 58%, #04070e 100%);
  background-attachment: fixed;
}
[data-testid="stHeader"] { background: transparent; }
/* Bordered containers become glass "section cards" with hover glow. */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--sentinel-surface);
  border: 1px solid var(--sentinel-border);
  border-radius: 14px;
  box-shadow: var(--sentinel-shadow);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
  transition: border-color 160ms ease, box-shadow 160ms ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: var(--sentinel-border-strong);
  box-shadow: var(--sentinel-glow-cyan);
}
.sentinel-status-bar {
  background: linear-gradient(180deg, rgba(22, 30, 44, 0.86), rgba(13, 19, 29, 0.86));
  border: 1px solid var(--sentinel-border);
  border-radius: 14px;
  padding: 14px 18px;
  margin-bottom: 8px;
  box-shadow: var(--sentinel-shadow);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
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
  font-size: 1.08rem;
  letter-spacing: 0.3px;
  color: #e8eef7;
  text-shadow: 0 0 18px rgba(34, 211, 238, 0.25);
}
.sentinel-card {
  background: var(--sentinel-surface);
  border: 1px solid var(--sentinel-border);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: var(--sentinel-shadow);
}
.sentinel-hero-card {
  background: linear-gradient(180deg, rgba(27, 35, 50, 0.90), rgba(18, 24, 36, 0.90));
  border: 1px solid var(--sentinel-border);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: var(--sentinel-shadow);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
  transition: border-color 160ms ease, box-shadow 160ms ease;
}
.sentinel-hero-card:hover {
  border-color: var(--sentinel-border-strong);
  box-shadow: var(--sentinel-glow-cyan);
}
.sentinel-hero-title {
  font-size: 1.45rem;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: #eef3fa;
}
.sentinel-hero-sub {
  color: var(--sentinel-text-muted);
  font-size: 0.85rem;
  margin-bottom: 10px;
}
/* Reusable neon-accent heading for section cards. */
.sentinel-panel-heading {
  font-size: 1.02rem;
  font-weight: 700;
  letter-spacing: 0.3px;
  margin: 2px 0 6px 0;
  padding-left: 11px;
  border-left: 3px solid var(--sentinel-cyan);
  color: #e6edf6;
}
.sentinel-pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  color: #0b0f14;
  font-weight: 600;
  font-size: 0.8rem;
  line-height: 1.5;
  box-shadow: 0 1px 10px rgba(2, 6, 14, 0.35);
}
.sentinel-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.10);
  color: #cfe9dd;
  font-size: 0.8rem;
  box-shadow: inset 0 0 12px rgba(16, 185, 129, 0.08);
}
.sentinel-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: #0a0f17;
  border: 1px solid var(--sentinel-border);
  border-radius: 8px;
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
.sentinel-stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.sentinel-stat {
  background: rgba(10, 16, 26, 0.55);
  border: 1px solid var(--sentinel-border);
  border-radius: 10px;
  padding: 9px 12px;
}
.sentinel-stat-label {
  color: var(--sentinel-text-muted);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.sentinel-stat-value {
  font-weight: 600;
  font-size: 0.95rem;
  margin-top: 3px;
  color: #e8eef7;
  word-break: break-word;
}
.sentinel-stat-value.sentinel-code {
  margin-top: 5px;
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
  border: 1px dashed var(--sentinel-border-strong);
  border-radius: 14px;
  padding: 14px 18px;
  color: var(--sentinel-text-muted);
  text-align: center;
  background: rgba(20, 27, 38, 0.40);
}
.sentinel-empty-icon { font-size: 1.05rem; margin-right: 6px; opacity: 0.85; }
/* Workspace group tabs: neon-cyan active accent. */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }
.stTabs [aria-selected="true"] { color: var(--sentinel-cyan) !important; }
/* Buttons: subtle cyan hover glow (primary accent comes from the theme). */
.stButton > button {
  border-radius: 10px;
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 120ms ease;
}
.stButton > button:hover {
  border-color: var(--sentinel-cyan);
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.25), 0 6px 18px rgba(34, 211, 238, 0.10);
}
.stButton > button:active { transform: translateY(1px); }
/* Inputs: cyan focus ring to match the command-center accent. */
.stTextArea textarea:focus,
.stTextInput input:focus {
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.45);
}
/* Code blocks: faint cyan inner glow. */
[data-testid="stCode"], .stCode {
  border-radius: 8px;
  box-shadow: inset 0 0 26px rgba(34, 211, 238, 0.045);
}
/* Denser vertical rhythm inside glass cards (less form-like spacing). */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] { gap: 0.6rem; }
/* Compact neon section titles (replace default subheaders). */
.sentinel-section-title {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 1.18rem;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #eef3fa;
  margin: 2px 0 10px 0;
}
.sentinel-section-title::before {
  content: "";
  width: 4px;
  height: 1.05em;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--sentinel-cyan), var(--sentinel-deterministic));
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.45);
}
/* SOC playbook demo cards. */
.sentinel-demo-body { display: flex; flex-direction: column; gap: 7px; }
.sentinel-demo-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 0.98rem;
  color: #e8eef7;
}
.sentinel-demo-title::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--sentinel-cyan);
  box-shadow: 0 0 8px var(--sentinel-cyan);
}
.sentinel-demo-desc {
  color: var(--sentinel-text-muted);
  font-size: 0.8rem;
  line-height: 1.35;
}
.sentinel-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.sentinel-meta-label {
  color: var(--sentinel-text-muted);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.sentinel-pill-outline {
  display: inline-block;
  padding: 1px 9px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.74rem;
  line-height: 1.6;
  border: 1px solid var(--sentinel-border-strong);
  color: #cfe9f2;
  background: rgba(34, 211, 238, 0.08);
}
.sentinel-pill-case {
  border-color: rgba(139, 92, 246, 0.5);
  color: #d9ccff;
  background: rgba(139, 92, 246, 0.12);
}
/* Active-context hero: more obvious risk/decision badges. */
.sentinel-hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 4px 0 2px 0;
}
.sentinel-hero-badges .sentinel-pill {
  font-size: 0.92rem;
  padding: 3px 14px;
}
/* AI Analyst readable response card (prose; wraps; no horizontal scroll). */
.sentinel-ai-card {
  background: var(--sentinel-surface);
  border: 1px solid var(--sentinel-border);
  border-left: 3px solid var(--sentinel-advisory);
  border-radius: 12px;
  padding: 12px 16px;
  margin-top: 6px;
}
.sentinel-ai-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #ddd2ff;
  background: rgba(139, 92, 246, 0.16);
  border: 1px solid rgba(139, 92, 246, 0.45);
  border-radius: 999px;
  padding: 2px 10px;
  margin-bottom: 8px;
}
.sentinel-ai-q {
  color: var(--sentinel-text-muted);
  font-size: 0.85rem;
  margin-bottom: 8px;
  overflow-wrap: anywhere;
}
.sentinel-ai-body {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.65;
  font-size: 0.95rem;
  color: #e6edf6;
}
.sentinel-ai-boundary {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--sentinel-border);
  color: var(--sentinel-text-muted);
  font-size: 0.78rem;
  overflow-wrap: anywhere;
}
.sentinel-ai-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 8px;
}
.sentinel-ai-chip {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--sentinel-text-muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--sentinel-border);
  border-radius: 999px;
  padding: 2px 10px;
  overflow-wrap: anywhere;
}
.sentinel-ai-chip.advisory {
  color: #f3d39b;
  border-color: rgba(245, 166, 35, 0.40);
  background: rgba(245, 166, 35, 0.10);
}
/* Friendly RAG empty-result card (amber accent, not a failure look). */
.sentinel-ai-empty {
  border-left-color: var(--sentinel-medium);
}
/* Route color-coding: deterministic follow-up = cyan, RAG knowledge = purple. */
.sentinel-ai-card.sentinel-ai-followup { border-left-color: var(--sentinel-cyan); }
.sentinel-ai-card.sentinel-ai-knowledge { border-left-color: var(--sentinel-advisory); }
.sentinel-ai-badge.followup {
  color: #bdeefb;
  background: rgba(34, 211, 238, 0.14);
  border-color: rgba(34, 211, 238, 0.50);
}
.sentinel-ai-badge.knowledge {
  color: #ddd2ff;
  background: rgba(139, 92, 246, 0.16);
  border-color: rgba(139, 92, 246, 0.45);
}
/* Analysis-mode banner above the report: fast = cyan, full AI-assisted = purple. */
.sentinel-mode-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 10px;
  padding: 8px 14px;
  margin: 2px 0 10px 0;
  font-size: 0.86rem;
  font-weight: 600;
  border: 1px solid var(--sentinel-border);
  overflow-wrap: anywhere;
}
.sentinel-mode-banner-icon { font-size: 1rem; }
.sentinel-mode-banner.fast {
  color: #cfeefb;
  background: rgba(34, 211, 238, 0.10);
  border-color: rgba(34, 211, 238, 0.40);
  border-left: 3px solid var(--sentinel-cyan);
}
.sentinel-mode-banner.full {
  color: #ddd2ff;
  background: rgba(139, 92, 246, 0.12);
  border-color: rgba(139, 92, 246, 0.40);
  border-left: 3px solid var(--sentinel-advisory);
}
/* v2.7-B Evidence Gap Analyzer panel: deterministic advisory analyst context.
   Confirmed = green, Missing = amber, Checks = cyan, Unsafe = red,
   Advisory boundary = purple. */
.sentinel-brief { display: flex; flex-direction: column; gap: 10px; }
.sentinel-brief-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.sentinel-brief-chip {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--sentinel-text-muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--sentinel-border);
  border-radius: 999px;
  padding: 2px 10px;
  overflow-wrap: anywhere;
}
.sentinel-brief-chip.det {
  color: #bdeefb;
  background: rgba(34, 211, 238, 0.12);
  border-color: rgba(34, 211, 238, 0.45);
}
.sentinel-brief-section {
  border: 1px solid var(--sentinel-border);
  border-left: 3px solid var(--sentinel-info);
  border-radius: 10px;
  padding: 9px 12px;
  background: rgba(10, 16, 26, 0.45);
}
.sentinel-brief-section.deterministic { border-left-color: var(--sentinel-cyan); }
.sentinel-brief-section.advisory { border-left-color: var(--sentinel-advisory); }
.sentinel-brief-section.gap { border-left-color: var(--sentinel-medium); }
.sentinel-brief-section.unsafe {
  border-left-color: var(--sentinel-high);
  background: rgba(225, 75, 75, 0.06);
}
.sentinel-brief-h {
  font-weight: 700;
  font-size: 0.88rem;
  letter-spacing: 0.2px;
  margin-bottom: 4px;
  color: #e6edf6;
}
.sentinel-brief-section.deterministic .sentinel-brief-h { color: #bdeefb; }
.sentinel-brief-section.advisory .sentinel-brief-h { color: #ddd2ff; }
.sentinel-brief-section.gap .sentinel-brief-h { color: #f3d39b; }
.sentinel-brief-section.unsafe .sentinel-brief-h { color: #ffb4bc; }
.sentinel-brief-section ul { margin: 2px 0 0 0; padding-left: 18px; }
.sentinel-brief-section li {
  margin: 3px 0;
  line-height: 1.55;
  font-size: 0.9rem;
  color: #e6edf6;
  overflow-wrap: anywhere;
}
.sentinel-brief-boundary {
  border-left: 3px solid var(--sentinel-advisory);
  background: rgba(139, 92, 246, 0.10);
  border-radius: 10px;
  padding: 9px 12px;
  color: #ddd2ff;
  font-size: 0.8rem;
  overflow-wrap: anywhere;
}
.sentinel-gap { display: flex; flex-direction: column; gap: 10px; }
.sentinel-gap-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.sentinel-gap-chip {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--sentinel-text-muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--sentinel-border);
  border-radius: 999px;
  padding: 2px 10px;
  overflow-wrap: anywhere;
}
.sentinel-gap-chip.det {
  color: #bdeefb;
  background: rgba(34, 211, 238, 0.12);
  border-color: rgba(34, 211, 238, 0.45);
}
.sentinel-gap-section {
  border: 1px solid var(--sentinel-border);
  border-left: 3px solid var(--sentinel-info);
  border-radius: 10px;
  padding: 9px 12px;
  background: rgba(10, 16, 26, 0.45);
}
.sentinel-gap-section.confirmed { border-left-color: var(--sentinel-low); }
.sentinel-gap-section.missing { border-left-color: var(--sentinel-medium); }
.sentinel-gap-section.checks { border-left-color: var(--sentinel-cyan); }
.sentinel-gap-section.unsafe {
  border-left-color: var(--sentinel-high);
  background: rgba(225, 75, 75, 0.06);
}
.sentinel-gap-h {
  display: flex;
  align-items: center;
  gap: 7px;
  font-weight: 700;
  font-size: 0.88rem;
  letter-spacing: 0.2px;
  margin-bottom: 4px;
}
.sentinel-gap-section.confirmed .sentinel-gap-h { color: #9ff0d0; }
.sentinel-gap-section.missing .sentinel-gap-h { color: #f3d39b; }
.sentinel-gap-section.checks .sentinel-gap-h { color: #bdeefb; }
.sentinel-gap-section.unsafe .sentinel-gap-h { color: #ffb4bc; }
.sentinel-gap-section ul { margin: 2px 0 0 0; padding-left: 18px; }
.sentinel-gap-section li {
  margin: 3px 0;
  line-height: 1.55;
  font-size: 0.9rem;
  color: #e6edf6;
  overflow-wrap: anywhere;
}
.sentinel-gap-boundary {
  border-left: 3px solid var(--sentinel-advisory);
  background: rgba(139, 92, 246, 0.10);
  border-radius: 10px;
  padding: 9px 12px;
  color: #ddd2ff;
  font-size: 0.8rem;
  overflow-wrap: anywhere;
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
