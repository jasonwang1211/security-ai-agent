import subprocess
import sys

import pytest
from pydantic import ValidationError

from modules.controller.tool_policy import (
    ToolPermission,
    ToolPolicy,
    ToolPolicyDecision,
    default_policy_for_tool,
    evaluate_tool_policy,
    is_tool_allowed_without_human_approval,
)


def test_tool_policy_rejects_blank_tool_name() -> None:
    with pytest.raises(ValidationError):
        ToolPolicy(
            tool_name=" ",
            permission="READ_ONLY",
            execution_mode="DIRECT_ALLOWED",
            risk_level="LOW",
            reason="Read-only helper.",
        )


def test_tool_policy_rejects_blank_reason() -> None:
    with pytest.raises(ValidationError):
        ToolPolicy(
            tool_name="report_explainer",
            permission="READ_ONLY",
            execution_mode="DIRECT_ALLOWED",
            risk_level="LOW",
            reason=" ",
        )


def test_forbidden_permission_must_use_blocked_execution_mode() -> None:
    with pytest.raises(ValidationError):
        ToolPolicy(
            tool_name="real_firewall_block",
            permission="FORBIDDEN",
            execution_mode="PREVIEW_ONLY",
            risk_level="CRITICAL",
            reason="Forbidden real enforcement.",
        )


def test_write_review_required_requires_human_approval() -> None:
    with pytest.raises(ValidationError):
        ToolPolicy(
            tool_name="knowledge_ingest",
            permission="WRITE_REVIEW_REQUIRED",
            execution_mode="HUMAN_APPROVAL_REQUIRED",
            risk_level="HIGH",
            reason="Writes require review.",
        )


def test_critical_risk_requires_human_approval_unless_forbidden() -> None:
    with pytest.raises(ValidationError):
        ToolPolicy(
            tool_name="critical_read",
            permission="READ_ONLY",
            execution_mode="PREVIEW_ONLY",
            risk_level="CRITICAL",
            reason="Critical read requires review.",
        )

    policy = ToolPolicy(
        tool_name="real_firewall_block",
        permission="FORBIDDEN",
        execution_mode="BLOCKED",
        risk_level="CRITICAL",
        reason="Forbidden real enforcement.",
    )

    assert policy.requires_human_approval is False


def test_simulated_action_must_use_simulated_or_preview_mode() -> None:
    with pytest.raises(ValidationError):
        ToolPolicy(
            tool_name="simulated_block",
            permission="SIMULATED_ACTION",
            execution_mode="DIRECT_ALLOWED",
            risk_level="MEDIUM",
            reason="Simulation only.",
        )


def test_unknown_tool_defaults_to_forbidden_blocked_critical() -> None:
    policy = default_policy_for_tool("unknown_future_tool")

    assert policy.permission == "FORBIDDEN"
    assert policy.execution_mode == "BLOCKED"
    assert policy.risk_level == "CRITICAL"
    assert evaluate_tool_policy("unknown_future_tool").allowed is False


def test_read_only_report_explainer_is_allowed() -> None:
    policy = default_policy_for_tool("report_explainer")
    decision = evaluate_tool_policy("report_explainer")

    assert policy.permission == "READ_ONLY"
    assert policy.execution_mode == "DIRECT_ALLOWED"
    assert decision.allowed is True


def test_smart_router_preview_is_read_only_and_preview_safe() -> None:
    policy = default_policy_for_tool("smart_router_preview")
    decision = evaluate_tool_policy("smart_router_preview")

    assert policy.permission == "READ_ONLY"
    assert policy.execution_mode == "PREVIEW_ONLY"
    assert decision.allowed is True
    assert is_tool_allowed_without_human_approval("smart_router_preview") is False


def test_knowledge_capture_draft_requires_human_approval() -> None:
    policy = default_policy_for_tool("knowledge_capture_draft")
    decision = evaluate_tool_policy("knowledge_capture_draft")

    assert policy.permission == "WRITE_DRAFT"
    assert policy.execution_mode == "HUMAN_APPROVAL_REQUIRED"
    assert policy.requires_human_approval is True
    assert decision.allowed is False
    assert is_tool_allowed_without_human_approval("knowledge_capture_draft") is False


