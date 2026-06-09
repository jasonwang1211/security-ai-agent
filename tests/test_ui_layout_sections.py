import sys
from pathlib import Path

from modules.ui.layout_sections import (
    AI_ANALYST_GROUP,
    ANALYSIS_GROUP,
    ANALYSIS_REPORT_PANEL,
    APPROVED_SIMILAR_CASES_PANEL,
    CASE_DRAFT_PANEL,
    CASE_INTELLIGENCE_GROUP,
    DRAFT_EXPORT_GROUP,
    EXPORT_REPORT_PANEL,
    FOLLOWUP_ASSISTANT_PANEL,
    KNOWLEDGE_QA_PANEL,
    PERFORMANCE_PANEL,
    ROUTE_POLICY_PANEL,
    SYSTEM_DEBUG_GROUP,
    panel_names_for_group,
    workspace_group_names,
)


def test_workspace_groups_are_in_expected_order() -> None:
    assert workspace_group_names() == (
        ANALYSIS_GROUP,
        CASE_INTELLIGENCE_GROUP,
        DRAFT_EXPORT_GROUP,
        AI_ANALYST_GROUP,
        SYSTEM_DEBUG_GROUP,
    )


def test_workspace_group_metadata_contains_expected_panels() -> None:
    assert ANALYSIS_REPORT_PANEL in panel_names_for_group(ANALYSIS_GROUP)
    assert APPROVED_SIMILAR_CASES_PANEL in panel_names_for_group(CASE_INTELLIGENCE_GROUP)
    assert CASE_DRAFT_PANEL in panel_names_for_group(DRAFT_EXPORT_GROUP)
    assert EXPORT_REPORT_PANEL in panel_names_for_group(DRAFT_EXPORT_GROUP)
    assert PERFORMANCE_PANEL in panel_names_for_group(SYSTEM_DEBUG_GROUP)
    assert ROUTE_POLICY_PANEL in panel_names_for_group(SYSTEM_DEBUG_GROUP)


def test_ai_analyst_group_contains_followup_and_knowledge_panels() -> None:
    assert AI_ANALYST_GROUP in workspace_group_names()
    panels = panel_names_for_group(AI_ANALYST_GROUP)
    assert FOLLOWUP_ASSISTANT_PANEL in panels
    assert KNOWLEDGE_QA_PANEL in panels
    # AI Analyst sits after Draft / Export and before System / Debug.
    names = workspace_group_names()
    assert names.index(AI_ANALYST_GROUP) == names.index(DRAFT_EXPORT_GROUP) + 1
    assert names.index(AI_ANALYST_GROUP) == names.index(SYSTEM_DEBUG_GROUP) - 1


def test_layout_section_helpers_do_not_import_streamlit() -> None:
    source = Path("modules/ui/layout_sections.py").read_text(encoding="utf-8")

    assert "streamlit" not in source.lower()
    assert "streamlit" not in sys.modules
