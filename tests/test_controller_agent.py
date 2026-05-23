from typing import cast

from pydantic import BaseModel

from modules.controller.agent import ControllerAgent, build_default_route_map
from modules.controller.types import (
    KnowledgeQuestionInput,
    PayloadTriageInput,
    ToolExecutionResult,
    ToolSpec,
)
from modules.controller.skill_catalog import (
    INCIDENT_JSON_EXPORT,
    LOG_FILE_INGEST,
    PAYLOAD_TRIAGE,
    RAG_SECURITY_QA,
    RAW_LOG_TRANSLATE,
    REPORT_FOLLOWUP,
    build_v1_5_registry,
)
from modules.controller.registry import ToolRegistry


def payload_handler(input_data: BaseModel) -> ToolExecutionResult:
    assert isinstance(input_data, PayloadTriageInput)
    return ToolExecutionResult(
        status="ok",
        output={"text": "payload done", "decision": "MONITOR"},
    )


def rag_handler(input_data: BaseModel) -> ToolExecutionResult:
    assert isinstance(input_data, KnowledgeQuestionInput)
    return ToolExecutionResult(status="ok", output={"text": "rag answer"})


def error_handler(input_data: BaseModel) -> ToolExecutionResult:
    raise RuntimeError("boom")


def clarification_handler(input_data: BaseModel) -> ToolExecutionResult:
    return ToolExecutionResult(
        status="clarification_required",
        output={"text": "need more detail", "reason": "missing context"},
        warnings=["missing context"],
    )


def invalid_output_handler(input_data: BaseModel) -> ToolExecutionResult:
    return cast(ToolExecutionResult, {"output": {"text": "missing status"}})


def make_agent() -> ControllerAgent:
    return ControllerAgent(
        registry=build_v1_5_registry(),
        handlers={
            PAYLOAD_TRIAGE: payload_handler,
            RAG_SECURITY_QA: rag_handler,
        },
        route_map={PAYLOAD_TRIAGE: PAYLOAD_TRIAGE, "ask_rag": RAG_SECURITY_QA},
    )


def test_available_tools_returns_registry_names() -> None:
    agent = make_agent()

    assert agent.available_tools() == [
        PAYLOAD_TRIAGE,
        RAW_LOG_TRANSLATE,
        LOG_FILE_INGEST,
        RAG_SECURITY_QA,
        REPORT_FOLLOWUP,
        INCIDENT_JSON_EXPORT,
    ]


def test_can_handle_requires_registry_tool_and_handler() -> None:
    agent = make_agent()

    assert agent.can_handle(PAYLOAD_TRIAGE) is True
    assert agent.can_handle(LOG_FILE_INGEST) is False
    assert agent.can_handle("missing") is False


def test_dispatch_tool_validates_payload_and_calls_handler() -> None:
    output = make_agent().dispatch_tool(PAYLOAD_TRIAGE, {"raw_text": "suspicious payload"})

    assert output.status == "ok"
    assert output.structured_result["output"]["decision"] == "MONITOR"


def test_dispatch_tool_returns_controller_output() -> None:
    output = make_agent().dispatch_tool(PAYLOAD_TRIAGE, {"raw_text": "suspicious payload"})

    assert output.selected_tool == PAYLOAD_TRIAGE
    assert output.route.selected_tool == PAYLOAD_TRIAGE
    assert output.route.confidence == "HIGH"
    assert output.route.reason == "deterministic route/tool dispatch"


def test_dispatch_tool_response_text_uses_output_text() -> None:
    output = make_agent().dispatch_tool(PAYLOAD_TRIAGE, {"raw_text": "suspicious payload"})

    assert output.response_text == "payload done"


def test_dispatch_tool_rejects_unknown_tool_gracefully() -> None:
    output = make_agent().dispatch_tool("unknown_tool", {"raw_text": "payload"})

    assert output.status == "error"
    assert output.selected_tool is None
    assert output.route.requires_clarification is True
    assert "Unknown tool" in output.structured_result["error_message"]


def test_dispatch_tool_handles_missing_handler_gracefully() -> None:
    output = make_agent().dispatch_tool(LOG_FILE_INGEST, {"path": "events.log"})

    assert output.status == "error"
    assert output.selected_tool == LOG_FILE_INGEST
    assert "No handler registered" in output.structured_result["error_message"]


