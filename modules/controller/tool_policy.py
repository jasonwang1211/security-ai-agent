"""Schema and deterministic dispatch-gate helpers for tool policy boundaries.

In v2.4-A, read-only DIRECT_ALLOWED skills may be permitted by deterministic
runtime policy. Future write-capable skills remain blocked without explicit
human approval, and policy never grants real firewall/WAF/SIEM/SOAR/cloud
enforcement authority.
"""

from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

ToolPermission = Literal[
    "READ_ONLY",
    "WRITE_DRAFT",
    "WRITE_REVIEW_REQUIRED",
    "SIMULATED_ACTION",
    "FORBIDDEN",
]
ToolExecutionMode = Literal[
    "DIRECT_ALLOWED",
    "PREVIEW_ONLY",
    "HUMAN_APPROVAL_REQUIRED",
    "SIMULATED_ONLY",
    "BLOCKED",
]
ToolRiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class ToolPolicy(BaseModel):
    """Static permission and execution-mode contract for one tool."""

    tool_name: str
    permission: ToolPermission
    execution_mode: ToolExecutionMode
    risk_level: ToolRiskLevel
    requires_human_approval: bool = False
    reason: str

    @field_validator("tool_name")
    @classmethod
    def tool_name_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "tool_name")

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "reason")

    @model_validator(mode="after")
    def policy_must_match_permission_boundary(self) -> "ToolPolicy":
        if self.permission == "FORBIDDEN" and self.execution_mode != "BLOCKED":
            raise ValueError("FORBIDDEN permission must use BLOCKED execution_mode")
        if self.permission == "WRITE_REVIEW_REQUIRED" and not self.requires_human_approval:
            raise ValueError("WRITE_REVIEW_REQUIRED must require human approval")
        if (
            self.risk_level == "CRITICAL"
            and self.permission != "FORBIDDEN"
            and not self.requires_human_approval
        ):
            raise ValueError("CRITICAL risk must require human approval unless permission is FORBIDDEN")
        if self.permission == "SIMULATED_ACTION" and self.execution_mode not in {
            "SIMULATED_ONLY",
            "PREVIEW_ONLY",
        }:
            raise ValueError("SIMULATED_ACTION must use SIMULATED_ONLY or PREVIEW_ONLY")
        return self


class ToolPolicyDecision(BaseModel):
    """Policy evaluation result used by dispatch gates; no tool execution."""

    tool_name: str
    allowed: bool
    permission: ToolPermission
    execution_mode: ToolExecutionMode
    requires_human_approval: bool
    reason: str

    @field_validator("tool_name")
    @classmethod
    def tool_name_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "tool_name")

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "reason")


