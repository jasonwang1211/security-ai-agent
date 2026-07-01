
"""Pure HTML renderer for v3.8 runtime health status.

The renderer accepts a precomputed RuntimeHealthStatus. The small collection
wrappers are explicit Streamlit-facing helpers so tests can verify passive vs
live-check arguments without importing Streamlit.
"""

from __future__ import annotations

import html

from modules.runtime_health import RuntimeHealthStatus, collect_runtime_health

PASSIVE_HEALTH_BOUNDARY = (
    "Passive health check does not start Ollama, initialize Chroma, initialize "
    "embeddings, or call RAGQA.is_ready()."
)
ACTIVE_HEALTH_BOUNDARY = (
    "Live health check contacts Ollama /api/tags only; it does not initialize "
    "RAG, Chroma, embeddings, or call RAGQA.is_ready()."
)


def collect_passive_runtime_health() -> RuntimeHealthStatus:
    """Collect default passive status for safe Streamlit startup."""

    return collect_runtime_health()


def collect_live_ollama_runtime_health() -> RuntimeHealthStatus:
    """Collect explicitly requested local Ollama/model status."""

    return collect_runtime_health(passive=False, check_ollama=True, check_models=True)


def build_runtime_health_panel_html(health: RuntimeHealthStatus) -> str:
    """Return escaped HTML for a compact runtime health panel."""

    rows = [
        ("Provider mode", health.provider_mode),
        ("Fallback", health.fallback.status),
        ("Ollama server", health.ollama_server.status),
        ("Primary model", _model_status(health.primary_model.model_name, health.primary_model.status)),
        ("Agent model", _model_status(health.agent_model.model_name, health.agent_model.status)),
        ("Chroma path", f"{health.chroma_path.status} · {health.chroma_path.path}"),
        ("Embeddings", _model_status(health.embeddings.model_name, health.embeddings.status)),
        ("RAG runtime", health.rag_runtime.status),
    ]
    row_html = "".join(_status_row(label, value) for label, value in rows)
    mode_label = "passive" if health.passive else "active_live_check"
    boundary = PASSIVE_HEALTH_BOUNDARY if health.passive else ACTIVE_HEALTH_BOUNDARY
    return (
        '<div class="sentinel-brief runtime-health">'
        '<div class="sentinel-brief-meta">'
        f'<span class="sentinel-brief-chip det">runtime_health: {html.escape(mode_label)}</span>'
        f'<span class="sentinel-brief-chip">fallback: {html.escape(health.fallback.status)}</span>'
        "</div>"
        '<div class="sentinel-section-title">Runtime Health</div>'
        f'<div class="sentinel-muted">{html.escape(boundary)}</div>'
        '<div class="sentinel-kv-grid">'
        f"{row_html}"
        "</div>"
        f'<div class="sentinel-advisory">{html.escape(health.fallback.detail)}</div>'
        "</div>"
    )


def _model_status(model_name: str, status: str) -> str:
    if model_name:
        return f"{status} · {model_name}"
    return status


def _status_row(label: str, value: str) -> str:
    readable = f"{label}: {value}"
    return (
        f'<div class="sentinel-kv-row" aria-label="{html.escape(readable)}">'
        f'<span class="sentinel-kv-label">{html.escape(label)}:</span> '
        f'<span class="sentinel-kv-value">{html.escape(value)}</span>'
        "</div>"
    )


__all__ = [
    "ACTIVE_HEALTH_BOUNDARY",
    "PASSIVE_HEALTH_BOUNDARY",
    "build_runtime_health_panel_html",
    "collect_live_ollama_runtime_health",
    "collect_passive_runtime_health",
]
