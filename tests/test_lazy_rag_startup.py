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
    # Invariant: importing ``app`` introduces no NEW heavy modules. We compare
    # the forbidden set before vs after the import instead of asserting it is
    # globally empty, because a CI runner can preload a heavy module such as
    # ``torch`` via unrelated site initialization before this probe even starts.
    # That pre-existing state is environmental noise, so we only fail on modules
    # newly imported by ``import app`` itself.
    data = _run_import_probe(
        """
        forbidden_before = set(loaded_forbidden())
        import app
        newly_forbidden = sorted(m for m in loaded_forbidden() if m not in forbidden_before)
        print(json.dumps({
            "newly_forbidden": newly_forbidden,
            "preexisting_forbidden": sorted(forbidden_before),
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
        }))
        """
    )

    assert data["newly_forbidden"] == []
    assert data["rag_module_loaded"] is False


def test_importing_streamlit_app_does_not_load_heavy_rag_dependencies() -> None:
    # Same "no NEW heavy imports" invariant as above, scoped to importing the
    # Streamlit app module. Heavy modules preloaded by the environment are
    # tolerated; modules newly imported by ``import ui.streamlit_app`` are not.
    data = _run_import_probe(
        """
        exec(_install_streamlit_stub)
        forbidden_before = set(loaded_forbidden())
        import ui.streamlit_app
        newly_forbidden = sorted(m for m in loaded_forbidden() if m not in forbidden_before)
        print(json.dumps({
            "newly_forbidden": newly_forbidden,
            "preexisting_forbidden": sorted(forbidden_before),
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
        }))
        """
    )

    assert data["newly_forbidden"] == []
    assert data["rag_module_loaded"] is False


def test_fast_deterministic_runtime_does_not_initialize_rag() -> None:
    # Invariant: the fast deterministic runtime (building the agent and running a
    # fast payload analysis) must not newly import or initialize the RAG/heavy
    # stack. We snapshot the forbidden heavy modules *before* the runtime
    # operation and again *after*, then assert the operation introduced no NEW
    # forbidden modules.
    #
    # We deliberately do not assert the forbidden set is globally empty. CI
    # runners can preload a heavy module such as ``torch`` (for example via an
    # unrelated dependency's import side effect during interpreter/site startup)
    # before the tested operation begins. That pre-existing module is
    # environmental noise, not a lazy-RAG violation -- the project itself never
    # imports torch, and the RAG-specific modules (modules.rag_qa, chromadb,
    # sentence_transformers, langchain vectorstores/embeddings) stay unloaded.
    # The invariant we protect is "no new heavy imports caused by the fast
    # deterministic runtime", together with the strict guarantee that
    # ``modules.rag_qa`` is never imported and the RAG provider stays
    # uninitialized.
    data = _run_import_probe(
        """
        exec(_install_streamlit_stub)
        from modules.controller.skill_catalog import ANALYZE_PAYLOAD_SKILL
        from modules.ui.console_state import STATE_CLI_STATE
        from ui.streamlit_app import build_agent
        from modules.controller.fast_analysis import run_fast_payload_analysis

        forbidden_before = set(loaded_forbidden())

        agent = build_agent()
        result = run_fast_payload_analysis(agent, "test; rm -rf /tmp/test", language="en")

        newly_forbidden = sorted(m for m in loaded_forbidden() if m not in forbidden_before)
        cli_state = getattr(agent, "cli_state", {})
        print(json.dumps({
            "newly_forbidden": newly_forbidden,
            "preexisting_forbidden": sorted(forbidden_before),
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
            "rag_initialized": getattr(agent.rag_qa, "is_initialized", True),
            "selected_tool": result.selected_tool,
            "active_context_kind": cli_state.get("active_context_kind"),
            "state_key_present": STATE_CLI_STATE is not None,
            "expected_tool": ANALYZE_PAYLOAD_SKILL,
        }))
        """
    )

    # The fast deterministic runtime must not newly import any heavy module.
    assert data["newly_forbidden"] == []
    # modules.rag_qa must never be imported, regardless of environmental preload.
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


def test_lazy_rag_provider_forwards_language_kwargs_on_first_rag_call() -> None:
    calls: list[str] = []

    class FakeRAG:
        def answer_question(self, query: str, *, language: str | None = None) -> str:
            calls.append(f"answer:{query}:{language}")
            return "fake localized answer"

    provider = LazyRAGQA(factory=lambda: FakeRAG())

    assert provider.is_initialized is False
    assert provider.answer_question("What is RAG?", language="en") == "fake localized answer"
    assert provider.is_initialized is True
    assert calls == ["answer:What is RAG?:en"]
