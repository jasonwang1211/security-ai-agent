# Architecture Debt Engineering Journal

Current milestone: v2.3 release gate passed; ready to tag
Current baseline: tag `v2.2.0`
Last full quality gate: v2.3 `670 passed in 8.23s`; Ruff, Mypy, diff-check, and Gitleaks passed

This document tracks structural debt cleanup as an engineering discipline: reducing module sprawl, consolidating thin wrappers, and preserving deterministic safety boundaries before adding more agentic behavior.

## Current Status

The project has reached a stable consolidated architecture with:

- Unified `Security Triage Report`
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- Raw auth log translation
- Log file ingestion and brute-force candidate aggregation
- `RAGQueryPlanner`-based knowledge QA
- Pydantic boundary models for future controller and tool work
- Evidence / Finding / Incident schemas and JSON Incident Report export
- Time-window authentication sequence correlation for Scenario A
- Advisory LLMAssist guardrails and report-aware follow-up
- YAML-based Detection-as-Code Lite rules with schema validation and metadata
- Isolated v1.5 ControllerAgent and Tool Registry infrastructure
- Isolated v1.6 RAG v2 helper infrastructure for source-cited explanations
- Isolated v1.7 reliability foundation for eval cases, deterministic AnswerGuardrails, Evaluation Runner, and rule-based Smart Router
- Isolated v1.8 protected report/rule helpers, guarded fallback behavior, Smart Router preview, and deterministic analyst suggestions
- v1.9 architecture cleanup and orchestration contracts: ownership map, ADRs, Tool Permission Contract, Workflow Plan Contract, Testing Strategy, and Package Migration Plan
- v2.0 Knowledge Graph Foundation: graph type contracts, deterministic builder, read-only lookup helpers, JSON-serializable export helpers, and 2A-3 seed-scope decision
- v2.1 Graph-Backed Explanation MVP: protected exact-reference graph explanations using explicit graph edges and existing `SourceCitation` provenance
- v2.2 Curated RAG Graph Seed Foundation: 9 reviewed Traditional Chinese report-explainer KB documents promoted to live, 20 live report-explainer docs, minimal typed metadata support, reviewed KnowledgeDoc graph seed candidates, and protected hybrid graph/knowledge explanation assembly
- v2.3 Controlled Retrieval and Structured Follow-Up: protected controlled Mode 3 retrieval, Mode 1 active payload-event follow-up, and Mode 2 current-incident graph-grounded authentication follow-up
- Controlled 9B package migration for RAG helper modules and controller/orchestration modules with temporary flat compatibility shims
- Manual smoke remains manual-only, not normal CI; targeted v2.3 runtime smoke has been completed for Mode 3 controlled retrieval, Mode 1 event follow-up, and Mode 2 graph-grounded incident follow-up

## Consolidation Outcomes

| Area | Before | After | Outcome |
|---|---|---|---|
| Triage policy | `risk_scorer.py`, `decision_engine.py`, `defense_simulator.py` | `triage_policy.py` | Consolidated risk scoring, decision mapping, and simulated defense policy |
| LLM assist | `llm_threat_judge.py`, `llm_analyzer.py` | `llm_assist.py` | Unified advisory LLM behavior and fallback handling |
| CLI mode wrappers | `modules/skills/*` | `mode_handlers.py` | Consolidated thin CLI wrappers |
| Log ingestion | parser / normalizer / aggregator / adapter modules | `log_pipeline.py` | Consolidated parse -> normalize -> aggregate -> adapt flow |
| Boundary contracts | ad-hoc dictionaries | `modules/types.py` | Added Pydantic boundary models for future controller/tool work |
| RAG helper ownership | flat `modules/rag_*.py` helpers | `modules/rag/` plus flat shims | Controlled helper package migration; `RAGQA` remains active runtime |
| Controller/orchestration ownership | flat controller/tool/policy/workflow modules | `modules/controller/` plus flat shims | Controlled package migration; no runtime auto-execution added |
| Graph foundation ownership | none | `modules/graph/` | In-memory graph contracts, deterministic builder, read-only lookup, JSON serialization, protected exact-reference explanation, and reviewed KnowledgeDoc seed candidates; no automatic Graph RAG or persistence |
| Testing foundation | limited smoke coverage | golden + log pipeline + boundary + incident + detection-rule + controller + RAG v2 + v1.7 reliability + v1.8 protected helper tests + v1.9 contract tests + v2.0 graph focused tests + v2.1 graph explanation focused tests + v2.2 focused metadata/seed/hybrid tests | Last full quality gate: v2.3 `670 passed in 8.23s`, Ruff, Mypy, diff-check, and Gitleaks |

