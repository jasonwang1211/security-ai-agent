"""Fixed controller skill catalog for existing local capabilities."""

from modules.controller.registry import ToolRegistry
from modules.controller.types import (
    CaseDraftInput,
    IncidentJsonExportInput,
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    RawLogInput,
    ReportFollowupInput,
    SimilarCaseInput,
    ToolExecutionResult,
    ToolSpec,
)

PAYLOAD_TRIAGE = "payload_triage"
RAW_LOG_TRANSLATE = "raw_log_translate"
LOG_FILE_INGEST = "log_file_ingest"
RAG_SECURITY_QA = "rag_security_qa"
REPORT_FOLLOWUP = "report_followup"
INCIDENT_JSON_EXPORT = "incident_json_export"
ANALYZE_PAYLOAD_SKILL = "AnalyzePayloadSkill"
ANALYZE_AUTHENTICATION_LOG_SKILL = "AnalyzeAuthenticationLogSkill"
EXPLAIN_ACTIVE_EVENT_SKILL = "ExplainActiveEventSkill"
EXPLAIN_ACTIVE_INCIDENT_SKILL = "ExplainActiveIncidentSkill"
KNOWLEDGE_QA_SKILL = "KnowledgeQASkill"
DRAFT_CASE_CAPTURE_SKILL = "DraftCaseCaptureSkill"
RETRIEVE_APPROVED_SIMILAR_CASE_SKILL = "RetrieveApprovedSimilarCaseSkill"


def build_v1_5_tool_specs() -> list[ToolSpec]:
    """Return the fixed v1.5 ToolSpec list without deferred skills."""

    return [
        ToolSpec(
            name=PAYLOAD_TRIAGE,
            description="Run deterministic payload triage using existing local behavior.",
            input_model=PayloadTriageInput,
            output_model=ToolExecutionResult,
            safety_level="safe_local_analysis",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["payload_or_event"],
        ),
        ToolSpec(
            name=RAW_LOG_TRANSLATE,
            description="Translate a single raw log line using existing local behavior.",
            input_model=RawLogInput,
            output_model=ToolExecutionResult,
            safety_level="safe_local_analysis",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["raw_log_line"],
        ),
        ToolSpec(
            name=LOG_FILE_INGEST,
            description="Ingest a log file using the existing local log pipeline.",
            input_model=LogFileInput,
            output_model=ToolExecutionResult,
            safety_level="safe_local_analysis",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["log_file_path"],
        ),
        ToolSpec(
            name=RAG_SECURITY_QA,
            description="Answer a security knowledge question using existing RAG behavior.",
            input_model=KnowledgeQuestionInput,
            output_model=ToolExecutionResult,
            safety_level="advisory_explanation",
            deterministic=False,
            requires_llm=True,
            requires_rag=True,
            allowed_input_kinds=["security_knowledge_question"],
        ),
        ToolSpec(
            name=REPORT_FOLLOWUP,
            description="Answer report-aware follow-up questions using existing local behavior.",
            input_model=ReportFollowupInput,
            output_model=ToolExecutionResult,
            safety_level="advisory_explanation",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["report_followup"],
        ),
        ToolSpec(
            name=INCIDENT_JSON_EXPORT,
            description="Export incident JSON using existing local incident data.",
            input_model=IncidentJsonExportInput,
            output_model=ToolExecutionResult,
            safety_level="export_only",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["report_followup"],
        ),
    ]


def build_v1_5_registry() -> ToolRegistry:
    """Build a ToolRegistry from the fixed v1.5 skill catalog."""

    return ToolRegistry(build_v1_5_tool_specs())


def build_v2_4_tool_specs() -> list[ToolSpec]:
    """Return the deterministic v2.4 direct-input skill catalog."""

    return [
        ToolSpec(
            name=ANALYZE_PAYLOAD_SKILL,
            description="Analyze a payload or event using existing Mode 1 behavior.",
            input_model=PayloadTriageInput,
            output_model=ToolExecutionResult,
            safety_level="safe_local_analysis",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["payload_or_event"],
        ),
        ToolSpec(
            name=ANALYZE_AUTHENTICATION_LOG_SKILL,
            description="Analyze an authentication log file using existing Mode 2 behavior.",
            input_model=LogFileInput,
            output_model=ToolExecutionResult,
            safety_level="safe_local_analysis",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["log_file_path"],
        ),
        ToolSpec(
            name=EXPLAIN_ACTIVE_EVENT_SKILL,
            description="Explain the retained active payload/event context.",
            input_model=ReportFollowupInput,
            output_model=ToolExecutionResult,
            safety_level="advisory_explanation",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["report_followup"],
        ),
        ToolSpec(
            name=EXPLAIN_ACTIVE_INCIDENT_SKILL,
            description="Explain the retained active authentication incident context.",
            input_model=ReportFollowupInput,
            output_model=ToolExecutionResult,
            safety_level="advisory_explanation",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["report_followup"],
        ),
        ToolSpec(
            name=KNOWLEDGE_QA_SKILL,
            description="Answer a security knowledge question using existing protected Mode 3 behavior.",
            input_model=KnowledgeQuestionInput,
            output_model=ToolExecutionResult,
            safety_level="advisory_explanation",
            deterministic=False,
            requires_llm=True,
            requires_rag=True,
            allowed_input_kinds=["security_knowledge_question"],
        ),
    ]


def build_v2_4_registry() -> ToolRegistry:
    """Build a ToolRegistry for the v2.4 direct-input orchestration skills."""

    return ToolRegistry(build_v2_4_tool_specs())


def build_v2_5_tool_specs() -> list[ToolSpec]:
    """Return the v2.5 skill catalog with approval-gated case draft capture."""

    return [
        *build_v2_4_tool_specs(),
        ToolSpec(
            name=DRAFT_CASE_CAPTURE_SKILL,
            description="Prepare, approve, cancel, and write isolated reviewed-later case drafts.",
            input_model=CaseDraftInput,
            output_model=ToolExecutionResult,
            safety_level="draft_write_review_required",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["case_draft_request"],
            notes="Writes only isolated workbench/case_drafts markdown after explicit approval.",
        ),
        ToolSpec(
            name=RETRIEVE_APPROVED_SIMILAR_CASE_SKILL,
            description="Retrieve approved similar case seeds for the current active context.",
            input_model=SimilarCaseInput,
            output_model=ToolExecutionResult,
            safety_level="advisory_explanation",
            deterministic=True,
            requires_llm=False,
            requires_rag=False,
            allowed_input_kinds=["similar_case_request"],
            notes="Read-only deterministic retrieval over manually curated approved case seeds.",
        ),
    ]


def build_v2_5_registry() -> ToolRegistry:
    """Build a ToolRegistry for the v2.5 direct-input orchestration skills."""

    return ToolRegistry(build_v2_5_tool_specs())