def test_knowledge_ingest_requires_human_approval_and_is_not_directly_allowed() -> None:
    decision = evaluate_tool_policy("knowledge_ingest")

    assert decision.permission == "WRITE_REVIEW_REQUIRED"
    assert decision.execution_mode == "HUMAN_APPROVAL_REQUIRED"
    assert decision.requires_human_approval is True
    assert decision.allowed is False


def test_graph_commit_requires_human_approval_and_is_not_directly_allowed() -> None:
    decision = evaluate_tool_policy("graph_commit")

    assert decision.permission == "WRITE_REVIEW_REQUIRED"
    assert decision.requires_human_approval is True
    assert decision.allowed is False


def test_simulated_block_is_simulated_action_not_real_enforcement() -> None:
    policy = default_policy_for_tool("simulated_block")
    decision = evaluate_tool_policy("simulated_block")

    assert policy.permission == "SIMULATED_ACTION"
    assert policy.execution_mode == "SIMULATED_ONLY"
    assert "no real enforcement" in policy.reason.lower()
    assert decision.allowed is True
    assert is_tool_allowed_without_human_approval("simulated_block") is False


def test_real_firewall_block_is_forbidden() -> None:
    decision = evaluate_tool_policy("real_firewall_block")

    assert decision.permission == "FORBIDDEN"
    assert decision.execution_mode == "BLOCKED"
    assert decision.allowed is False


def test_auto_rule_activation_is_forbidden() -> None:
    decision = evaluate_tool_policy("auto_rule_activation")

    assert decision.permission == "FORBIDDEN"
    assert decision.execution_mode == "BLOCKED"
    assert decision.allowed is False


def test_evaluate_tool_policy_returns_decision_only_and_does_not_execute_tools() -> None:
    decision = evaluate_tool_policy("report_explainer")

    assert isinstance(decision, ToolPolicyDecision)
    assert decision.tool_name == "report_explainer"
    assert decision.reason


def test_is_tool_allowed_without_human_approval_true_only_for_safe_read_only_tools() -> None:
    assert is_tool_allowed_without_human_approval("report_explainer") is True
    assert is_tool_allowed_without_human_approval("answer_guardrails_check") is True
    assert is_tool_allowed_without_human_approval("knowledge_capture_draft") is False
    assert is_tool_allowed_without_human_approval("knowledge_ingest") is False
    assert is_tool_allowed_without_human_approval("simulated_allow") is False
    assert is_tool_allowed_without_human_approval("real_waf_update") is False
    assert is_tool_allowed_without_human_approval("unknown_future_tool") is False


def test_v2_4_initial_runtime_skills_are_read_only_direct_allowed() -> None:
    for tool_name in [
        "AnalyzePayloadSkill",
        "AnalyzeAuthenticationLogSkill",
        "ExplainActiveEventSkill",
        "ExplainActiveIncidentSkill",
        "KnowledgeQASkill",
    ]:
        decision = evaluate_tool_policy(tool_name)

        assert decision.allowed is True
        assert decision.permission == "READ_ONLY"
        assert decision.execution_mode == "DIRECT_ALLOWED"
        assert decision.requires_human_approval is False
        assert is_tool_allowed_without_human_approval(tool_name) is True


def test_future_draft_case_capture_skill_requires_human_approval() -> None:
    decision = evaluate_tool_policy("DraftCaseCaptureSkill")

    assert decision.permission == "WRITE_DRAFT"
    assert decision.execution_mode == "HUMAN_APPROVAL_REQUIRED"
    assert decision.requires_human_approval is True
    assert decision.allowed is False
    assert "explicit human approval" in decision.reason
    assert is_tool_allowed_without_human_approval("DraftCaseCaptureSkill") is False


def test_tool_policy_module_does_not_import_runtime_heavy_or_dispatch_modules() -> None:
    code = (
        "import sys; "
        "import modules.controller.tool_policy; "
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


def test_tool_policy_shim_reexports_canonical_permission_type() -> None:
    from modules.tool_policy import ToolPermission as ShimToolPermission

    assert ShimToolPermission is ToolPermission
