import json
from pathlib import Path
import subprocess
import sys
import textwrap

from modules.lazy_rag import LazyRAGQA

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_HEAVY_MODULES = (
    "chromadb",
    "sentence_transformers",
    "torch",
    "langchain_community.vectorstores",
    "langchain_community.embeddings",
)


def _install_streamlit_stub() -> str:
    return """
import types
streamlit = types.ModuleType('streamlit')
streamlit.session_state = {}
components = types.ModuleType('streamlit.components')
components_v1 = types.ModuleType('streamlit.components.v1')
streamlit.components = components
components.v1 = components_v1
sys.modules['streamlit'] = streamlit
sys.modules['streamlit.components'] = components
sys.modules['streamlit.components.v1'] = components_v1
"""


def _run_import_probe(code: str) -> dict[str, object]:
    probe = textwrap.dedent(
        f"""
        import json
        import sys

        FORBIDDEN = {FORBIDDEN_HEAVY_MODULES!r}
        _install_streamlit_stub = {_install_streamlit_stub()!r}

        def loaded_forbidden():
            loaded = []
            for name in FORBIDDEN:
                if any(module == name or module.startswith(name + ".") for module in sys.modules):
                    loaded.append(name)
            return loaded

        {textwrap.indent(textwrap.dedent(code), "        ")}
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_importing_app_does_not_load_heavy_rag_dependencies() -> None:
    data = _run_import_probe(
        """
        import app
        print(json.dumps({
            "forbidden": loaded_forbidden(),
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
        }))
        """
    )

    assert data == {"forbidden": [], "rag_module_loaded": False}


def test_importing_streamlit_app_does_not_load_heavy_rag_dependencies() -> None:
    data = _run_import_probe(
        """
        exec(_install_streamlit_stub)
        import ui.streamlit_app
        print(json.dumps({
            "forbidden": loaded_forbidden(),
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
        }))
        """
    )

    assert data == {"forbidden": [], "rag_module_loaded": False}


def test_fast_deterministic_runtime_does_not_initialize_rag() -> None:
    data = _run_import_probe(
        """
        exec(_install_streamlit_stub)
        from modules.controller.skill_catalog import ANALYZE_PAYLOAD_SKILL
        from modules.ui.console_state import STATE_CLI_STATE
        from ui.streamlit_app import build_agent
        from modules.controller.fast_analysis import run_fast_payload_analysis

        agent = build_agent()
        result = run_fast_payload_analysis(agent, "test; rm -rf /tmp/test", language="en")
        cli_state = getattr(agent, "cli_state", {})
        print(json.dumps({
            "forbidden": loaded_forbidden(),
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
            "rag_initialized": getattr(agent.rag_qa, "is_initialized", True),
            "selected_tool": result.selected_tool,
            "active_context_kind": cli_state.get("active_context_kind"),
            "state_key_present": STATE_CLI_STATE is not None,
            "expected_tool": ANALYZE_PAYLOAD_SKILL,
        }))
        """
    )

    assert data["forbidden"] == []
    assert data["rag_module_loaded"] is False
    assert data["rag_initialized"] is False
    assert data["selected_tool"] == data["expected_tool"]
    assert data["active_context_kind"] == "event"
    assert data["state_key_present"] is True


def test_lazy_rag_provider_constructs_real_runtime_on_first_rag_call() -> None:
    calls: list[str] = []

    class FakeRAG:
        def is_ready(self) -> bool:
            calls.append("is_ready")
            return True

        def answer_question(self, query: str) -> str:
            calls.append(f"answer:{query}")
            return "fake answer"

    provider = LazyRAGQA(factory=lambda: FakeRAG())

    assert provider.is_initialized is False
    assert calls == []
    assert provider.answer_question("What is RAG?") == "fake answer"
    assert provider.is_initialized is True
    assert calls == ["answer:What is RAG?"]
    assert provider.is_ready() is True
    assert calls == ["answer:What is RAG?", "is_ready"]
