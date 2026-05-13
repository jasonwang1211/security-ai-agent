import pytest

from modules.controller_types import (
    KnowledgeQuestionInput,
    PayloadTriageInput,
    ToolExecutionResult,
    ToolSpec,
)
from modules.tool_registry import ToolRegistry, build_empty_registry


def make_payload_tool() -> ToolSpec:
    return ToolSpec(
        name="payload_triage",
        description="Run deterministic payload triage.",
        input_model=PayloadTriageInput,
        output_model=ToolExecutionResult,
        safety_level="safe_local_analysis",
        allowed_input_kinds=["payload_or_event"],
    )


def make_rag_tool() -> ToolSpec:
    return ToolSpec(
        name="rag_security_qa",
        description="Answer security knowledge questions with RAG context.",
        input_model=KnowledgeQuestionInput,
        output_model=ToolExecutionResult,
        safety_level="advisory_explanation",
        requires_rag=True,
        deterministic=False,
        allowed_input_kinds=["security_knowledge_question"],
    )


def test_registry_starts_empty() -> None:
    registry = ToolRegistry()

    assert len(registry) == 0
    assert registry.list_tools() == []
    assert registry.list_names() == []


def test_registry_can_register_and_retrieve_tool_spec() -> None:
    registry = ToolRegistry()
    tool = make_payload_tool()

    registry.register(tool)

    assert registry.get("payload_triage") is tool


def test_registry_has_returns_true_and_false() -> None:
    registry = ToolRegistry([make_payload_tool()])

    assert registry.has("payload_triage") is True
    assert registry.has("missing") is False


def test_registry_contains_uses_tool_names() -> None:
    registry = ToolRegistry([make_payload_tool()])

    assert "payload_triage" in registry
    assert "missing" not in registry


def test_duplicate_tool_names_raise_value_error() -> None:
    registry = ToolRegistry([make_payload_tool()])

    with pytest.raises(ValueError):
        registry.register(make_payload_tool())


def test_get_unknown_tool_raises_key_error() -> None:
    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.get("missing")


def test_list_tools_preserves_registration_order() -> None:
    payload_tool = make_payload_tool()
    rag_tool = make_rag_tool()
    registry = ToolRegistry()

    registry.register(payload_tool)
    registry.register(rag_tool)

    assert registry.list_tools() == [payload_tool, rag_tool]


def test_list_names_preserves_registration_order() -> None:
    registry = ToolRegistry([make_payload_tool(), make_rag_tool()])

    assert registry.list_names() == ["payload_triage", "rag_security_qa"]


def test_find_by_input_kind_returns_matching_tools() -> None:
    payload_tool = make_payload_tool()
    rag_tool = make_rag_tool()
    registry = ToolRegistry([payload_tool, rag_tool])

    assert registry.find_by_input_kind("payload_or_event") == [payload_tool]
    assert registry.find_by_input_kind("security_knowledge_question") == [rag_tool]


def test_find_by_input_kind_returns_empty_list_when_none_match() -> None:
    registry = ToolRegistry([make_payload_tool(), make_rag_tool()])

    assert registry.find_by_input_kind("report_followup") == []


def test_constructor_accepts_initial_tools() -> None:
    registry = ToolRegistry([make_payload_tool(), make_rag_tool()])

    assert len(registry) == 2
    assert registry.list_names() == ["payload_triage", "rag_security_qa"]


def test_constructor_rejects_duplicate_initial_tools() -> None:
    with pytest.raises(ValueError):
        ToolRegistry([make_payload_tool(), make_payload_tool()])


def test_registry_rejects_non_tool_spec_objects() -> None:
    registry = ToolRegistry()

    with pytest.raises(TypeError):
        registry.register(object())  # type: ignore[arg-type]


def test_build_empty_registry_returns_empty_tool_registry() -> None:
    registry = build_empty_registry()

    assert isinstance(registry, ToolRegistry)
    assert len(registry) == 0
