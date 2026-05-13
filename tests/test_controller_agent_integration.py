from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from modules.controller_agent import ControllerAgent, build_default_route_map
from modules.controller_types import (
    IncidentJsonExportInput,
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    RawLogInput,
    ReportFollowupInput,
    ToolExecutionResult,
)
from modules.skill_catalog import (
    INCIDENT_JSON_EXPORT,
    LOG_FILE_INGEST,
    PAYLOAD_TRIAGE,
    RAG_SECURITY_QA,
    RAW_LOG_TRANSLATE,
    REPORT_FOLLOWUP,
    build_v1_5_registry,
)
from modules.skill_wrappers import (
    run_incident_json_export_skill,
    run_log_file_ingest_skill,
    run_payload_triage_skill,
    run_rag_security_qa_skill,
    run_raw_log_translate_skill,
    run_report_followup_skill,
)

Handler = Callable[[BaseModel], ToolExecutionResult]

EXPECTED_SKILLS = [
    PAYLOAD_TRIAGE,
    RAW_LOG_TRANSLATE,
    LOG_FILE_INGEST,
    RAG_SECURITY_QA,
    REPORT_FOLLOWUP,
    INCIDENT_JSON_EXPORT,
]


class FakeIntegrationAgent:
    def __init__(self) -> None:
        self.cli_state = {
            "last_question": "What happened in INC-001?",
            "last_answer": "INC-001 involved suspicious web input.",
            "last_points": ["EV-001"],
            "last_focus": "INC-001",
        }

    def handle_query(self, query: str, state: dict[str, Any]) -> str:
        if "詳細" in query:
            return "follow-up answer"
        return "payload triage done"

    def handle_knowledge_query(self, question: str, state: dict[str, Any]) -> str:
        return "rag answer"


def build_test_handlers(fake_agent: FakeIntegrationAgent) -> dict[str, Handler]:
    def payload_handler(input_data: BaseModel) -> ToolExecutionResult:
        assert isinstance(input_data, PayloadTriageInput)
        return run_payload_triage_skill(input_data, fake_agent)

    def raw_log_handler(input_data: BaseModel) -> ToolExecutionResult:
        assert isinstance(input_data, RawLogInput)
        return run_raw_log_translate_skill(input_data)

    def log_file_handler(input_data: BaseModel) -> ToolExecutionResult:
        assert isinstance(input_data, LogFileInput)
        return run_log_file_ingest_skill(input_data)

    def rag_handler(input_data: BaseModel) -> ToolExecutionResult:
        assert isinstance(input_data, KnowledgeQuestionInput)
        return run_rag_security_qa_skill(input_data, fake_agent)

    def report_followup_handler(input_data: BaseModel) -> ToolExecutionResult:
        assert isinstance(input_data, ReportFollowupInput)
        return run_report_followup_skill(input_data, fake_agent)

    def incident_export_handler(input_data: BaseModel) -> ToolExecutionResult:
        assert isinstance(input_data, IncidentJsonExportInput)
        return run_incident_json_export_skill(input_data)

    return {
        PAYLOAD_TRIAGE: payload_handler,
        RAW_LOG_TRANSLATE: raw_log_handler,
        LOG_FILE_INGEST: log_file_handler,
        RAG_SECURITY_QA: rag_handler,
        REPORT_FOLLOWUP: report_followup_handler,
        INCIDENT_JSON_EXPORT: incident_export_handler,
    }


def make_agent() -> ControllerAgent:
    return ControllerAgent(
        registry=build_v1_5_registry(),
        handlers=build_test_handlers(FakeIntegrationAgent()),
        route_map=build_default_route_map(),
    )


def test_controller_agent_constructs_with_v1_5_registry_and_six_handlers() -> None:
    registry = build_v1_5_registry()
    handlers = build_test_handlers(FakeIntegrationAgent())
    agent = ControllerAgent(registry, handlers, build_default_route_map())

    assert len(registry) == 6
    assert set(handlers) == set(EXPECTED_SKILLS)
    assert all(agent.can_handle(skill_name) for skill_name in EXPECTED_SKILLS)


def test_available_tools_returns_exactly_six_v1_5_skills() -> None:
    assert make_agent().available_tools() == EXPECTED_SKILLS


def test_all_registered_tool_specs_have_matching_integration_handlers() -> None:
    registry = build_v1_5_registry()
    handlers = build_test_handlers(FakeIntegrationAgent())

    assert set(registry.list_names()) == set(handlers)


def test_dispatch_route_payload_triage_succeeds() -> None:
    output = make_agent().dispatch_route(
        PAYLOAD_TRIAGE,
        {"raw_text": "<script>alert(1)</script>"},
    )

    assert output.status == "ok"
    assert output.selected_tool == PAYLOAD_TRIAGE
    assert output.response_text == "payload triage done"


def test_dispatch_route_mode_1_maps_to_payload_triage() -> None:
    output = make_agent().dispatch_route(
        "mode_1",
        {"raw_text": "<script>alert(1)</script>"},
    )

    assert output.status == "ok"
    assert output.selected_tool == PAYLOAD_TRIAGE


def test_dispatch_route_raw_log_translate_succeeds() -> None:
    output = make_agent().dispatch_route(
        RAW_LOG_TRANSLATE,
        {
            "raw_log": (
                "2026-05-14T08:30:00Z login_failed "
                "src_ip=203.0.113.10 user=alice endpoint=/login status=401"
            )
        },
    )

    assert output.status == "ok"
    assert output.selected_tool == RAW_LOG_TRANSLATE
    assert output.structured_result["output"]["normalized_event_type"] == "auth_failure"