## v1.3 Phase Outcomes

- Evidence / Finding / Incident schemas
- LLM Safety Layer Foundation
- Time-window auth sequence correlation
- JSON Incident Report export
- Minimal report-aware follow-up helper
- Evidence-grounded LLMAssist
- Scenario A integration test
- 11 `report_explainer` KB docs

Engineering note: v1.3 intentionally increased module count because the new modules represent separate responsibilities:

- `evidence_correlator.py`
- `incident_exporter.py`
- `llm_guardrails.py`
- `report_followup.py`

## v1.4 Phase Outcomes

- Detection rules moved into YAML files.
- Added `DetectionRule` schema and `RuleLoader`.
- Detector adapter now uses YAML rules as the primary path.
- Rule metadata exposed in detector results.
- Hard-coded signatures retained as conservative fallback during migration.
- Quality gate updated to `141 passed`.

Metrics note:

- Test count: `102 passed` -> `141 passed`
- New modules: `detection_rules.py`, `rule_loader.py`
- New rule directory: `detections/blue_team/`
- YAML rule files: 4
- Supported YAML attack types: XSS, SQL Injection, Path Traversal, Command Injection
- Hard-coded signatures retained as conservative fallback

New modules:

- `detection_rules.py`
- `rule_loader.py`

New rule folder:

- `detections/blue_team/`

## v1.5 Phase Outcomes

- Added typed ControllerAgent infrastructure while keeping existing CLI modes unchanged.
- Added deterministic dispatch by explicit route/tool name.
- Added six v1.5 wrapper skill contracts and thin wrappers.
- Verified `ToolRegistry`, Skill Catalog, Skill Wrappers, and `ControllerAgent` together through integration-style tests.
- Deferred Smart Router, Auto Route, LLM-driven routing, Rule Explainer, and Investigation Planner.

New modules:

- `controller_types.py`
- `tool_registry.py`
- `skill_catalog.py`
- `skill_wrappers.py`
- `controller_agent.py`

New tests:

- `test_controller_types.py`
- `test_tool_registry.py`
- `test_skill_catalog.py`
- `test_skill_wrappers.py`
- `test_controller_agent.py`
- `test_controller_agent_integration.py`

Quality gate:

- Previous v1.4 gate: `141 passed`
- Current v1.5 gate: `240 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed

Architecture note:

v1.5 intentionally keeps `ControllerAgent` isolated from CLI runtime. Existing CLI modes remain unchanged, and Smart Router is deferred.

## v1.6 Phase Outcomes

- Added RAG v2 boundary types, metadata parsing, rule-based intent classification, exact ID extraction, metadata-aware planning, source assembly, and deterministic report/rule explainer helpers.
- Added frontmatter metadata for the 11 `report_explainer` docs.
- Kept RAG v2 helpers isolated from the existing `RAGQA` runtime.
- Existing CLI modes remain unchanged.
- Deferred AnswerGuardrails, evaluation datasets, Smart Router, and Investigation Planner.

New modules:

- `rag_types.py`
- `rag_metadata.py`
- `rag_intent.py`
- `rag_retrieval_planner.py`
- `rag_source_assembly.py`
- `rag_explainers.py`

New tests:

- `test_rag_types.py`
- `test_rag_metadata.py`
- `test_rag_intent.py`
- `test_rag_retrieval_planner.py`
- `test_rag_source_assembly.py`
- `test_rag_explainers.py`

Quality gate:

- Previous v1.5 gate: `240 passed`
- Current v1.6 gate: `366 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed

