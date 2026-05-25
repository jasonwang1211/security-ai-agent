"""Schema-only workflow preview contracts for controller tools.

WorkflowPlan objects describe planned steps; they do not execute tools, wire
runtime behavior, or perform real enforcement actions.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from modules.controller.tool_policy import ToolPermission, default_policy_for_tool

WorkflowExecutionMode = Literal[
    "PREVIEW_ONLY",
    "READ_ONLY",
    "HUMAN_APPROVAL_REQUIRED",
    "SIMULATED_ONLY",
    "FORBIDDEN",
]
WorkflowPlanStatus = Literal["DRAFT", "READY", "BLOCKED"]
WorkflowStepStatus = Literal["PENDING", "SKIPPED", "BLOCKED"]


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class WorkflowStep(BaseModel):
    """One schema-only workflow preview step."""

    step_id: str
    tool_name: str
    purpose: str
    execution_mode: WorkflowExecutionMode
    permission: ToolPermission
    status: WorkflowStepStatus = "PENDING"
    requires_human_approval: bool = False
    reason: str

    @field_validator("step_id")
    @classmethod
    def step_id_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "step_id")

    @field_validator("tool_name")
    @classmethod
    def tool_name_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "tool_name")

    @field_validator("purpose")
    @classmethod
    def purpose_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "purpose")

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "reason")

    @model_validator(mode="after")
    def step_boundaries_must_match_mode_and_permission(self) -> "WorkflowStep":
        if self.execution_mode == "FORBIDDEN" and self.status != "BLOCKED":
            raise ValueError("FORBIDDEN execution_mode must use BLOCKED status")
        if self.permission == "FORBIDDEN" and self.status != "BLOCKED":
            raise ValueError("FORBIDDEN permission must use BLOCKED status")
        if self.execution_mode == "HUMAN_APPROVAL_REQUIRED" and not self.requires_human_approval:
            raise ValueError("HUMAN_APPROVAL_REQUIRED execution_mode must require human approval")
        if self.permission == "WRITE_REVIEW_REQUIRED" and not self.requires_human_approval:
            raise ValueError("WRITE_REVIEW_REQUIRED permission must require human approval")
        return self


class WorkflowPlan(BaseModel):
    """Schema-only workflow preview composed of ordered steps."""

    plan_id: str
    route: str
    execution_mode: WorkflowExecutionMode
    status: WorkflowPlanStatus = "DRAFT"
    steps: list[WorkflowStep]
    summary: str
    limitations: list[str] = Field(default_factory=list)

    @field_validator("plan_id")
    @classmethod
    def plan_id_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "plan_id")

    @field_validator("route")
    @classmethod
    def route_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "route")

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "summary")

    @field_validator("steps")
    @classmethod
    def steps_must_not_be_empty(cls, value: list[WorkflowStep]) -> list[WorkflowStep]:
        if not value:
            raise ValueError("steps must not be empty")
        return value

    @model_validator(mode="after")
    def plan_status_must_match_steps_and_mode(self) -> "WorkflowPlan":
        if any(step.status == "BLOCKED" for step in self.steps) and self.status != "BLOCKED":
            raise ValueError("plans with blocked steps must use BLOCKED status")
        if self.execution_mode == "FORBIDDEN" and self.status != "BLOCKED":
            raise ValueError("FORBIDDEN execution_mode must use BLOCKED status")
        if self.execution_mode == "HUMAN_APPROVAL_REQUIRED" and not any(
            step.requires_human_approval for step in self.steps
        ):
            raise ValueError("HUMAN_APPROVAL_REQUIRED plans need at least one approval step")
        return self


def build_preview_workflow_plan(
    plan_id: str,
    route: str,
    tool_names: list[str],
    summary: str,
) -> WorkflowPlan:
    """Build a schema-only preview plan from tool policy decisions."""

    steps = [
        _step_from_tool_policy(index=index, tool_name=tool_name)
        for index, tool_name in enumerate(tool_names, start=1)
    ]
    execution_mode = _aggregate_execution_mode(steps)
    status: WorkflowPlanStatus = "BLOCKED" if any(step.status == "BLOCKED" for step in steps) else "READY"
    return WorkflowPlan(
        plan_id=plan_id,
        route=route,
        execution_mode=execution_mode,
        status=status,
        steps=steps,
        summary=summary,
        limitations=[
            "Workflow plans are schema-only previews.",
            "This plan does not execute tools or change runtime state.",
        ],
    )


def is_workflow_executable_without_human_approval(plan: WorkflowPlan) -> bool:
    """Return true only for ready read-only preview plans."""

    if plan.status != "READY" or plan.execution_mode != "READ_ONLY":
        return False
    return all(
        step.status != "BLOCKED"
        and step.permission == "READ_ONLY"
        and step.execution_mode == "READ_ONLY"
        and not step.requires_human_approval
        for step in plan.steps
    )


def _step_from_tool_policy(index: int, tool_name: str) -> WorkflowStep:
    policy = default_policy_for_tool(tool_name)
    execution_mode = _workflow_mode_from_policy(
        permission=policy.permission,
        execution_mode=policy.execution_mode,
    )
    status: WorkflowStepStatus = "BLOCKED" if execution_mode == "FORBIDDEN" else "PENDING"
    return WorkflowStep(
        step_id=f"step-{index:03d}",
        tool_name=policy.tool_name,
        purpose=f"Preview policy for {policy.tool_name}.",
        execution_mode=execution_mode,
        permission=policy.permission,
        status=status,
        requires_human_approval=policy.requires_human_approval,
        reason=policy.reason,
    )


def _workflow_mode_from_policy(
    *,
    permission: ToolPermission,
    execution_mode: str,
) -> WorkflowExecutionMode:
    if permission == "FORBIDDEN" or execution_mode == "BLOCKED":
        return "FORBIDDEN"
    if execution_mode == "HUMAN_APPROVAL_REQUIRED" or permission in {
        "WRITE_DRAFT",
        "WRITE_REVIEW_REQUIRED",
    }:
        return "HUMAN_APPROVAL_REQUIRED"
    if permission == "SIMULATED_ACTION" or execution_mode == "SIMULATED_ONLY":
        return "SIMULATED_ONLY"
    if execution_mode == "PREVIEW_ONLY":
        return "PREVIEW_ONLY"
    return "READ_ONLY"


def _aggregate_execution_mode(steps: list[WorkflowStep]) -> WorkflowExecutionMode:
    """Return the most restrictive execution mode represented by the steps."""

    modes = {step.execution_mode for step in steps}
    if "FORBIDDEN" in modes:
        return "FORBIDDEN"
    if "HUMAN_APPROVAL_REQUIRED" in modes:
        return "HUMAN_APPROVAL_REQUIRED"
    if "SIMULATED_ONLY" in modes:
        return "SIMULATED_ONLY"
    if "PREVIEW_ONLY" in modes:
        return "PREVIEW_ONLY"
    return "READ_ONLY"
