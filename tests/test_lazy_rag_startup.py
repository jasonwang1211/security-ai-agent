import json
from pathlib import Path
import subprocess
import sys
import textwrap

from modules.lazy_rag import LazyRAGQA

ROOT = Path(__file__).resolve().parents[1]

# The lazy RAG invariant is "no RAG stack import / no RAG initialization", NOT
# "no heavy module such as torch ever appears anywhere in the interpreter".
#
# These are the modules that actually constitute (or are imported by) the RAG
# runtime. If any of them is newly imported by a lightweight startup/runtime
# path -- or if ``modules.rag_qa`` is imported / ``LazyRAGQA`` is initialized --
# the lazy invariant is broken.
RAG_STACK_MODULES = (
    "modules.rag_qa",
    "chromadb",
    "sentence_transformers",
    "langchain_community.vectorstores",
    "langchain_community.embeddings",
)

# torch is heavy but is NOT a RAG-stack proxy. The project never imports torch
# directly; in CI it can be pulled in transitively by environment / third-party
# UI dependencies during an import, completely independent of the RAG stack.
# Its mere presence in ``sys.modules`` therefore does not prove RAG was loaded
# or initialized, and must not by itself fail the import-level invariant tests.
GENERAL_HEAVY_MODULES = (
    "torch",
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

        RAG_STACK_MODULES = {RAG_STACK_MODULES!r}
        GENERAL_HEAVY_MODULES = {GENERAL_HEAVY_MODULES!r}
        _install_streamlit_stub = {_install_streamlit_stub()!r}

        def _loaded(names):
            found = []
            for name in names:
                if any(module == name or module.startswith(name + ".") for module in sys.modules):
                    found.append(name)
            return sorted(found)

        def loaded_rag_stack():
            return _loaded(RAG_STACK_MODULES)

        def loaded_heavy():
            return _loaded(GENERAL_HEAVY_MODULES)

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
    # Invariant: importing ``app`` must not import the RAG stack and must not
    # initialize the RAG runtime. We compare the RAG-stack modules loaded before
    # vs after the import and assert the import introduced none of them.
    #
    # We intentionally do NOT fail on torch. In CI, ``import app`` can pull torch
    # in transitively through environment / third-party dependencies; that is a
    # heavy module appearing, not the RAG stack being loaded. torch presence is
    # reported only for diagnostics.
    data = _run_import_probe(
        """
        rag_stack_before = set(loaded_rag_stack())
        import app
        newly_rag_stack = sorted(m for m in loaded_rag_stack() if m not in rag_stack_before)
        print(json.dumps({
            "newly_rag_stack": newly_rag_stack,
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
            "heavy_present": loaded_heavy(),
        }))
        """
    )

    # No RAG-stack module may be imported by importing ``app``.
    assert data["newly_rag_stack"] == []
    # The RAG module specifically must never be imported.
    assert data["rag_module_loaded"] is False
    # data["heavy_present"] (e.g. ["torch"] in some CI environments) is
    # diagnostic only and must not, on its own, fail this invariant.


def test_importing_streamlit_app_does_not_load_heavy_rag_dependencies() -> None:
    # Same RAG-stack invariant as above, scoped to importing the Streamlit app
    # module. torch (or any general heavy module) appearing via environment /
    # third-party UI dependencies does not fail this test; only importing the
    # RAG stack or the RAG module does.
    data = _run_import_probe(
        """
        exec(_install_streamlit_stub)
        rag_stack_before = set(loaded_rag_stack())
        import ui.streamlit_app
        newly_rag_stack = sorted(m for m in loaded_rag_stack() if m not in rag_stack_before)
        print(json.dumps({
            "newly_rag_stack": newly_rag_stack,
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
            "heavy_present": loaded_heavy(),
        }))
        """
    )

    assert data["newly_rag_stack"] == []
    assert data["rag_module_loaded"] is False
    # data["heavy_present"] is diagnostic only; torch alone is not a violation.


def test_fast_deterministic_runtime_does_not_initialize_rag() -> None:
    # Invariant: the fast deterministic runtime (building the agent and running a
    # fast payload analysis) must not import the RAG stack, must not import
    # ``modules.rag_qa``, and must not initialize ``LazyRAGQA``. We snapshot the
    # relevant modules *before* the runtime operation and again *after*, then
    # assert the operation introduced no new RAG-stack (and no new heavy) module.
    #
    # The lazy RAG invariant here is "no RAG stack import / no RAG
    # initialization", not "torch never appears". CI runners can preload torch
    # (e.g. via an unrelated dependency's import side effect) before this
    # operation begins; such pre-existing modules are excluded by the
    # before/after comparison. The project itself never imports torch, so the
    # "no NEW heavy import" check below is expected to hold as well.
    data = _run_import_probe(
        """
        exec(_install_streamlit_stub)
        from modules.controller.skill_catalog import ANALYZE_PAYLOAD_SKILL
        from modules.ui.console_state import STATE_CLI_STATE
        from ui.streamlit_app import build_agent
        from modules.controller.fast_analysis import run_fast_payload_analysis

        rag_stack_before = set(loaded_rag_stack())
        heavy_before = set(loaded_heavy())

        agent = build_agent()
        result = run_fast_payload_analysis(agent, "test; rm -rf /tmp/test", language="en")

        newly_rag_stack = sorted(m for m in loaded_rag_stack() if m not in rag_stack_before)
        newly_heavy = sorted(m for m in loaded_heavy() if m not in heavy_before)
        cli_state = getattr(agent, "cli_state", {})
        print(json.dumps({
            "newly_rag_stack": newly_rag_stack,
            "newly_heavy": newly_heavy,
            "preexisting_heavy": sorted(heavy_before),
            "rag_module_loaded": "modules.rag_qa" in sys.modules,
            "rag_initialized": getattr(agent.rag_qa, "is_initialized", True),
            "selected_tool": result.selected_tool,
            "active_context_kind": cli_state.get("active_context_kind"),
            "state_key_present": STATE_CLI_STATE is not None,
            "expected_tool": ANALYZE_PAYLOAD_SKILL,
        }))
        """
    )

    # Strict lazy-RAG invariant: no RAG-stack module is newly imported, the RAG
    # module is never imported, and the RAG provider is never initialized.
    assert data["newly_rag_stack"] == []
    assert data["rag_module_loaded"] is False
    assert data["rag_initialized"] is False
    # The fast deterministic runtime must not newly import torch either. We check
    # only NEWLY imported torch (pre-existing/preloaded torch is excluded above),
    # so CI environments that preload torch do not break this assertion.
    assert data["newly_heavy"] == []
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