Architecture note:

v1.6 intentionally keeps RAG v2 helpers isolated from the existing `RAGQA` runtime. Existing CLI modes remain unchanged. AnswerGuardrails and evaluation are deferred.

### RAG Runtime vs RAG v2 Helper Status

| Module | Status | Role |
|---|---|---|
| `rag_qa.py` | active runtime | Current RAG QA path used by existing CLI / agent flow |
| `rag_query_planner.py` | active legacy planner | Current planner used by existing RAG QA flow |
| `rag_types.py` | v1.6 helper foundation | Pydantic boundary types for future source-cited RAG |
| `rag_metadata.py` | v1.6 helper foundation | Frontmatter metadata parser for KB docs |
| `rag_intent.py` | v1.6 helper foundation | Rule-based intent classification and exact ID extraction |
| `rag_retrieval_planner.py` | v1.6 helper foundation | Metadata-aware candidate planning, no vector runtime |
| `rag_source_assembly.py` | v1.6 helper foundation | SourceCitation / AnswerWithSources assembly |
| `rag_explainers.py` | v1.6 helper foundation | Deterministic source-cited report/rule explanation helpers |

v1.6 intentionally keeps these helpers isolated from `rag_qa.py`. v1.7 ownership decision: `RAGQA` remains the active general knowledge QA runtime, while RAG v2 helpers remain staged for future narrow report/rule explanation wiring through `report_followup.py` or a protected helper path. This reduces the risk of adding more parallel RAG modules before AnswerGuardrails and eval coverage prove a user-facing path is safe.

## v1.7 Phase Outcomes

- Added small regression datasets under `eval_cases/`.
- Added `modules/eval_cases.py` for pure JSONL loading and validation.
- Added `modules/answer_guardrails.py` for deterministic answer safety checks.
- Added `modules/eval_runner.py` for deterministic eval smoke summaries.
- Added `modules/smart_router.py` for isolated rule-based route decisions.
- Added `modules/log_ingestion_runner.py` so runtime code no longer imports demo helpers.
- Added CI Gitleaks secret scanning.

Architecture note:

v1.7 intentionally keeps Smart Router isolated from CLI runtime. The phase improves reliability and evaluation before wiring. v1.8 should decide the protected wiring strategy for narrow report/rule explanations and any router activation.

## v1.8 Phase Outcomes

- Added protected report/rule explanation helper paths through `report_followup.py`.
- Refined guarded fallback behavior for unsafe helper output.
- Added Smart Router preview mode without CLI default wiring or tool execution.
- Added deterministic analyst follow-up suggestions.

Architecture note:

v1.8 intentionally keeps Smart Router preview isolated from CLI default behavior and does not replace `RAGQA`.

## v1.9 Phase Outcomes

- Added `docs/v1.9-spec.md` as the detailed design source of truth for Architecture Cleanup and Orchestration Contracts.
- Added `docs/ARCHITECTURE_MAP.md` to document runtime, helper, staged, eval, and docs ownership.
- Added ADRs for deterministic ControllerAgent behavior, follow-up boundaries, RAGQA/RAG helper coexistence, Tool Permission Model, and Workflow Plan Model.
- Added schema-only Tool Permission Contract and focused tests.
- Added schema-only Workflow Plan Contract and focused tests.
- Added Testing Strategy documentation.
- Added Package Migration Plan documentation.
- Migrated RAG v2 helper-only modules into `modules/rag/` with flat compatibility shims.
- Migrated controller/orchestration helper modules into `modules/controller/` with flat compatibility shims.
- Added manual LLM/RAG smoke checklist documentation as manual-only, not normal CI.

Architecture note:

v1.9 intentionally keeps contracts separate from runtime wiring. Tool Policy and Workflow Plan are schema-only. ControllerAgent does not auto-execute, Smart Router does not become the default CLI auto-route, and `RAGQA` remains the active general knowledge QA runtime.

