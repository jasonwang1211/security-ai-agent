import subprocess
import sys

import pytest
from pydantic import ValidationError

from modules.workflow_types import (
    WorkflowPlan,
    WorkflowStep,
    build_preview_workflow_plan,
    is_workflow_executable_without_human_approval,
)


def make_read_only_step() -> WorkflowStep:
    return WorkflowStep(
        step_id="step-001",
        tool_name="report_explainer",
        purpose="Explain report details.",
        execution_mode="READ_ONLY",
        permission="READ_ONLY",
        reason="Read-only helper.",
    )


def test_workflow_step_rejects_blank_step_id() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id=" ",
            tool_name="report_explainer",
            purpose="Explain report details.",
            execution_mode="READ_ONLY",
            permission="READ_ONLY",
            reason="Read-only helper.",
        )


def test_workflow_step_rejects_blank_tool_name() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-001",
            tool_name=" ",
            purpose="Explain report details.",
            execution_mode="READ_ONLY",
            permission="READ_ONLY",
            reason="Read-only helper.",
        )


def test_workflow_step_rejects_blank_purpose() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-001",
            tool_name="report_explainer",
            purpose=" ",
            execution_mode="READ_ONLY",
            permission="READ_ONLY",
            reason="Read-only helper.",
        )


def test_workflow_step_rejects_blank_reason() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-001",
            tool_name="report_explainer",
            purpose="Explain report details.",
            execution_mode="READ_ONLY",
            permission="READ_ONLY",
            reason=" ",
        )


def test_forbidden_execution_mode_requires_blocked_status() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-001",
            tool_name="real_firewall_block",
            purpose="Forbidden real enforcement.",
            execution_mode="FORBIDDEN",
            permission="FORBIDDEN",
            reason="Forbidden.",
        )


def test_forbidden_permission_requires_blocked_status() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-001",
            tool_name="real_firewall_block",
            purpose="Forbidden real enforcement.",
            execution_mode="READ_ONLY",
            permission="FORBIDDEN",
            reason="Forbidden.",
        )


def test_human_approval_execution_mode_requires_human_approval() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-001",
            tool_name="knowledge_capture_draft",
            purpose="Draft knowledge content.",
            execution_mode="HUMAN_APPROVAL_REQUIRED",
            permission="WRITE_DRAFT",
            reason="Draft requires review.",
        )


def test_write_review_required_permission_requires_human_approval() -> None:
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-001",
            tool_name="knowledge_ingest",
            purpose="Ingest knowledge.",
            execution_mode="HUMAN_APPROVAL_REQUIRED",
            permission="WRITE_REVIEW_REQUIRED",
            reason="Write requires review.",
        )


def test_workflow_plan_rejects_blank_plan_id() -> None:
    with pytest.raises(ValidationError):
        WorkflowPlan(
            plan_id=" ",
            route="report_followup",
            execution_mode="READ_ONLY",
            status="READY",
            steps=[make_read_only_step()],
            summary="Read-only plan.",
        )


def test_workflow_plan_rejects_blank_route() -> None:
    with pytest.raises(ValidationError):
        WorkflowPlan(
            plan_id="plan-001",
            route=" ",
            execution_mode="READ_ONLY",
            status="READY",
            steps=[make_read_only_step()],
            summary="Read-only plan.",
        )


def test_workflow_plan_rejects_empty_steps() -> None:
    with pytest.raises(ValidationError):
        WorkflowPlan(
            plan_id="plan-001",
            route="report_followup",
            execution_mode="READ_ONLY",
            status="READY",
            steps=[],
            summary="Read-only plan.",
        )


def test_build_preview_workflow_plan_creates_ready_plan_for_read_only_tools() -> None:
    plan = build_preview_workflow_plan(
        "plan-001",
        "report_followup",
        ["report_explainer", "answer_guardrails_check"],
        "Explain report safely.",
    )

    assert plan.status == "READY"
    assert plan.execution_mode == "READ_ONLY"
    assert [step.execution_mode for step in plan.steps] == ["READ_ONLY", "READ_ONLY"]


