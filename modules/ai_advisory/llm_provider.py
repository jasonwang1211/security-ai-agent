"""Provider abstraction for v3.1 full AI-assisted advisory generation.

Providers return raw model text only. They never own risk, decision, retrieval,
graph, case memory, or enforcement behavior. The caller must validate and
guardrail the returned text before using it.
"""

from __future__ import annotations

import importlib
import json
import os
from collections.abc import Callable, Mapping
from typing import Any, Literal
from urllib import error, request

from pydantic import BaseModel, Field

ProviderMode = Literal["disabled", "fake", "local", "openai_compatible"]
ProviderStatus = Literal["success", "disabled", "configuration_error", "unavailable", "error"]

DEFAULT_PROVIDER_MODE: ProviderMode = "disabled"
PROVIDER_MODE_ENV = "SENTINEL_AI_PROVIDER_MODE"
LOCAL_MODEL_ENV = "SENTINEL_LOCAL_LLM_MODEL"
OPENAI_COMPATIBLE_BASE_URL_ENV = "SENTINEL_OPENAI_COMPATIBLE_BASE_URL"
OPENAI_COMPATIBLE_MODEL_ENV = "SENTINEL_OPENAI_COMPATIBLE_MODEL"
OPENAI_COMPATIBLE_API_KEY_ENV = "SENTINEL_OPENAI_COMPATIBLE_API_KEY"


class LLMProviderRequest(BaseModel):
    """Prompt payload passed to provider adapters."""

    system_prompt: str
    user_prompt: str
    temperature: float = 0.0


class LLMProviderResponse(BaseModel):
    """Normalized provider response; failures are data, not exceptions."""

    mode: ProviderMode
    status: ProviderStatus
    content: str = ""
    error_message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "success" and bool(self.content.strip())


class BaseLLMProvider:
    """Small callable provider interface used by backend contracts."""

    mode: ProviderMode

    def generate(self, request_payload: LLMProviderRequest) -> LLMProviderResponse:
        raise NotImplementedError


class DisabledLLMProvider(BaseLLMProvider):
    mode: ProviderMode = "disabled"

    def generate(self, request_payload: LLMProviderRequest) -> LLMProviderResponse:
        del request_payload
        return LLMProviderResponse(
            mode=self.mode,
            status="disabled",
            error_message="AI provider is disabled.",
        )


class FakeLLMProvider(BaseLLMProvider):
    """Injection-only provider for deterministic tests."""

    mode: ProviderMode = "fake"

    def __init__(self, content: str | dict[str, Any] = "", *, status: ProviderStatus = "success") -> None:
        self.content = json.dumps(content) if isinstance(content, dict) else str(content or "")
        self.status = status

    def generate(self, request_payload: LLMProviderRequest) -> LLMProviderResponse:
        del request_payload
        if self.status != "success":
            return LLMProviderResponse(
                mode=self.mode,
                status=self.status,
                error_message=f"Fake provider returned {self.status}.",
            )
        return LLMProviderResponse(mode=self.mode, status="success", content=self.content)


class LocalLLMProvider(BaseLLMProvider):
    """Optional local provider using ChatOllama lazily inside the call path."""

    mode: ProviderMode = "local"

    def __init__(self, model_name: str) -> None:
        self.model_name = str(model_name or "").strip()

    def generate(self, request_payload: LLMProviderRequest) -> LLMProviderResponse:
        if not self.model_name:
            return LLMProviderResponse(
                mode=self.mode,
                status="configuration_error",
                error_message="Local provider requires a model name.",
            )
        try:
            chat_models: Any = importlib.import_module("langchain_community.chat_models")
            chat_ollama: Any = chat_models.ChatOllama
            llm = chat_ollama(model=self.model_name, temperature=request_payload.temperature)
            response = llm.invoke(
                f"{request_payload.system_prompt}\n\n{request_payload.user_prompt}"
            )
            content = str(getattr(response, "content", "") or "").strip()
        except Exception as exc:
            return LLMProviderResponse(
                mode=self.mode,
                status="unavailable",
                error_message=str(exc),
            )
        return LLMProviderResponse(mode=self.mode, status="success", content=content)