The controlled package migrations improve ownership boundaries but do not change runtime behavior. `RAGQA` and RAG v2 helpers coexist: `RAGQA` remains the active general knowledge QA runtime, while RAG helper modules remain helper/staged infrastructure. Package shims are temporary compatibility layers and should be removed only after imports are stable and separately scoped.

## v2.0 Phase Outcomes

- Added `docs/v2.0-spec.md` as the detailed design source of truth for Knowledge Graph Foundation.
- Added graph type contracts: `GraphNodeKind`, `GraphEdgeKind`, `GraphSourceRef`, `GraphNode`, `GraphEdge`, and `GraphSnapshot`.
- Added deterministic `build_graph_snapshot(...)` for structured `Incident` objects and explicitly provided `DetectionRule` objects.
- Added read-only graph lookup helpers over in-memory `GraphSnapshot` objects.
- Added JSON-serializable graph export helpers without save/load or file persistence.
- Recorded the 2A-3 decision: do not add `rule_graph.py` now; keep explicit `DetectionRule` seed inside the builder; defer KnowledgeDoc graph seed until a metadata audit.

Architecture note:

v2.0 graph helpers are evidence/context infrastructure, not detection authority. They do not load YAML or files, infer relations from free text, call LLM/RAG/vector systems, execute tools, replace `RAGQA`, replace the Rule-Based Detector, write knowledge automatically, or change Risk Level / Decision. `BLOCK`, `MONITOR`, and `ALLOW` remain simulated decisions.

## v2.1 Phase Outcomes

- Added `modules/graph/explainers.py` as the canonical graph-backed explanation helper.
- Added `explain_graph_reference(snapshot, reference_id) -> AnswerWithSources` for exact `EV-*`, `F-*`, rule ID, and `INC-*` references.
- Reused existing `SourceCitation.metadata` for graph node, edge, and source provenance without expanding the RAG schema.
- Added `explain_graph_followup_protected(...)` in `modules/report_followup.py`, so graph-backed answers pass through existing `AnswerGuardrails`.
- Kept the feature as a protected helper and tested integration path, without CLI auto-routing or new `app.py` mode.

Architecture note:

v2.1 deliberately stays within explicit graph nodes and edges. Missing references do not produce fabricated graph citations, disconnected existing nodes are reported as having no explicit relationship, and graph explanations do not change Risk Level / Decision. Full Graph RAG retrieval, Knowledge Capture, LLM graph extraction, Neo4j/NetworkX, runtime orchestration, tool execution, `RAGQA` replacement, and real enforcement remain deferred.

## v2.2 Phase Outcomes

- Promoted 9 reviewed Traditional Chinese report-explainer KB documents into live `knowledge/blue_team/report_explainer/`.
- Expanded live report-explainer coverage from 11 to 20 documents.
- Added minimal typed metadata support for `title`, `review_status`, `finding_types`, `evidence_types`, `decision_labels`, and `tags`.
- Promoted documents use `schema_version: v2.2-live1` and `review_status: approved_for_runtime_promotion`.
- Kept five authentication documents retrieval/explanation-only with no graph-seed edges.
- Retained reviewed attack/rule metadata for XSS / `XSS-001` / `MEDIUM` / simulated `MONITOR`, SQL Injection / `SQLI-001` / `HIGH` / simulated `BLOCK`, Path Traversal / `PATH-001` / `HIGH` / simulated `BLOCK`, and Command Injection / `CMD-001` / `HIGH` / simulated `BLOCK`.
- Added `modules/graph/knowledge_doc_seed.py` for reviewed KnowledgeDoc graph seed candidates.
- Added `build_knowledge_doc_seed(...)`, which accepts parsed `KnowledgeDocMetadata` plus explicitly supplied `DetectionRule` objects.
- Limited seed edges to `RELATED_TO_ATTACK` and `MAPS_TO_RULE`, with provenance from `frontmatter.attack_types` and `frontmatter.rule_ids`.
- Added `combine_hybrid_explanation_protected(...)` in `modules/report_followup.py`.
- Combined already-built graph context and already-built curated knowledge context, preserved citations, and applied existing deterministic guardrails.
- Demonstrated Scenario A authentication hybrid context with `Decision` remaining simulated `MONITOR`.
- Demonstrated Command Injection hybrid context with `Decision` remaining simulated `BLOCK`.

