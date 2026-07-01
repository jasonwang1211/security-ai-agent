
"""Passive runtime health probe for live-provider and RAG readiness.

The default probe is intentionally lightweight: it reads config/env/path state
only. It must not start Ollama, initialize Chroma, import embedding providers, or
call ``RAGQA.is_ready()`` because those operations can initialize heavy runtime
components.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any, Literal
from urllib.error import URLError
from urllib.request import Request, urlopen

ProviderModeStatus = Literal["disabled", "live", "unknown"]
OllamaServerStatus = Literal["not_checked", "reachable", "unreachable"]
ModelStatus = Literal["not_checked", "ready", "missing", "unavailable"]
ChromaPathStatus = Literal["not_checked", "exists", "missing"]
RagRuntimeStatus = Literal["not_checked", "lazy_not_initialized", "ready", "unavailable"]
EmbeddingStatus = Literal["not_checked", "configured", "available", "unavailable"]
FallbackStatus = Literal["available", "unavailable"]

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_HOST_ENV = "OLLAMA_HOST"
PROVIDER_MODE_ENV = "SENTINEL_AI_PROVIDER_MODE"


@dataclass(frozen=True)
class RuntimeHealthConfig:
    primary_model_name: str
    agent_model_name: str
    chroma_path: str
    embedding_model_name: str
    top_k: int
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    provider_mode_env: str = ""


@dataclass(frozen=True)
class OllamaHealth:
    status: OllamaServerStatus
    endpoint: str
    checked: bool
    error: str = ""


@dataclass(frozen=True)
class ModelHealth:
    status: ModelStatus
    model_name: str
    checked: bool
    error: str = ""


@dataclass(frozen=True)
class ChromaHealth:
    status: ChromaPathStatus
    path: str
    checked: bool


@dataclass(frozen=True)
class RagHealth:
    status: RagRuntimeStatus
    checked: bool
    detail: str = ""


@dataclass(frozen=True)
class EmbeddingHealth:
    status: EmbeddingStatus
    model_name: str
    checked: bool
    detail: str = ""


@dataclass(frozen=True)
class FallbackHealth:
    status: FallbackStatus
    detail: str


@dataclass(frozen=True)
class RuntimeHealthStatus:
    provider_mode: ProviderModeStatus
    config: RuntimeHealthConfig
    ollama_server: OllamaHealth
    primary_model: ModelHealth
    agent_model: ModelHealth
    chroma_path: ChromaHealth
    rag_runtime: RagHealth
    embeddings: EmbeddingHealth
    fallback: FallbackHealth
    passive: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation for UI/debug rendering."""

        return asdict(self)


def collect_runtime_health(
    passive: bool = True,
    check_ollama: bool = False,
    check_models: bool = False,
    check_chroma_path: bool = True,
    *,
    config: RuntimeHealthConfig | None = None,
    timeout_seconds: float = 0.35,
) -> RuntimeHealthStatus:
    """Collect read-only runtime health without initializing heavy components."""

    runtime_config = config or load_runtime_health_config()
    provider_mode = _provider_mode_status(runtime_config.provider_mode_env)
    should_check_ollama = bool(check_ollama or check_models)

    ollama_health = _not_checked_ollama(runtime_config.ollama_base_url)
    model_names: set[str] | None = None
    if should_check_ollama:
        ollama_health, model_names = _probe_ollama(runtime_config.ollama_base_url, timeout_seconds)

    primary_model = _model_health(
        runtime_config.primary_model_name,
        check_models=check_models,
        ollama_health=ollama_health,
        model_names=model_names,
    )
    agent_model = _model_health(
        runtime_config.agent_model_name,
        check_models=check_models,
        ollama_health=ollama_health,
        model_names=model_names,
    )

    chroma = _chroma_health(runtime_config.chroma_path, check_chroma_path)
    embeddings = EmbeddingHealth(
        status="configured" if runtime_config.embedding_model_name else "unavailable",
        model_name=runtime_config.embedding_model_name,
        checked=False,
        detail="Configured only; passive probe does not import or initialize embeddings.",
    )
    rag_runtime = RagHealth(
        status="lazy_not_initialized" if passive else "not_checked",
        checked=False,
        detail="Passive probe does not import RAGQA, initialize Chroma, or call RAGQA.is_ready().",
    )
    fallback = FallbackHealth(
        status="available",
        detail="Provider-disabled deterministic fallback is available for Full AI and Event-Aware Q&A paths.",
    )

    return RuntimeHealthStatus(
        provider_mode=provider_mode,
        config=runtime_config,
        ollama_server=ollama_health,
        primary_model=primary_model,
        agent_model=agent_model,
        chroma_path=chroma,
        rag_runtime=rag_runtime,
        embeddings=embeddings,
        fallback=fallback,
        passive=passive,
    )