Transport = Callable[[str, dict[str, str], bytes, float], str]


class OpenAICompatibleProvider(BaseLLMProvider):
    """Optional OpenAI-compatible chat-completions provider using stdlib HTTP."""

    mode: ProviderMode = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        timeout_seconds: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = str(base_url or "").strip().rstrip("/")
        self.model = str(model or "").strip()
        self.api_key = str(api_key or "").strip()
        self.timeout_seconds = timeout_seconds
        self.transport = transport or _default_transport

    def generate(self, request_payload: LLMProviderRequest) -> LLMProviderResponse:
        missing = [
            name
            for name, value in (
                ("base_url", self.base_url),
                ("model", self.model),
                ("api_key", self.api_key),
            )
            if not value
        ]
        if missing:
            return LLMProviderResponse(
                mode=self.mode,
                status="configuration_error",
                error_message=f"OpenAI-compatible provider missing: {', '.join(missing)}.",
            )

        endpoint = _chat_completions_endpoint(self.base_url)
        payload = {
            "model": self.model,
            "temperature": request_payload.temperature,
            "messages": [
                {"role": "system", "content": request_payload.system_prompt},
                {"role": "user", "content": request_payload.user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            raw = self.transport(
                endpoint,
                headers,
                json.dumps(payload).encode("utf-8"),
                self.timeout_seconds,
            )
            content = _extract_openai_compatible_content(raw)
        except Exception as exc:
            return LLMProviderResponse(
                mode=self.mode,
                status="unavailable",
                error_message=str(exc),
            )
        return LLMProviderResponse(mode=self.mode, status="success", content=content)


def normalize_provider_mode(value: str | None) -> ProviderMode:
    """Normalize runtime provider mode; fake is not enabled from env."""

    text = str(value or "").strip().casefold()
    if text in {"local", "openai_compatible"}:
        return text  # type: ignore[return-value]
    return DEFAULT_PROVIDER_MODE


def provider_mode_from_env(env: Mapping[str, str] | None = None) -> ProviderMode:
    source = os.environ if env is None else env
    return normalize_provider_mode(source.get(PROVIDER_MODE_ENV))


def build_default_provider(env: Mapping[str, str] | None = None) -> BaseLLMProvider:
    source = os.environ if env is None else env
    mode = provider_mode_from_env(source)
    if mode == "local":
        return LocalLLMProvider(
            source.get(LOCAL_MODEL_ENV) or _default_local_model_name()
        )
    if mode == "openai_compatible":
        return OpenAICompatibleProvider(
            base_url=source.get(OPENAI_COMPATIBLE_BASE_URL_ENV, ""),
            model=source.get(OPENAI_COMPATIBLE_MODEL_ENV, ""),
            api_key=source.get(OPENAI_COMPATIBLE_API_KEY_ENV, ""),
        )
    return DisabledLLMProvider()


def _default_local_model_name() -> str:
    try:
        from config import AGENT_MODEL_NAME

        return str(AGENT_MODEL_NAME or "")
    except Exception:
        return ""


def _chat_completions_endpoint(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def _extract_openai_compatible_content(raw: str) -> str:
    parsed = json.loads(raw)
    choices = parsed.get("choices") if isinstance(parsed, dict) else None
    if not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        return ""
    return str(message.get("content") or "").strip()


def _default_transport(url: str, headers: dict[str, str], data: bytes, timeout: float) -> str:
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except error.URLError as exc:
        raise RuntimeError(str(exc)) from exc


__all__ = [
    "BaseLLMProvider",
    "DEFAULT_PROVIDER_MODE",
    "DisabledLLMProvider",
    "FakeLLMProvider",
    "LLMProviderRequest",
    "LLMProviderResponse",
    "LocalLLMProvider",
    "OpenAICompatibleProvider",
    "ProviderMode",
    "ProviderStatus",
    "build_default_provider",
    "normalize_provider_mode",
    "provider_mode_from_env",
]