Architecture note:

v2.2 implements protected hybrid explanation/context assembly using explicit graph context plus curated knowledge source context. It does not implement automatic Graph RAG retrieval, vector-to-graph expansion, Knowledge Capture, LLM graph extraction, `RAGQA` replacement, CLI auto-route, graph or LLM Risk Level / Decision override, tool execution, real enforcement, or real monitoring deployment. Existing legacy KB documents remain supported, and full corpus schema migration is deferred.

## v2.3 Phase Outcomes

- Added protected controlled Mode 3 retrieval before vector fallback for reviewed targets including SQL Injection, `CMD-001`, and `success_after_failures`.
- Mode 3 answers now return through the protected path with Traditional Chinese safety boundary text, internal metadata-label suppression, canonical visible RAG / LLM terminology, and deterministic final-authority wording.
- Mode 1 payload analysis retains an in-memory `ActiveEventContext` with facts produced by the current payload-analysis flow only.
- Mode 4 current-event follow-up explains classification reasoning, matched rule/signature evidence, simulated Decision boundary, exploitation uncertainty, and defensive investigation/remediation guidance.
- Mode 2 qualifying authentication logs create structured `Incident`, `Evidence`, and `Finding` values through deterministic correlation.
- Scenario A stores `ActiveAuthIncidentContext`, builds an explicit current-incident `GraphSnapshot`, and displays `INC-20260501-001`, `EV-003`, `F-001`, `HIGH`, and simulated `MONITOR`.
- Mode 4 graph-grounded authentication follow-up explains `EV-003`, the explicit `EV-003` / `F-001` support relationship, simulated `MONITOR`, compromise uncertainty, and investigation next steps.
- Non-qualifying Mode 2 log analysis clears stale structured context.

Architecture note:

v2.3 uses graph-grounded follow-up only for the current structured authentication incident. It does not implement direct-input Auto Router, Agent Skill Orchestration, LLM-assisted skill selection, Similar-Case Graph RAG, approved historical-case retrieval, Knowledge Capture or event write-back, automatic vector-to-graph expansion, the deferred Mode 3 KnowledgeDoc graph-expansion WIP, real firewall/WAF/EDR/account action, or RAG/LLM override of deterministic `Risk Level` or `Decision`. v2.3 release gate has passed and the milestone is ready to tag.

## Last Full Quality Gate

- `python -m pytest` -> `670 passed in 8.23s` for v2.3
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed, `106 source files`
- `git diff --check` -> passed
- Gitleaks -> passed, no leaks found across 167 commits scanned using `gitleaks detect --source . --verbose --redact`

## v2.2 Focused Validation

- Batch 2.2-A focused validation: `67 passed`, Ruff passed, Mypy passed, `git diff --check` passed
- Batch 2.2-B focused validation: `96 passed`, Ruff passed, Mypy passed, `git diff --check` passed
- Do not treat these overlapping focused-test counts as a combined suite total
- v2.2 full release gate passed with `628 passed`, Ruff, Mypy, diff-check, and Gitleaks
- v2.3 full release gate passed with `670 passed in 8.23s`, Ruff, Mypy across 106 source files, diff-check, and Gitleaks across 167 commits scanned

## Remaining Engineering Notes

### ControllerAgent / Tool Registry

`ControllerAgent` now exists as an isolated deterministic dispatcher for typed tools. It is not wired into the CLI runtime yet. Future controller work should preserve deterministic policy boundaries and avoid LLM-driven routing. Smart Router preview is also helper-only and does not execute tools.