def test_build_preview_workflow_plan_blocks_unknown_tools() -> None:
    plan = build_preview_workflow_plan(
        "plan-001",
        "unknown",
        ["unknown_future_tool"],
        "Unknown tool plan.",
    )

    assert plan.status == "BLOCKED"
    assert plan.execution_mode == "FORBIDDEN"
    assert plan.steps[0].permission == "FORBIDDEN"
    assert plan.steps[0].status == "BLOCKED"


def test_build_preview_workflow_plan_marks_knowledge_capture_draft_as_human_approval_required() -> None:
    plan = build_preview_workflow_plan(
        "plan-001",
        "knowledge_capture",
        ["knowledge_capture_draft"],
        "Draft knowledge capture.",
    )

    assert plan.status == "READY"
    assert plan.execution_mode == "HUMAN_APPROVAL_REQUIRED"
    assert plan.steps[0].permission == "WRITE_DRAFT"
    assert plan.steps[0].requires_human_approval is True


def test_build_preview_workflow_plan_marks_simulated_block_as_simulated_only() -> None:
    plan = build_preview_workflow_plan(
        "plan-001",
        "simulated_response",
        ["simulated_block"],
        "Preview simulated block.",
    )

    assert plan.status == "READY"
    assert plan.execution_mode == "SIMULATED_ONLY"
    assert plan.steps[0].execution_mode == "SIMULATED_ONLY"
    assert "no real enforcement" in plan.steps[0].reason.lower()


def test_is_workflow_executable_without_human_approval_true_only_for_safe_read_only_plans() -> None:
    plan = build_preview_workflow_plan(
        "plan-001",
        "report_followup",
        ["report_explainer"],
        "Read-only report plan.",
    )

    assert is_workflow_executable_without_human_approval(plan) is True


def test_is_workflow_executable_without_human_approval_false_for_human_approval_plans() -> None:
    plan = build_preview_workflow_plan(
        "plan-001",
        "knowledge_capture",
        ["knowledge_capture_draft"],
        "Draft knowledge capture.",
    )

    assert is_workflow_executable_without_human_approval(plan) is False


def test_is_workflow_executable_without_human_approval_false_for_simulated_or_forbidden_plans() -> None:
    simulated_plan = build_preview_workflow_plan(
        "plan-001",
        "simulated_response",
        ["simulated_allow"],
        "Simulated allow.",
    )
    forbidden_plan = build_preview_workflow_plan(
        "plan-002",
        "forbidden",
        ["real_firewall_block"],
        "Forbidden real enforcement.",
    )

    assert is_workflow_executable_without_human_approval(simulated_plan) is False
    assert is_workflow_executable_without_human_approval(forbidden_plan) is False


def test_build_preview_workflow_plan_returns_data_only_and_does_not_execute_tools() -> None:
    plan = build_preview_workflow_plan(
        "plan-001",
        "report_followup",
        ["report_explainer"],
        "Read-only report plan.",
    )

    assert isinstance(plan, WorkflowPlan)
    assert plan.steps[0].tool_name == "report_explainer"
    assert "does not execute tools" in " ".join(plan.limitations)


def test_workflow_types_module_does_not_import_runtime_heavy_or_dispatch_modules() -> None:
    code = (
        "import sys; "
        "import modules.workflow_types; "
        "forbidden={"
        "'app',"
        "'modules.rag_qa',"
        "'modules.detector',"
        "'modules.controller_agent',"
        "'modules.tool_registry',"
        "'modules.skill_wrappers',"
        "'modules.smart_router',"
        "'chromadb',"
        "'ollama',"
        "'langchain',"
        "'torch',"
        "}; "
        "present=forbidden.intersection(sys.modules); "
        "raise SystemExit(1 if present else 0)"
    )

    result = subprocess.run([sys.executable, "-c", code], check=False)

    assert result.returncode == 0