def test_dispatch_route_log_file_ingest_missing_file_is_graceful() -> None:
    output = make_agent().dispatch_route(LOG_FILE_INGEST, {"path": "missing.log"})

    assert output.status in {"ok", "error", "clarification_required"}
    assert output.selected_tool == LOG_FILE_INGEST
    assert output.response_text


def test_dispatch_route_rag_security_qa_succeeds_with_fake_agent() -> None:
    output = make_agent().dispatch_route(RAG_SECURITY_QA, {"question": "XSS 是什麼？"})

    assert output.status == "ok"
    assert output.selected_tool == RAG_SECURITY_QA
    assert output.response_text == "rag answer"


def test_dispatch_route_mode_3_maps_to_rag_security_qa() -> None:
    output = make_agent().dispatch_route("mode_3", {"question": "XSS 是什麼？"})

    assert output.status == "ok"
    assert output.selected_tool == RAG_SECURITY_QA


def test_dispatch_route_report_followup_succeeds_with_fake_context() -> None:
    output = make_agent().dispatch_route(REPORT_FOLLOWUP, {"question": "詳細說明"})

    assert output.status == "ok"
    assert output.selected_tool == REPORT_FOLLOWUP
    assert output.response_text == "follow-up answer"


def test_dispatch_route_mode_4_maps_to_report_followup() -> None:
    output = make_agent().dispatch_route("mode_4", {"question": "詳細說明"})

    assert output.status == "ok"
    assert output.selected_tool == REPORT_FOLLOWUP


def test_dispatch_route_incident_json_export_with_incident_succeeds() -> None:
    output = make_agent().dispatch_route(
        INCIDENT_JSON_EXPORT,
        {"incident": {"id": "INC-001"}},
    )

    assert output.status == "ok"
    assert output.selected_tool == INCIDENT_JSON_EXPORT
    assert output.structured_result["output"]["incident"] == {"id": "INC-001"}


def test_dispatch_route_incident_json_export_with_id_requires_clarification() -> None:
    output = make_agent().dispatch_route(
        INCIDENT_JSON_EXPORT,
        {"incident_id": "INC-001"},
    )

    assert output.status == "clarification_required"
    assert output.selected_tool == INCIDENT_JSON_EXPORT
    assert "not implemented" in output.response_text


def test_unknown_route_returns_clarification_controller_output() -> None:
    output = make_agent().dispatch_route("unknown_route", {"raw_text": "payload"})

    assert output.status == "clarification_required"
    assert output.selected_tool is None
    assert output.route.requires_clarification is True


def test_invalid_payload_for_route_returns_error_controller_output() -> None:
    output = make_agent().dispatch_route(PAYLOAD_TRIAGE, {"raw_text": "   "})

    assert output.status == "error"
    assert output.selected_tool == PAYLOAD_TRIAGE
    assert output.structured_result["error_message"] == "Tool input validation failed."


def test_successful_dispatches_set_selected_tool() -> None:
    agent = make_agent()
    cases: list[tuple[str, dict[str, Any], str]] = [
        (PAYLOAD_TRIAGE, {"raw_text": "<script>alert(1)</script>"}, PAYLOAD_TRIAGE),
        (
            RAW_LOG_TRANSLATE,
            {
                "raw_log": (
                    "2026-05-14T08:30:00Z login_failed "
                    "src_ip=203.0.113.10 user=alice endpoint=/login status=401"
                )
            },
            RAW_LOG_TRANSLATE,
        ),
        (RAG_SECURITY_QA, {"question": "XSS 是什麼？"}, RAG_SECURITY_QA),
        (REPORT_FOLLOWUP, {"question": "詳細說明"}, REPORT_FOLLOWUP),
        (INCIDENT_JSON_EXPORT, {"incident": {"id": "INC-001"}}, INCIDENT_JSON_EXPORT),
    ]

    for route, payload, expected_tool in cases:
        output = agent.dispatch_route(route, payload)
        assert output.status == "ok"
        assert output.selected_tool == expected_tool


def test_controller_does_not_override_deterministic_final_decision() -> None:
    def payload_decision_handler(input_data: BaseModel) -> ToolExecutionResult:
        assert isinstance(input_data, PayloadTriageInput)
        return ToolExecutionResult(
            status="ok",
            output={"text": "payload done", "decision": "MONITOR"},
        )

    handlers = build_test_handlers(FakeIntegrationAgent())
    handlers[PAYLOAD_TRIAGE] = payload_decision_handler
    agent = ControllerAgent(build_v1_5_registry(), handlers, build_default_route_map())

    output = agent.dispatch_route(PAYLOAD_TRIAGE, {"raw_text": "<script>alert(1)</script>"})

    assert output.status == "ok"
    assert output.selected_tool == PAYLOAD_TRIAGE
    assert output.structured_result["output"]["decision"] == "MONITOR"


def test_no_auto_route_or_smart_router_route_is_present() -> None:
    route_map = build_default_route_map()

    assert "auto_route" not in route_map
    assert "smart_router" not in route_map


def test_no_deferred_skills_are_registered() -> None:
    registry = build_v1_5_registry()

    assert "rule_explainer" not in registry
    assert "investigation_planner" not in registry