def test_dispatch_tool_handles_invalid_payload_gracefully() -> None:
    output = make_agent().dispatch_tool(PAYLOAD_TRIAGE, {"raw_text": "   "})

    assert output.status == "error"
    assert output.selected_tool == PAYLOAD_TRIAGE
    assert output.structured_result["error_message"] == "Tool input validation failed."
    assert "validation_error" in output.structured_result


def test_dispatch_tool_wraps_handler_exception_as_error_output() -> None:
    registry = build_v1_5_registry()
    agent = ControllerAgent(registry, {PAYLOAD_TRIAGE: error_handler})

    output = agent.dispatch_tool(PAYLOAD_TRIAGE, {"raw_text": "payload"})

    assert output.status == "error"
    assert output.response_text == "boom"
    assert output.warnings == [f"{PAYLOAD_TRIAGE} handler failed"]


def test_dispatch_route_uses_route_map() -> None:
    output = make_agent().dispatch_route("ask_rag", {"question": "What is phishing?"})

    assert output.status == "ok"
    assert output.selected_tool == RAG_SECURITY_QA
    assert output.response_text == "rag answer"


def test_dispatch_route_rejects_unknown_route_gracefully() -> None:
    output = make_agent().dispatch_route("auto_route", {"raw_text": "payload"})

    assert output.status == "clarification_required"
    assert output.selected_tool is None
    assert output.route.input_kind == "unknown"
    assert output.route.requires_clarification is True


def test_build_default_route_map_contains_six_skill_routes() -> None:
    route_map = build_default_route_map()

    assert route_map[PAYLOAD_TRIAGE] == PAYLOAD_TRIAGE
    assert route_map[RAW_LOG_TRANSLATE] == RAW_LOG_TRANSLATE
    assert route_map[LOG_FILE_INGEST] == LOG_FILE_INGEST
    assert route_map[RAG_SECURITY_QA] == RAG_SECURITY_QA
    assert route_map[REPORT_FOLLOWUP] == REPORT_FOLLOWUP
    assert route_map[INCIDENT_JSON_EXPORT] == INCIDENT_JSON_EXPORT


def test_default_route_map_includes_mode_1_payload_triage_hint() -> None:
    assert build_default_route_map()["mode_1"] == PAYLOAD_TRIAGE


def test_output_model_validation_is_applied() -> None:
    registry = ToolRegistry(
        [
            ToolSpec(
                name=PAYLOAD_TRIAGE,
                description="Run deterministic payload triage.",
                input_model=PayloadTriageInput,
                output_model=ToolExecutionResult,
                safety_level="safe_local_analysis",
                allowed_input_kinds=["payload_or_event"],
            )
        ]
    )
    agent = ControllerAgent(registry, {PAYLOAD_TRIAGE: invalid_output_handler})

    output = agent.dispatch_tool(PAYLOAD_TRIAGE, {"raw_text": "payload"})

    assert output.status == "error"
    assert output.structured_result["error_message"] == "Tool output validation failed."
    assert "validation_error" in output.structured_result


def test_controller_agent_does_not_override_deterministic_result_fields() -> None:
    registry = build_v1_5_registry()
    agent = ControllerAgent(registry, {PAYLOAD_TRIAGE: clarification_handler})

    output = agent.dispatch_tool(PAYLOAD_TRIAGE, {"raw_text": "payload"})

    assert output.status == "clarification_required"
    assert output.response_text == "need more detail"
    assert output.structured_result["status"] == "clarification_required"
    assert output.structured_result["warnings"] == ["missing context"]


def test_controller_agent_construction_does_not_require_rag_llm_chroma_or_ollama() -> None:
    registry = ToolRegistry(
        [
            ToolSpec(
                name=RAG_SECURITY_QA,
                description="Fake RAG tool spec with no real backend.",
                input_model=KnowledgeQuestionInput,
                output_model=ToolExecutionResult,
                safety_level="advisory_explanation",
                requires_llm=True,
                requires_rag=True,
                deterministic=False,
                allowed_input_kinds=["security_knowledge_question"],
            )
        ]
    )
    agent = ControllerAgent(registry, {RAG_SECURITY_QA: rag_handler})

    output = agent.dispatch_tool(RAG_SECURITY_QA, {"question": "What is phishing?"})

    assert output.status == "ok"
    assert output.response_text == "rag answer"


def test_controller_agent_shim_reexports_canonical_symbol() -> None:
    from modules.controller_agent import ControllerAgent as ShimControllerAgent

    assert ShimControllerAgent is ControllerAgent