Tool Permission and Workflow Plan contracts now document future orchestration boundaries, but they are not runtime enforcement or auto-execution paths.

### Deferred Work After v2.3

- Tool Permission and Workflow Plan contracts are not runtime-wired.
- Partial controlled package migration has been performed for RAG helpers and controller/orchestration helpers, while flat compatibility shims remain.
- Automatic Graph RAG retrieval remains deferred; v2.2 adds deterministic KnowledgeDoc seed helpers and protected hybrid explanation/context assembly only.
- Knowledge Capture remains deferred until ownership, review, and ingest boundaries are stable.
- Automatic vector-to-graph expansion and automatic retrieval-to-graph expansion remain deferred.
- Similar-Case Graph RAG and approved historical-case retrieval remain deferred after v2.3.
- Direct-input Auto Router, Agent Skill Orchestration, and LLM-assisted skill selection remain deferred after v2.3.
- The deferred Mode 3 KnowledgeDoc graph-expansion WIP remains deferred.
- Full legacy KB corpus schema migration remains deferred; existing legacy KB documents remain supported.
- Agent Skill Orchestration remains deferred; ControllerAgent does not auto-execute tools or workflows.
- Smart Router remains preview-only and is not the default CLI auto-route.
- `RAGQA` has not been replaced.
- Manual LLM/RAG smoke remains manual-only and is not part of normal CI. Targeted v2.3 manual runtime smoke was executed and recorded for Mode 3 controlled retrieval, Mode 1 event follow-up, and Mode 2 graph-grounded incident follow-up.

### Quantified Current Debt

| Area | Current measurement / status | Debt note |
|---|---|---|
| `report_followup.py` | Above the inspection threshold after protected report/rule and graph follow-up helpers | Future split candidate; do not split without a focused ownership phase |
| `tests/test_report_followup.py` | Expanded further by protected graph follow-up coverage | Large focused test file; future test-alignment debt only |
| RAG helper package shims | flat `modules/rag_*.py` compatibility paths remain | Temporary compatibility layer after `modules/rag/` migration |
| Controller package shims | flat controller/tool/policy/workflow compatibility paths remain | Temporary compatibility layer after `modules/controller/` migration |
| Tests layout | owner clusters documented, but tests remain mostly flat | Future alignment only after package ownership is stable |

### Follow-up Module Boundary

`followup_handler.py` and `report_followup.py` remain separate for now. v1.7 ownership decision: point/context follow-up stays with `followup_handler.py`, while report-aware EV/F-ID follow-up stays with `report_followup.py`. Do not unify them until Smart Router eval cases prove a single route is safe.

### Responder Size

`responder.py` owns unified report formatting and response playbooks. This keeps output consistent, but the file remains large.

Future cleanup can keep report formatting in `responder.py` while moving static playbook data into structured constants or knowledge files. Planned sequencing should follow [docs/ROADMAP.md](docs/ROADMAP.md).

### RAG Routing

`RAGQueryPlanner` supports preferred source selection for the current small knowledge base. v1.6 adds isolated metadata-aware RAG v2 helper modules for source-cited report/rule explanations, and v1.8 wires them only through protected helper paths.

Future retrieval work can decide whether to expand protected report follow-up integration while keeping `RAGQA` as the active general knowledge QA runtime. Planned sequencing should follow [docs/ROADMAP.md](docs/ROADMAP.md).

### Startup Cost

App startup may still initialize heavy RAG, embedding, and Chroma resources.

Future work should continue moving heavy components toward lazy initialization. Planned sequencing should follow [docs/ROADMAP.md](docs/ROADMAP.md).

## Out of Scope for Consolidation

- Building a large multi-agent architecture immediately
- Building a Red / Blue simulation lab during consolidation
- Supporting every real-world log format during consolidation
- Connecting to real firewall, WAF, EDR, SIEM, SOAR, or cloud policy actions

For planned future work after consolidation, see [docs/ROADMAP.md](docs/ROADMAP.md).
