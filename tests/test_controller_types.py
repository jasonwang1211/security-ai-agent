import pytest
from pydantic import BaseModel, ValidationError

from modules.controller_types import (
    ControllerInput,
    ControllerOutput,
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    RawLogInput,
    ReportFollowupInput,
    RouterDecision,
    ToolExecutionResult,
    ToolSpec,
)


class ExampleToolOutput(BaseModel):
    message: str


def make_payload_route() -> RouterDecision:
    return RouterDecision(
        input_kind="payload_or_event",
        selected_tool="payload_triage",
        confidence="HIGH",
        reason="Looks like a known payload pattern.",
    )


def test_controller_input_accepts_valid_raw_text_and_independent_contexts() -> None:
    first = ControllerInput(raw_text="<script>alert(1)</script>")
    second = ControllerInput(raw_text="normal input")

    first.context["route_hint"] = "payload"

    assert first.raw_text == "<script>alert(1)</script>"
    assert first.context == {"route_hint": "payload"}
    assert second.context == {}


def test_controller_input_rejects_blank_raw_text() -> None:
    with pytest.raises(ValidationError):
        ControllerInput(raw_text="   ")


def test_router_decision_accepts_payload_route() -> None:
    decision = make_payload_route()

    assert decision.input_kind == "payload_or_event"
    assert decision.selected_tool == "payload_triage"
    assert decision.confidence == "HIGH"
    assert decision.requires_clarification is False


def test_router_decision_unknown_input_requires_clarification_and_no_tool() -> None:
    decision = RouterDecision(
        input_kind="unknown",
        selected_tool=None,
        confidence="LOW",
        reason="No deterministic route matched.",
        requires_clarification=True,
    )

    assert decision.requires_clarification is True
    assert decision.selected_tool is None


def test_router_decision_unknown_input_rejects_selected_tool() -> None:
    with pytest.raises(ValidationError):
        RouterDecision(
            input_kind="unknown",
            selected_tool="payload_triage",
            confidence="LOW",
            reason="No deterministic route matched.",
            requires_clarification=True,
        )


def test_router_decision_unknown_input_requires_clarification_true() -> None:
    with pytest.raises(ValidationError):
        RouterDecision(
            input_kind="unknown",
            selected_tool=None,
            confidence="LOW",
            reason="No deterministic route matched.",
            requires_clarification=False,
        )


def test_router_decision_rejects_blank_reason() -> None:
    with pytest.raises(ValidationError):
        RouterDecision(input_kind="payload_or_event", confidence="MEDIUM", reason=" ")


def test_payload_triage_input_rejects_blank_raw_text() -> None:
    with pytest.raises(ValidationError):
        PayloadTriageInput(raw_text="")


def test_raw_log_input_rejects_blank_raw_log() -> None:
    with pytest.raises(ValidationError):
        RawLogInput(raw_log="  ")


def test_log_file_input_rejects_blank_path() -> None:
    with pytest.raises(ValidationError):
        LogFileInput(path="\t")


def test_knowledge_question_input_rejects_blank_question() -> None:
    with pytest.raises(ValidationError):
        KnowledgeQuestionInput(question=" ")


def test_report_followup_input_accepts_question_and_optional_last_incident_id() -> None:
    followup = ReportFollowupInput(question="EV-003 是什麼意思？", last_incident_id="INC-001")

    assert followup.question == "EV-003 是什麼意思？"
    assert followup.last_incident_id == "INC-001"


def test_tool_execution_result_uses_independent_output_and_warning_defaults() -> None:
    first = ToolExecutionResult(status="ok")
    second = ToolExecutionResult(status="ok")

    first.output["risk"] = "HIGH"
    first.warnings.append("advisory only")

    assert first.output == {"risk": "HIGH"}
    assert first.warnings == ["advisory only"]
    assert second.output == {}
    assert second.warnings == []


def test_controller_output_accepts_valid_route() -> None:
    output = ControllerOutput(
        status="ok",
        selected_tool="payload_triage",
        response_text="Payload triage completed.",
        structured_result={"decision": "MONITOR"},
        route=make_payload_route(),
    )

    assert output.status == "ok"
    assert output.selected_tool == "payload_triage"
    assert output.structured_result == {"decision": "MONITOR"}


def test_controller_output_rejects_blank_response_text_for_ok_status() -> None:
    with pytest.raises(ValidationError):
        ControllerOutput(status="ok", response_text=" ", route=make_payload_route())


def test_tool_spec_accepts_valid_input_model_and_output_model() -> None:
    spec = ToolSpec(
        name="payload_triage",
        description="Run deterministic payload triage.",
        input_model=PayloadTriageInput,
        output_model=ExampleToolOutput,
        safety_level="safe_local_analysis",
        allowed_input_kinds=["payload_or_event"],
    )

    assert spec.name == "payload_triage"
    assert spec.input_model is PayloadTriageInput
    assert spec.output_model is ExampleToolOutput
    assert spec.deterministic is True


def test_tool_spec_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        ToolSpec(
            name=" ",
            description="Run deterministic payload triage.",
            input_model=PayloadTriageInput,
            output_model=ExampleToolOutput,
            safety_level="safe_local_analysis",
            allowed_input_kinds=["payload_or_event"],
        )


def test_tool_spec_rejects_empty_allowed_input_kinds() -> None:
    with pytest.raises(ValidationError):
        ToolSpec(
            name="payload_triage",
            description="Run deterministic payload triage.",
            input_model=PayloadTriageInput,
            output_model=ExampleToolOutput,
            safety_level="safe_local_analysis",
            allowed_input_kinds=[],
        )


def test_tool_spec_can_describe_non_deterministic_rag_tool() -> None:
    spec = ToolSpec(
        name="rag_security_qa",
        description="Answer security knowledge questions with RAG context.",
        input_model=KnowledgeQuestionInput,
        output_model=ExampleToolOutput,
        safety_level="advisory_explanation",
        requires_rag=True,
        deterministic=False,
        allowed_input_kinds=["security_knowledge_question"],
    )

    assert spec.requires_rag is True
    assert spec.deterministic is False


def test_model_serialization_for_controller_input_router_decision_and_output() -> None:
    controller_input = ControllerInput(
        raw_text="EV-003 是什麼意思？",
        context={"locale": "zh-TW"},
        last_incident_id="INC-001",
    )
    route = RouterDecision(
        input_kind="report_followup",
        selected_tool="report_followup",
        confidence="HIGH",
        reason="Question references a stable evidence ID.",
    )
    output = ControllerOutput(
        status="ok",
        selected_tool="report_followup",
        response_text="EV-003 describes the successful login after failures.",
        route=route,
    )

    assert controller_input.model_dump() == {
        "raw_text": "EV-003 是什麼意思？",
        "context": {"locale": "zh-TW"},
        "last_incident_id": "INC-001",
    }
    assert route.model_dump()["input_kind"] == "report_followup"
    assert output.model_dump()["route"]["selected_tool"] == "report_followup"
