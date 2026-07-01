
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from modules.runtime_health import (
    ChromaHealth,
    EmbeddingHealth,
    FallbackHealth,
    ModelHealth,
    OllamaHealth,
    RagHealth,
    RuntimeHealthConfig,
    RuntimeHealthStatus,
)
from modules.ui.runtime_health_view import (
    PASSIVE_HEALTH_BOUNDARY,
    build_runtime_health_panel_html,
    collect_live_ollama_runtime_health,
    collect_passive_runtime_health,
)

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_health_renderer_formats_passive_statuses() -> None:
    html = build_runtime_health_panel_html(_health())

    assert "Provider mode" in html
    assert "disabled" in html
    assert "Fallback" in html
    assert "available" in html
    assert "Ollama server" in html
    assert "not_checked" in html
    assert "RAG runtime" in html
    assert "lazy_not_initialized" in html
    assert "Embeddings" in html
    assert "configured" in html
    assert PASSIVE_HEALTH_BOUNDARY in html


def test_runtime_health_view_does_not_import_heavy_modules() -> None:
    code = """
import importlib
import json
import sys
forbidden = [
    'modules.rag_qa',
    'chromadb',
    'sentence_transformers',
    'langchain_community',
    'torch',
]
before = {
    name for name in forbidden
    if any(module == name or module.startswith(name + '.') for module in sys.modules)
}
importlib.import_module('modules.ui.runtime_health_view')
after = {
    name for name in forbidden
    if any(module == name or module.startswith(name + '.') for module in sys.modules)
}
print(json.dumps(sorted(after - before)))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout.strip().splitlines()[-1]) == []


def test_passive_wrapper_calls_collect_runtime_health_without_live_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    view = importlib.import_module("modules.ui.runtime_health_view")
    calls: list[dict[str, object]] = []
    health = _health()

    def fake_collect(**kwargs: object) -> RuntimeHealthStatus:
        calls.append(kwargs)
        return health

    monkeypatch.setattr(view, "collect_runtime_health", fake_collect)

    assert collect_passive_runtime_health() is health
    assert calls == [{}]


def test_live_wrapper_enables_ollama_and_model_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    view = importlib.import_module("modules.ui.runtime_health_view")
    calls: list[dict[str, object]] = []
    health = _health()

    def fake_collect(**kwargs: object) -> RuntimeHealthStatus:
        calls.append(kwargs)
        return health

    monkeypatch.setattr(view, "collect_runtime_health", fake_collect)

    assert collect_live_ollama_runtime_health() is health
    assert calls == [{"check_ollama": True, "check_models": True}]


def test_streamlit_app_wires_passive_and_explicit_live_health_paths() -> None:
    source = (ROOT / "ui" / "streamlit_app.py").read_text(encoding="utf-8")

    assert "collect_passive_runtime_health()" in source
    assert "collect_live_ollama_runtime_health()" in source
    assert "Check live Ollama / models" in source
    assert "RAGQA.is_ready" not in source


def test_runtime_health_view_does_not_touch_detector_risk_or_decision_modules() -> None:
    code = """
import importlib
import json
import sys
importlib.import_module('modules.ui.runtime_health_view')
touched = sorted(
    name for name in sys.modules
    if name.startswith('modules.detector')
    or name.startswith('modules.triage_policy')
    or name.startswith('modules.responder')
)
print(json.dumps(touched))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout.strip().splitlines()[-1]) == []


def _health() -> RuntimeHealthStatus:
    return RuntimeHealthStatus(
        provider_mode="disabled",
        config=RuntimeHealthConfig(
            primary_model_name="qwen2.5:7b",
            agent_model_name="gemma4:e4b",
            chroma_path="./chroma_db",
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
            top_k=5,
        ),
        ollama_server=OllamaHealth(
            status="not_checked",
            endpoint="http://localhost:11434",
            checked=False,
        ),
        primary_model=ModelHealth(
            status="not_checked",
            model_name="qwen2.5:7b",
            checked=False,
        ),
        agent_model=ModelHealth(
            status="not_checked",
            model_name="gemma4:e4b",
            checked=False,
        ),
        chroma_path=ChromaHealth(status="exists", path="./chroma_db", checked=True),
        rag_runtime=RagHealth(status="lazy_not_initialized", checked=False),
        embeddings=EmbeddingHealth(
            status="configured",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            checked=False,
        ),
        fallback=FallbackHealth(status="available", detail="fallback available"),
        passive=True,
    )
