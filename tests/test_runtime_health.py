
import importlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.error import URLError

import pytest

from modules.runtime_health import RuntimeHealthConfig, collect_runtime_health

ROOT = Path(__file__).resolve().parents[1]


def test_importing_runtime_health_does_not_import_heavy_modules() -> None:
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
importlib.import_module('modules.runtime_health')
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


def test_default_passive_probe_does_not_contact_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_health = importlib.import_module("modules.runtime_health")

    def fail_if_called(_url: str, _timeout_seconds: float) -> dict[str, object]:
        raise AssertionError("default passive probe must not contact Ollama")

    monkeypatch.setattr(runtime_health, "_http_get_json", fail_if_called)

    result = collect_runtime_health()

    assert result.ollama_server.status == "not_checked"
    assert result.primary_model.status == "not_checked"
    assert result.agent_model.status == "not_checked"
    assert result.rag_runtime.status == "lazy_not_initialized"
    assert result.embeddings.status == "configured"
    assert result.fallback.status == "available"


def test_default_passive_probe_returns_configured_model_names() -> None:
    result = collect_runtime_health(check_chroma_path=False)

    assert result.config.primary_model_name == "qwen2.5:7b"
    assert result.config.agent_model_name == "gemma4:e4b"
    assert result.config.embedding_model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert result.config.top_k == 5
    assert result.provider_mode == "disabled"


def test_missing_chroma_path_returns_missing_without_crash(tmp_path: Path) -> None:
    config = _config(tmp_path / "missing_chroma")

    result = collect_runtime_health(config=config)

    assert result.chroma_path.status == "missing"
    assert result.chroma_path.checked is True
    assert result.chroma_path.path == str(tmp_path / "missing_chroma")


def test_existing_chroma_path_returns_exists_without_initializing_chroma(tmp_path: Path) -> None:
    chroma_path = tmp_path / "chroma_db"
    chroma_path.mkdir()
    config = _config(chroma_path)
    before = set(sys.modules)

    result = collect_runtime_health(config=config)

    after = set(sys.modules)
    assert result.chroma_path.status == "exists"
    assert "modules.rag_qa" not in after - before
    assert "chromadb" not in after - before


def test_ollama_unreachable_returns_status_not_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_health = importlib.import_module("modules.runtime_health")

    def raise_unreachable(_url: str, _timeout_seconds: float) -> dict[str, object]:
        raise URLError("connection refused")

    monkeypatch.setattr(runtime_health, "_http_get_json", raise_unreachable)

    result = collect_runtime_health(check_ollama=True, check_models=True, config=_config())

    assert result.ollama_server.status == "unreachable"
    assert result.primary_model.status == "unavailable"
    assert result.agent_model.status == "unavailable"


def test_model_check_reports_ready_and_missing_when_ollama_reachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_health = importlib.import_module("modules.runtime_health")

    def fake_tags(_url: str, _timeout_seconds: float) -> dict[str, object]:
        return {"models": [{"name": "qwen2.5:7b"}]}

    monkeypatch.setattr(runtime_health, "_http_get_json", fake_tags)

    result = collect_runtime_health(check_models=True, config=_config())

    assert result.ollama_server.status == "reachable"
    assert result.primary_model.status == "ready"
    assert result.agent_model.status == "missing"


def test_provider_mode_reports_live_or_unknown_without_enabling_provider() -> None:
    live = collect_runtime_health(config=_config(provider_mode_env="local"))
    unknown = collect_runtime_health(config=_config(provider_mode_env="surprise"))

    assert live.provider_mode == "live"
    assert unknown.provider_mode == "unknown"
    assert live.fallback.status == "available"
    assert unknown.fallback.status == "available"


def test_runtime_health_status_is_json_serializable(tmp_path: Path) -> None:
    result = collect_runtime_health(config=_config(tmp_path / "missing"))

    payload = result.to_dict()

    assert payload["fallback"]["status"] == "available"
    assert json.loads(json.dumps(payload))["rag_runtime"]["status"] == "lazy_not_initialized"


def test_runtime_health_does_not_touch_detector_risk_or_decision_modules() -> None:
    code = """
import importlib
import json
import sys
importlib.import_module('modules.runtime_health').collect_runtime_health(check_chroma_path=False)
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


def _config(
    chroma_path: Path | str = "missing_chroma",
    *,
    provider_mode_env: str = "",
) -> RuntimeHealthConfig:
    return RuntimeHealthConfig(
        primary_model_name="qwen2.5:7b",
        agent_model_name="gemma4:e4b",
        chroma_path=str(chroma_path),
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        top_k=5,
        ollama_base_url="http://127.0.0.1:11434",
        provider_mode_env=provider_mode_env,
    )
