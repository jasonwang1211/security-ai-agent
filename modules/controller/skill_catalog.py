from modules.controller.registry import ToolRegistry
from modules.controller.types import (
    IncidentJsonExportInput,
    KnowledgeQuestionInput,
    LogFileInput,
    PayloadTriageInput,
    RawLogInput,
    ReportFollowupInput,
    ToolExecutionResult,
    ToolSpec,
)

PAYLOAD_TRIAGE = "payload_triage"
RAW_LOG_TRANSLATE = "raw_log_translate"
LOG_FILE_INGEST = "log_file_ingest"
RAG_SECURITY_QA = "rag_security_qa"
REPORT_FOLLOWUP = "report_followup"
INCIDENT_JSON_EXPORT = "incident_json_export"


def build_v1_5_tool_specs() -> list[ToolSpec]:
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
    return ToolRegistry(build_v1_5_tool_specs())
