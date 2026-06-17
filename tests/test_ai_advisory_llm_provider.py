"""Focused tests for v3.1 LLM provider abstraction."""

import importlib
import json
import subprocess
import sys

from modules.ai_advisory.llm_provider import (
    DisabledLLMProvider,
    FakeLLMProvider,
    LLMProviderRequest,
    OpenAICompatibleProvider,
    build_default_provider,
    normalize_provider_mode,
    provider_mode_from_env,
)


def request_payload() -> LLMProviderRequest:
    return LLMProviderRequest(system_prompt="system", user_prompt="user")


def test_provider_mode_defaults_to_disabled_and_fake_is_not_env_enabled() -> None:
    assert normalize_provider_mode(None) == "disabled"
    assert normalize_provider_mode("unknown") == "disabled"
    assert normalize_provider_mode("fake") == "disabled"
    assert provider_mode_from_env({}) == "disabled"
    assert provider_mode_from_env({"SENTINEL_AI_PROVIDER_MODE": "fake"}) == "disabled"


def test_build_default_provider_disabled_without_env() -> None:
    provider = build_default_provider({})
    response = provider.generate(request_payload())

    assert isinstance(provider, DisabledLLMProvider)
    assert response.mode == "disabled"
    assert response.status == "disabled"
    assert response.ok is False


def test_fake_provider_is_injection_only_and_can_return_json() -> None:
    provider = FakeLLMProvider({"hello": "world"})
    response = provider.generate(request_payload())

    assert response.mode == "fake"
    assert response.status == "success"
    assert json.loads(response.content) == {"hello": "world"}


def test_openai_compatible_missing_config_returns_failure_without_network() -> None:
    called = False

    def transport(_url: str, _headers: dict[str, str], _data: bytes, _timeout: float) -> str:
        nonlocal called
        called = True
        return "{}"

    provider = OpenAICompatibleProvider(base_url="", model="", api_key="", transport=transport)
    response = provider.generate(request_payload())

    assert response.mode == "openai_compatible"
    assert response.status == "configuration_error"
    assert called is False


def test_openai_compatible_uses_injected_transport_when_configured() -> None:
    seen: dict[str, object] = {}

    def transport(url: str, headers: dict[str, str], data: bytes, timeout: float) -> str:
        seen["url"] = url
        seen["headers"] = headers
        seen["payload"] = json.loads(data.decode("utf-8"))
        seen["timeout"] = timeout
        return json.dumps({"choices": [{"message": {"content": "{\"ok\": true}"}}]})

    provider = OpenAICompatibleProvider(
        base_url="https://example.invalid/v1",
        model="test-model",
        api_key="test-key",
        timeout_seconds=1.5,
        transport=transport,
    )
    response = provider.generate(request_payload())

    assert response.status == "success"
    assert response.content == '{"ok": true}'
    headers = seen["headers"]
    payload = seen["payload"]
    assert isinstance(headers, dict)
    assert isinstance(payload, dict)
    assert seen["url"] == "https://example.invalid/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-key"
    assert payload["model"] == "test-model"
    assert seen["timeout"] == 1.5


def test_provider_modules_do_not_import_heavy_runtime_dependencies() -> None:
    code = """
import importlib
import json
import sys

forbidden = [
    "langchain_community.chat_models",
    "modules.rag_qa",
    "chromadb",
    "sentence_transformers",
    "openai",
]
importlib.import_module("modules.ai_advisory.llm_provider")
importlib.import_module("modules.ai_advisory.full_ai_assisted")
loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]
print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True, check=False)

    assert result.returncode == 0, result.stdout + result.stderr


def test_local_provider_does_not_import_chatollama_until_call_path() -> None:
    sys.modules.pop("langchain_community.chat_models", None)
    module = importlib.import_module("modules.ai_advisory.llm_provider")

    assert hasattr(module, "LocalLLMProvider")
    assert "langchain_community.chat_models" not in sys.modules
