"""Pure layout metadata for the analyst console."""

from __future__ import annotations

from dataclasses import dataclass

ANALYSIS_GROUP = "Analysis"
CASE_INTELLIGENCE_GROUP = "Case Intelligence"
DRAFT_EXPORT_GROUP = "Draft / Export"
SYSTEM_DEBUG_GROUP = "System / Debug"

ANALYSIS_REPORT_PANEL = "Analysis Report"
SAFETY_BOUNDARY_PANEL = "Safety Boundary"
RAW_OUTPUT_PANEL = "Raw Output"
APPROVED_SIMILAR_CASES_PANEL = "Approved Similar Cases"
GRAPH_RELATIONS_PANEL = "Graph Relations"
CASE_MEMORY_PANEL = "Case Memory"
CASE_DRAFT_PANEL = "Case Draft"
EXPORT_REPORT_PANEL = "Export Report"
PERFORMANCE_PANEL = "Performance"
ROUTE_POLICY_PANEL = "Route / Policy"


@dataclass(frozen=True)
class WorkspacePanel:
    """A named panel inside one top-level console workspace group."""

    name: str
    default_expanded: bool = True


@dataclass(frozen=True)
class WorkspaceGroup:
    """Top-level console workspace group metadata."""

    name: str
    caption: str
    panels: tuple[WorkspacePanel, ...]


WORKSPACE_GROUPS = (
    WorkspaceGroup(
        name=ANALYSIS_GROUP,
        caption="Primary triage output and safety boundaries.",
        panels=(
            WorkspacePanel(ANALYSIS_REPORT_PANEL),
            WorkspacePanel(SAFETY_BOUNDARY_PANEL),
            WorkspacePanel(RAW_OUTPUT_PANEL, default_expanded=False),
        ),
    ),
    WorkspaceGroup(
        name=CASE_INTELLIGENCE_GROUP,
        caption="Approved reference cases, text relationships, and seed memory.",
        panels=(
            WorkspacePanel(APPROVED_SIMILAR_CASES_PANEL),
            WorkspacePanel(GRAPH_RELATIONS_PANEL),
            WorkspacePanel(CASE_MEMORY_PANEL),
        ),
    ),
    WorkspaceGroup(
        name=DRAFT_EXPORT_GROUP,
        caption="Approval-gated draft workflow and in-memory report export.",
        panels=(
            WorkspacePanel(CASE_DRAFT_PANEL),
            WorkspacePanel(EXPORT_REPORT_PANEL),
        ),
    ),
    WorkspaceGroup(
        name=SYSTEM_DEBUG_GROUP,
        caption="Diagnostic timing and deterministic route/policy details.",
        panels=(
            WorkspacePanel(PERFORMANCE_PANEL),
            WorkspacePanel(ROUTE_POLICY_PANEL),
        ),
    ),
)


def workspace_group_names() -> tuple[str, ...]:
    """Return top-level console group names in display order."""

    return tuple(group.name for group in WORKSPACE_GROUPS)


def panel_names_for_group(group_name: str) -> tuple[str, ...]:
    """Return panel names for a known top-level workspace group."""

    for group in WORKSPACE_GROUPS:
        if group.name == group_name:
            return tuple(panel.name for panel in group.panels)
    raise KeyError(f"Unknown workspace group: {group_name}")