_KNOWN_TOOL_POLICIES: dict[str, ToolPolicy] = {
    "AnalyzePayloadSkill": ToolPolicy(
        tool_name="AnalyzePayloadSkill",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only payload/event analysis with in-memory active context only.",
    ),
    "AnalyzeAuthenticationLogSkill": ToolPolicy(
        tool_name="AnalyzeAuthenticationLogSkill",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only authentication log analysis with in-memory active context only.",
    ),
    "ExplainActiveEventSkill": ToolPolicy(
        tool_name="ExplainActiveEventSkill",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only explanation over the current active event context.",
    ),
    "ExplainActiveIncidentSkill": ToolPolicy(
        tool_name="ExplainActiveIncidentSkill",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only explanation over the current active incident context.",
    ),
    "KnowledgeQASkill": ToolPolicy(
        tool_name="KnowledgeQASkill",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only protected knowledge question answering.",
    ),
    "DraftCaseCaptureSkill": ToolPolicy(
        tool_name="DraftCaseCaptureSkill",
        permission="WRITE_DRAFT",
        execution_mode="HUMAN_APPROVAL_REQUIRED",
        risk_level="MEDIUM",
        requires_human_approval=True,
        reason="Approval-gated case draft capture requires explicit human approval; request and cancel actions write nothing.",
    ),
    "RetrieveApprovedSimilarCaseSkill": ToolPolicy(
        tool_name="RetrieveApprovedSimilarCaseSkill",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only retrieval over manually curated approved case seeds.",
    ),
    "vector_rag_search": ToolPolicy(
        tool_name="vector_rag_search",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only retrieval helper.",
    ),
    "graph_lookup": ToolPolicy(
        tool_name="graph_lookup",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only graph lookup helper.",
    ),
    "report_explainer": ToolPolicy(
        tool_name="report_explainer",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only report explanation helper.",
    ),
    "rule_explainer": ToolPolicy(
        tool_name="rule_explainer",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only rule explanation helper.",
    ),
    "answer_guardrails_check": ToolPolicy(
        tool_name="answer_guardrails_check",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only answer safety check.",
    ),
    "analyst_suggestions": ToolPolicy(
        tool_name="analyst_suggestions",
        permission="READ_ONLY",
        execution_mode="DIRECT_ALLOWED",
        risk_level="LOW",
        reason="Read-only analyst suggestion helper.",
    ),
    "smart_router_preview": ToolPolicy(
        tool_name="smart_router_preview",
        permission="READ_ONLY",
        execution_mode="PREVIEW_ONLY",
        risk_level="LOW",
        reason="Preview-only route classification helper.",
    ),
    "knowledge_capture_draft": ToolPolicy(
        tool_name="knowledge_capture_draft",
        permission="WRITE_DRAFT",
        execution_mode="HUMAN_APPROVAL_REQUIRED",
        risk_level="MEDIUM",
        requires_human_approval=True,
        reason="Draft-only knowledge capture requires human review.",
    ),
    "rule_draft_suggestion": ToolPolicy(
        tool_name="rule_draft_suggestion",
        permission="WRITE_DRAFT",
        execution_mode="HUMAN_APPROVAL_REQUIRED",
        risk_level="MEDIUM",
        requires_human_approval=True,
        reason="Draft-only rule suggestion requires human review.",
    ),
    "knowledge_ingest": ToolPolicy(
        tool_name="knowledge_ingest",
        permission="WRITE_REVIEW_REQUIRED",
        execution_mode="HUMAN_APPROVAL_REQUIRED",
        risk_level="HIGH",
        requires_human_approval=True,
        reason="Knowledge ingest writes require human review.",
    ),
    "graph_commit": ToolPolicy(
        tool_name="graph_commit",
        permission="WRITE_REVIEW_REQUIRED",
        execution_mode="HUMAN_APPROVAL_REQUIRED",
        risk_level="HIGH",
        requires_human_approval=True,
        reason="Graph commits require human review.",
    ),
    "simulated_block": ToolPolicy(
        tool_name="simulated_block",
        permission="SIMULATED_ACTION",
        execution_mode="SIMULATED_ONLY",
        risk_level="MEDIUM",
        reason="Simulated BLOCK decision only; no real enforcement.",
    ),
    "simulated_monitor": ToolPolicy(
        tool_name="simulated_monitor",
        permission="SIMULATED_ACTION",
        execution_mode="SIMULATED_ONLY",
        risk_level="LOW",
        reason="Simulated MONITOR decision only; no real enforcement.",
    ),
    "simulated_allow": ToolPolicy(
        tool_name="simulated_allow",
        permission="SIMULATED_ACTION",
        execution_mode="SIMULATED_ONLY",
        risk_level="LOW",
        reason="Simulated ALLOW decision only; no real enforcement.",
    ),
    "real_firewall_block": ToolPolicy(
        tool_name="real_firewall_block",
        permission="FORBIDDEN",
        execution_mode="BLOCKED",
        risk_level="CRITICAL",
        reason="Real firewall enforcement is forbidden.",
    ),
    "real_waf_update": ToolPolicy(
        tool_name="real_waf_update",
        permission="FORBIDDEN",
        execution_mode="BLOCKED",
        risk_level="CRITICAL",
        reason="Real WAF updates are forbidden.",
    ),
    "real_account_disable": ToolPolicy(
        tool_name="real_account_disable",
        permission="FORBIDDEN",
        execution_mode="BLOCKED",
        risk_level="CRITICAL",
        reason="Real account disablement is forbidden.",
    ),
    "auto_rule_activation": ToolPolicy(
        tool_name="auto_rule_activation",
        permission="FORBIDDEN",
        execution_mode="BLOCKED",
        risk_level="CRITICAL",
        reason="Automatic rule activation is forbidden.",
    ),
    "autonomous_rule_deployment": ToolPolicy(
        tool_name="autonomous_rule_deployment",
        permission="FORBIDDEN",
        execution_mode="BLOCKED",
        risk_level="CRITICAL",
        reason="Autonomous rule deployment is forbidden.",
    ),
}


def default_policy_for_tool(tool_name: str) -> ToolPolicy:
    """Return a known policy or a safe forbidden default for unknown tools."""

    _require_non_blank(tool_name, "tool_name")
    policy = _KNOWN_TOOL_POLICIES.get(tool_name)
    if policy is not None:
        return policy.model_copy()
    # Unknown tools default to blocked/forbidden as a safety boundary.
    return ToolPolicy(
        tool_name=tool_name,
        permission="FORBIDDEN",
        execution_mode="BLOCKED",
        risk_level="CRITICAL",
        reason="Unknown tools default to FORBIDDEN.",
    )


def evaluate_tool_policy(tool_name: str) -> ToolPolicyDecision:
    """Evaluate deterministic permission data without executing the tool."""

    policy = default_policy_for_tool(tool_name)
    allowed = (
        policy.permission in {"READ_ONLY", "SIMULATED_ACTION"}
        and policy.execution_mode != "BLOCKED"
        and not policy.requires_human_approval
    )
    if policy.permission in {"WRITE_DRAFT", "WRITE_REVIEW_REQUIRED"}:
        allowed = False
    if policy.permission == "FORBIDDEN":
        allowed = False
    return ToolPolicyDecision(
        tool_name=policy.tool_name,
        allowed=allowed,
        permission=policy.permission,
        execution_mode=policy.execution_mode,
        requires_human_approval=policy.requires_human_approval,
        reason=policy.reason,
    )


def is_tool_allowed_without_human_approval(tool_name: str) -> bool:
    """Return true only for low-risk read-only direct-allowed tools."""

    policy = default_policy_for_tool(tool_name)
    return (
        policy.permission == "READ_ONLY"
        and policy.execution_mode == "DIRECT_ALLOWED"
        and policy.risk_level == "LOW"
        and not policy.requires_human_approval
    )
