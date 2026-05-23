import pytest
from pydantic import ValidationError

from modules.controller.registry import ToolRegistry
from modules.controller.skill_catalog import (
    INCIDENT_JSON_EXPORT,
    LOG_FILE_INGEST,
    PAYLOAD_TRIAGE,
    RAG_SECURITY_QA,
    RAW_LOG_TRANSLATE,
    REPORT_FOLLOWUP,
    build_v1_5_registry,
    build_v1_5_tool_specs,
)
from modules.controller.types import IncidentJsonExportInput

EXPECTED_SKILL_NAMES = [
    PAYLOAD_TRIAGE,
    RAW_LOG_TRANSLATE,
    LOG_FILE_INGEST,
    RAG_SECURITY_QA,
    REPORT_FOLLOWUP,
    INCIDENT_JSON_EXPORT,
]

DEFERRED_SKILL_NAMES = {
    "rule_explainer",
    "investigation_planner",
    "smart_router",
    "auto_route",
}


def spec_by_name(name: str):
    return {spec.name: spec for spec in build_v1_5_tool_specs()}[name]


def test_build_v1_5_tool_specs_returns_exactly_six_specs() -> None:
    assert len(build_v1_5_tool_specs()) == 6


def test_skill_names_are_deterministic_and_in_expected_order() -> None:
    assert [spec.name for spec in build_v1_5_tool_specs()] == EXPECTED_SKILL_NAMES


def test_all_six_specs_are_unique() -> None:
    names = [spec.name for spec in build_v1_5_tool_specs()]

    assert len(set(names)) == 6


def test_build_v1_5_registry_returns_registry_with_six_tools() -> None:
    registry = build_v1_5_registry()

    assert isinstance(registry, ToolRegistry)
    assert len(registry) == 6


def test_registry_can_retrieve_payload_triage() -> None:
    registry = build_v1_5_registry()

    assert registry.get(PAYLOAD_TRIAGE).name == PAYLOAD_TRIAGE


def test_registry_can_retrieve_rag_security_qa() -> None:
    registry = build_v1_5_registry()

    assert registry.get(RAG_SECURITY_QA).name == RAG_SECURITY_QA


def test_no_deferred_skills_are_present() -> None:
    names = set(build_v1_5_registry().list_names())

    assert names.isdisjoint(DEFERRED_SKILL_NAMES)


def test_payload_triage_tool_spec_has_expected_flags() -> None:
    spec = spec_by_name(PAYLOAD_TRIAGE)

    assert spec.deterministic is True
    assert spec.requires_llm is False
    assert spec.requires_rag is False
    assert spec.safety_level == "safe_local_analysis"
    assert spec.allowed_input_kinds == ["payload_or_event"]


def test_rag_security_qa_tool_spec_requires_rag_and_llm() -> None:
    spec = spec_by_name(RAG_SECURITY_QA)

    assert spec.requires_rag is True
    assert spec.requires_llm is True
    assert spec.deterministic is False
    assert spec.safety_level == "advisory_explanation"


def test_incident_json_export_tool_spec_has_export_only_safety_level() -> None:
    spec = spec_by_name(INCIDENT_JSON_EXPORT)

    assert spec.safety_level == "export_only"
    assert spec.deterministic is True
    assert spec.requires_llm is False
    assert spec.requires_rag is False


def test_find_by_input_kind_payload_returns_payload_triage() -> None:
    registry = build_v1_5_registry()

    assert [tool.name for tool in registry.find_by_input_kind("payload_or_event")] == [
        PAYLOAD_TRIAGE
    ]


def test_find_by_input_kind_security_question_returns_rag_security_qa() -> None:
    registry = build_v1_5_registry()

    assert [tool.name for tool in registry.find_by_input_kind("security_knowledge_question")] == [
        RAG_SECURITY_QA
    ]


def test_incident_json_export_input_accepts_incident_id() -> None:
    export_input = IncidentJsonExportInput(incident_id="INC-001")

    assert export_input.incident_id == "INC-001"
    assert export_input.incident == {}


def test_incident_json_export_input_accepts_incident_dict() -> None:
    export_input = IncidentJsonExportInput(incident={"id": "INC-001", "risk_level": "HIGH"})

    assert export_input.incident == {"id": "INC-001", "risk_level": "HIGH"}


def test_incident_json_export_input_rejects_empty_input() -> None:
    with pytest.raises(ValidationError):
        IncidentJsonExportInput()