def load_runtime_health_config(env: dict[str, str] | None = None) -> RuntimeHealthConfig:
    """Load lightweight runtime settings from config.py and environment."""

    source = os.environ if env is None else env
    from config import AGENT_MODEL_NAME, CHROMA_PATH, EMBED_MODEL, MODEL_NAME, TOP_K

    return RuntimeHealthConfig(
        primary_model_name=str(MODEL_NAME or ""),
        agent_model_name=str(AGENT_MODEL_NAME or ""),
        chroma_path=str(CHROMA_PATH or ""),
        embedding_model_name=str(EMBED_MODEL or ""),
        top_k=int(TOP_K),
        ollama_base_url=_normalize_ollama_base_url(source.get(OLLAMA_HOST_ENV)),
        provider_mode_env=str(source.get(PROVIDER_MODE_ENV) or ""),
    )


def _provider_mode_status(value: str) -> ProviderModeStatus:
    text = str(value or "").strip().casefold()
    if text in {"", "disabled", "fake"}:
        return "disabled"
    if text in {"local", "openai_compatible"}:
        return "live"
    return "unknown"


def _normalize_ollama_base_url(value: str | None) -> str:
    text = str(value or "").strip() or DEFAULT_OLLAMA_BASE_URL
    if "://" not in text:
        text = "http://" + text
    return text.rstrip("/")


def _not_checked_ollama(endpoint: str) -> OllamaHealth:
    return OllamaHealth(status="not_checked", endpoint=endpoint, checked=False)


def _probe_ollama(endpoint: str, timeout_seconds: float) -> tuple[OllamaHealth, set[str] | None]:
    url = endpoint.rstrip("/") + "/api/tags"
    try:
        payload = _http_get_json(url, timeout_seconds)
    except Exception as exc:
        return (
            OllamaHealth(
                status="unreachable",
                endpoint=endpoint,
                checked=True,
                error=_safe_error_message(exc),
            ),
            None,
        )

    return (
        OllamaHealth(status="reachable", endpoint=endpoint, checked=True),
        _extract_ollama_model_names(payload),
    )


def _http_get_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    request = Request(url, method="GET")
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - localhost/manual health probe
        data = response.read()
    parsed = json.loads(data.decode("utf-8"))
    if isinstance(parsed, dict):
        return parsed
    return {}


def _extract_ollama_model_names(payload: dict[str, Any]) -> set[str]:
    models = payload.get("models", [])
    names: set[str] = set()
    if not isinstance(models, list):
        return names
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("model")
        if isinstance(name, str) and name.strip():
            names.add(name.strip())
    return names


def _model_health(
    model_name: str,
    *,
    check_models: bool,
    ollama_health: OllamaHealth,
    model_names: set[str] | None,
) -> ModelHealth:
    if not check_models:
        return ModelHealth(status="not_checked", model_name=model_name, checked=False)
    if ollama_health.status != "reachable" or model_names is None:
        return ModelHealth(
            status="unavailable",
            model_name=model_name,
            checked=True,
            error=ollama_health.error,
        )
    return ModelHealth(
        status="ready" if model_name in model_names else "missing",
        model_name=model_name,
        checked=True,
    )


def _chroma_health(path: str, check_chroma_path: bool) -> ChromaHealth:
    if not check_chroma_path:
        return ChromaHealth(status="not_checked", path=path, checked=False)
    exists = Path(path).exists()
    return ChromaHealth(status="exists" if exists else "missing", path=path, checked=True)


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, URLError) and getattr(exc, "reason", None):
        return str(exc.reason)
    return str(exc)[:200]


__all__ = [
    "ChromaHealth",
    "EmbeddingHealth",
    "FallbackHealth",
    "ModelHealth",
    "OllamaHealth",
    "RagHealth",
    "RuntimeHealthConfig",
    "RuntimeHealthStatus",
    "collect_runtime_health",
    "load_runtime_health_config",
]
