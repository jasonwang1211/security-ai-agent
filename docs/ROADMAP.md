# Roadmap

This roadmap describes planned development after the v2.4 deterministic Agent Skill Orchestration implementation.

## Current Baseline

Current release baseline: tag `v2.4.0`.

Current phase: v2.4 released as `v2.4.0`.

Completed:

- Unified Security Triage Report
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- Single raw auth log translation
- Log ingestion and brute-force candidate aggregation
- RAGQueryPlanner for knowledge QA
- LLMAssist as advisory-only reasoning
- Pydantic boundary types
- v1.3 Evidence and Incident Capability
- v1.4 Detection-as-Code Lite
- Scenario A integration coverage
- JSON Incident Report export
- Report-aware follow-up
- LLM Safety Layer
- v1.3 initially delivered 11 `report_explainer` KB docs; v2.2 expands the live report-explainer corpus to 20 documents
- YAML detection rules with schema validation and metadata
- v1.5 ControllerAgent and Tool Registry infrastructure
- v1.6 RAG v2 Foundation
- v1.7 Answer Safety / Evaluation / Smart Router Foundation
- v1.8 Protected Runtime Wiring and Analyst UX
- v1.9 Architecture Cleanup and Orchestration Contracts
- v2.0 Knowledge Graph Foundation
- v2.1 Graph-Backed Explanation MVP
- v2.2 Curated RAG Graph Seed Foundation
- v2.3 Controlled Retrieval and Structured Follow-Up
- v2.4 Deterministic Agent Skill Orchestration Runtime
- pytest / ruff / mypy / GitHub Actions CI

Last full quality gate (v2.4):

- `python -m pytest` -> `693 passed in 14.72s`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed, `108 source files`
- `git diff --check` -> passed
- Gitleaks -> passed, no leaks found across 171 commits scanned using `gitleaks detect --source . --verbose --redact`

Focused v2.4-A deterministic validation already completed:

- Pytest: `110 passed in 1.64s`
- Ruff: passed
- Mypy: passed across 108 source files
- `git diff --check`: passed
- Mojibake scan over v2.4-A touched files: no known corrupted fragments found

Focused v2.2 validation already completed:

- Batch 2.2-A focused validation: `67 passed`, Ruff passed, Mypy passed, `git diff --check` passed
- Batch 2.2-B focused validation: `96 passed`, Ruff passed, Mypy passed, `git diff --check` passed

## v1.3 — Evidence and Incident Capability

Status: Completed.

Delivered:

- Evidence / Finding / Incident schemas
- Stable EV-ID and F-ID references
- Time-window authentication sequence correlation
- `possible_account_compromise` scenario with `HIGH / MONITOR`
- JSON Incident Report export
- Report-aware follow-up
- Evidence-grounded LLMAssist with safety guardrails
- Scenario A mixed auth log integration coverage
- 11 `report_explainer` KB docs
- 102 passed quality gate

## v1.4 — Detection-as-Code Lite

Status: Completed.

Delivered:

- YAML-based deterministic detection rules
- `DetectionRule` Pydantic schema
- YAML rule loader with schema validation
- Detector adapter using YAML rules as the primary path
- XSS / SQL Injection / Path Traversal / Command Injection signatures migrated to YAML
- Rule metadata for IDs, source paths, severity, confidence, MITRE techniques, and references
- Hard-coded signatures retained as conservative fallback
- 141 passed quality gate

Boundary:
v1.4 does not add ML detection, LLM-generated rules, Sigma/YARA compatibility, production SIEM integration, or real enforcement.

## v1.5 - ControllerAgent and Tool Registry

Status: Completed on `v1.5-controller-agent`.

Delivered:

- Typed `ToolSpec` contracts and controller boundary models
- `ToolRegistry` skeleton
- Skill Catalog with exactly six v1.5 wrapper skill specs
- Thin Skill Wrappers for existing local capabilities
- Deterministic `ControllerAgent` dispatch by explicit route/tool name
- Default route map with explicit skill routes and CLI mode hints
- ControllerAgent unit tests and integration-style tests
- 240 passed quality gate

Boundary:
v1.5 does not add Auto Route, Smart Router, LLM-driven routing, Investigation Planner, Rule Explainer, or CLI wiring. Existing CLI behavior remains unchanged.

## v1.6 - RAG v2 Foundation

Status: Completed on `v1.6-rag-v2-foundation`.

Delivered:

- RAG v2 boundary types: `AnswerWithSources`, `SourceCitation`, `RAGRetrievalPlan`, and `ExtractedIds`
- Frontmatter metadata for the 11 `report_explainer` docs
- Rule-based RAG intent classification
- Exact ID extraction / lookup helpers for EV-ID, F-ID, INC-ID, rule IDs, and MITRE technique IDs
- Metadata-aware retrieval planner
- Source assembly from metadata candidates into source-cited answers
- Deterministic Report Explainer v2 and Rule Explainer v2 helpers
- 366 passed quality gate

Boundary:
v1.6 does not add AnswerGuardrails, Smart Router, Investigation Planner, LLM-based routing, LLM generation, or replacement of the existing `RAGQA` runtime. Existing CLI behavior remains unchanged.

## v1.7 - Answer Safety, Evaluation, and Smart Router

Status: Foundation completed on `v1.7-answer-safety-eval-router`.

Delivered:

- Small regression eval cases for answer safety, report QA, router cases, and payload detection
- Deterministic AnswerGuardrails foundation
- Deterministic Evaluation Runner foundation
- Isolated rule-based Smart Router foundation
- RAG v2 protected-wiring strategy and follow-up ownership decisions documented
- CI Gitleaks secret scanning
- Reusable log ingestion runner moved into `modules/`
- 445 passed quality gate

Boundary:
Smart Router is not CLI-wired yet. v1.7 does not add LLM-based routing, an LLM final verdict, RAGQA replacement, Investigation Planner, or real enforcement.

## v1.8 - Protected Runtime Wiring and Analyst UX Polish

Status: Release-ready foundation for tag `v1.8.0` on `main`.

Delivered:

- Protected report/rule explanation helpers through `report_followup.py`
- AnswerGuardrails-protected fallback behavior for unsafe helper output
- Smart Router preview mode that shows route decisions without executing tools
- Deterministic analyst follow-up suggestions
- 487 passed quality gate

Boundary:
v1.8 does not replace `RAGQA`, make Smart Router the default CLI path, add LLM routing, implement Investigation Planner, or perform real enforcement.

## v1.9 - Architecture Cleanup and Orchestration Contracts

Status: Release-ready documentation and contract milestone.

Delivered:

- `docs/v1.9-spec.md` detailed design source of truth
- Architecture ownership map
- ADR foundation
- Tool Permission Contract and tests
- Workflow Plan Contract and tests
- Testing Strategy documentation
- Package Migration Plan
- Controlled RAG helper migration into `modules/rag/` with flat compatibility shims
- Controlled controller/orchestration migration into `modules/controller/` with flat compatibility shims
- Manual LLM/RAG smoke checklist documented as manual-only, not CI, and not executed
- quality gate passed before v2.0 expansion

Boundary:
v1.9 keeps contracts separate from runtime automation. It does not implement Graph RAG, Knowledge Capture, Agent Skill Orchestration runtime, LLM tool selection, runtime auto-execution, Smart Router default CLI auto-route, `RAGQA` replacement, AI attack decisions, Risk Level / Decision override, automatic rule changes, or real enforcement.

## v2.0 - Knowledge Graph Foundation

Status: Released as `v2.0.0`.

Delivered:

- `docs/v2.0-spec.md` as the detailed boundary source of truth
- typed graph contracts in `modules/graph/types.py`
- deterministic `build_graph_snapshot(...)` from structured `Incident` objects and explicitly provided `DetectionRule` objects
- read-only graph lookup helpers over in-memory `GraphSnapshot` objects
- JSON-serializable snapshot export helpers
- 2A-3 decision: no `rule_graph.py` now; KnowledgeDoc graph seeding is deferred until a metadata audit

Boundary:

v2.0 graph helpers are evidence/context structure, not detection authority. They do not load YAML or files, infer relationships from free text, call Chroma/Ollama/LLMs, execute tools, replace `RAGQA`, replace the Rule-Based Detector, or change Risk Level / Decision.

Deferred beyond v2.0:

- Graph RAG retrieval as active runtime behavior
- Knowledge Capture implementation
- LLM graph extraction
- Neo4j or vector search
- runtime agent orchestration
- `RAGQA` replacement
- detector / risk / decision override by graph or LLM
- automatic rule modification or deployment

## v2.1 - Graph-Backed Explanation MVP

Status: Release gate passed in the previous milestone.

Delivered:

- `modules/graph/explainers.py` as the canonical graph-backed explanation helper
- `explain_graph_reference(snapshot, reference_id) -> AnswerWithSources`
- exact `EV-*`, `F-*`, rule ID, and `INC-*` explanations from explicit graph nodes and edges
- graph provenance represented through existing `SourceCitation.metadata`, without expanding the RAG schema
- protected adapter `explain_graph_followup_protected(...)` in `modules/report_followup.py`
- rule ID normalization so `CMD-001` and `DETECTION_RULE:CMD-001` produce stable outward-facing `rule_ids`
- Scenario A focused coverage showing `EV-003` explicitly supports `F-001` while `Decision` remains `MONITOR`

Boundary:

v2.1 is graph-backed explanation, not Graph RAG retrieval. It is a protected helper and tested integration capability, not CLI auto-routing or a new `app.py` mode. It does not implement Knowledge Capture, LLM graph extraction, Neo4j/NetworkX, vector search, runtime orchestration, tool execution, `RAGQA` replacement, graph-driven Risk Level / Decision changes, or real enforcement.

## v2.2 - Curated RAG Graph Seed Foundation

Status: Released as `v2.2.0`.

Delivered:

- Promoted 9 reviewed Traditional Chinese report-explainer KB documents into live `knowledge/blue_team/report_explainer/`.
- Expanded live report-explainer coverage from 11 to 20 documents.
- Added minimal typed metadata support for `title`, `review_status`, `finding_types`, `evidence_types`, `decision_labels`, and `tags`.
- Promoted documents use `schema_version: v2.2-live1` and `review_status: approved_for_runtime_promotion`.
- Five authentication documents remain retrieval/explanation context only and do not define graph-seed edges.
- Four verified rule explainers retain reviewed attack/rule metadata for XSS / `XSS-001` / `MEDIUM` / simulated `MONITOR`, SQL Injection / `SQLI-001` / `HIGH` / simulated `BLOCK`, Path Traversal / `PATH-001` / `HIGH` / simulated `BLOCK`, and Command Injection / `CMD-001` / `HIGH` / simulated `BLOCK`.
- Resolved references were added before live promotion.
- Added `modules/graph/knowledge_doc_seed.py`.
- `build_knowledge_doc_seed(...)` accepts parsed `KnowledgeDocMetadata` plus explicitly supplied `DetectionRule` objects.
- Seed candidates must be approved for runtime promotion and cross-validated against supplied detection rules.
- Retrieval-only documents with empty attack/rule metadata produce no seed graph output.
- Seed helper creates only `KNOWLEDGE_DOC -> ATTACK_TYPE` through `RELATED_TO_ATTACK` and `KNOWLEDGE_DOC -> DETECTION_RULE` through `MAPS_TO_RULE`.
- Added `combine_hybrid_explanation_protected(...)` in `modules/report_followup.py`.
- Hybrid helper combines already-built graph context and already-built curated knowledge context, preserves citations, and applies existing deterministic guardrails.
- Scenario A authentication hybrid context keeps `Decision` simulated `MONITOR`.
- Command Injection hybrid context keeps `Decision` simulated `BLOCK`.

Boundary:

v2.2 implements protected hybrid explanation/context assembly using explicit graph context plus curated knowledge source context. It does not implement automatic Graph RAG retrieval, vector-to-graph expansion, Knowledge Capture, LLM graph extraction, `RAGQA` replacement, CLI auto-route, graph or LLM Risk Level / Decision override, tool execution, real enforcement, or real monitoring deployment. Existing legacy KB documents remain supported, and full corpus schema migration is deferred.

Deferred beyond v2.2:

- Automatic Graph RAG retrieval
- Vector-to-graph expansion
- Knowledge Capture implementation
- LLM graph extraction
- Full legacy KB schema migration
- Runtime wiring or CLI auto-route for hybrid explanations

## v2.3 - Controlled Retrieval and Structured Follow-Up

Status: Released as `v2.3.0`.

Delivered:

- Mode 3 controlled approved-source retrieval before vector fallback for reviewed targets including SQL Injection, `CMD-001`, and `success_after_failures`.
- Protected Mode 3 return path with Traditional Chinese safety boundary, internal metadata-label suppression, canonical visible RAG / LLM terminology, and deterministic final-authority wording.
- Mode 1 stores `ActiveEventContext` with only facts produced by the current payload-analysis flow.
- Mode 4 current-event follow-up covers classification reasoning, matched rule/signature evidence, simulated Decision boundary, exploitation uncertainty, and defensive investigation/remediation guidance.
- Mode 2 qualifying authentication logs create structured `Incident`, `Evidence`, and `Finding` values through deterministic correlation.
- Scenario A stores `ActiveAuthIncidentContext`, builds an explicit current-incident `GraphSnapshot`, and shows a structured summary with `INC-20260501-001`, `EV-003`, `F-001`, `HIGH`, and simulated `MONITOR`.
- Mode 4 graph-grounded authentication incident follow-up explains `EV-003`, the explicit `EV-003` / `F-001` support relationship, simulated `MONITOR`, compromise uncertainty, and investigation next steps.
- Non-qualifying Mode 2 log analysis clears stale structured context.

Manual smoke:

- Command Injection payload `test; rm -rf /tmp/test` retained `Command Injection`, `HIGH`, `BLOCK`, matched signatures, and simulation notice. Follow-up confirmed `BLOCK` is simulated and a rule match does not prove successful execution.
- Scenario A log `demo_logs\scenario_a_mixed_auth.log` produced `INC-20260501-001`, `Possible Account Compromise`, `HIGH`, simulated `MONITOR`, `EV-003`, and `F-001`. Follow-up used explicit current `GraphSnapshot` facts and did not claim confirmed intrusion or real monitoring deployment.

Boundary:

v2.3 includes graph-grounded follow-up for the current structured authentication incident only. It is not Similar-Case Graph RAG, LLM-generated graph reasoning, automatic historical-case retrieval, Knowledge Capture, event write-back, Auto Router, Skill Orchestration, LLM-assisted skill selection, automatic vector-to-graph expansion, restored Mode 3 KnowledgeDoc graph expansion, real enforcement, real monitoring deployment, or RAG/LLM override of deterministic `Risk Level` or `Decision`.

## v2.4 - Deterministic Agent Skill Orchestration Runtime

Status: Released as `v2.4.0`.

Delivered:

- Direct user input is now the primary CLI interaction path.
- Users can enter suspicious payloads, authentication log paths, active-context follow-up questions, or general security knowledge questions without manually selecting Mode 1 / 2 / 3 / 4 first.
- `menu` preserves the legacy four-mode interface as a debug/demo fallback.
- Deterministic routing and invocation now covers `AnalyzePayloadSkill`, `AnalyzeAuthenticationLogSkill`, `ExplainActiveEventSkill`, `ExplainActiveIncidentSkill`, and `KnowledgeQASkill`.
- Skill selection is deterministic, not LLM-selected.
- `ToolPolicy` permits approved read/analysis flows and keeps future write-capable behavior blocked or approval-required.
- `ActiveEventContext` and `ActiveAuthIncidentContext` are preserved for structured current-event/current-incident follow-up precedence.
- General knowledge Q&A may run while an active context exists and does not overwrite that structured context.
- The runtime reuses v2.3 event-grounded payload follow-up, graph-grounded current authentication incident follow-up, and protected controlled knowledge Q&A.

Focused validation:

- Pytest: `110 passed in 1.64s`
- Ruff: passed
- Mypy: passed across 108 source files
- `git diff --check`: passed
- Mojibake scan over v2.4-A touched files: no known corrupted fragments found
- Manual runtime smoke passed for direct payload input, direct authentication log input, active follow-up, protected SQL Injection knowledge Q&A, and legacy `menu` fallback.

Boundary:

v2.4 does not replace detector, incident, graph, or protected RAG authority. It does not implement or release LLM-assisted skill selection, `RetrieveSimilarCaseSkill`, executable `DraftCaseCaptureSkill`, Similar-Case Graph RAG, historical-case retrieval, Knowledge Capture or event write-back, automatic live ingestion, real firewall/WAF/EDR/account enforcement, real monitoring deployment, or RAG/LLM override of deterministic `Risk Level` or `Decision`. Any future write-capable capture skill must require explicit approval and human review before live ingestion.
## v2.7 - Completed / Demo-Ready: AI Advisory and Safe Resource Exhaustion Demo

v2.7 is documented as demo-ready with the deterministic safety boundary preserved:

- AI Advisory / Evidence Gap capability is available as analyst context.
- RAG knowledge expansion covers Resource Exhaustion, HTTP/2 DoS, and CVE terminology.
- AI Analyst Brief summarizes deterministic advisory context without taking final authority.
- Safe synthetic Resource Exhaustion demo scenario is available for manual UI smoke.

Safety boundary remains unchanged: detector authority is rule-based, Risk Level / Decision are deterministic, `BLOCK` / `MONITOR` / `ALLOW` are simulated, advisory layers do not override current results, no real enforcement occurs, and no exploit, PoC, or traffic generation is provided.

## v2.8 - Deferred Larger Work

Candidate follow-up work moved beyond v2.7:

- Richer analyst timeline.
- More incident scenarios.
- Deeper graph and case memory integration.
- Optional report export polish.

## Non-Goals

The roadmap does not include offensive automation or real enforcement actions.
All response decisions remain simulated unless explicitly redesigned in a future production-safe environment.

# 後續規劃

本 roadmap 說明 v2.4 deterministic Agent Skill Orchestration implementation 之後的規劃。

## 目前基準

目前 release baseline：tag `v2.4.0`。
目前里程碑：v2.4 已發布為 `v2.4.0`。
已完成：

已完成：

- Unified Security Triage Report
- XSS、SQL Injection、Path Traversal、Command Injection 規則式偵測
- 單筆 raw auth log translation
- Log ingestion 與 brute-force candidate aggregation
- RAGQueryPlanner knowledge QA
- LLMAssist advisory-only reasoning
- Pydantic boundary types
- v1.3 Evidence and Incident Capability
- v1.4 Detection-as-Code Lite
- Scenario A integration coverage
- JSON Incident Report export
- Report-aware follow-up
- LLM Safety Layer
- v1.3 initially delivered 11 篇 `report_explainer` KB docs；v2.2 將 live report-explainer corpus 擴充為 20 篇文件
- YAML detection rules、schema validation 與 rule metadata
- v1.5 ControllerAgent and Tool Registry infrastructure
- v1.6 RAG v2 Foundation
- v1.7 Answer Safety / Evaluation / Smart Router Foundation
- v1.8 Protected Runtime Wiring and Analyst UX
- v1.9 Architecture Cleanup and Orchestration Contracts
- v2.0 知識圖譜基礎
- v2.1 Graph-Backed Explanation MVP
- v2.2 Curated RAG Graph Seed Foundation
- v2.3 Controlled Retrieval and Structured Follow-Up
- v2.4 Deterministic Agent Skill Orchestration Runtime
- pytest / ruff / mypy / GitHub Actions CI

Last full quality gate (v2.3):

- `python -m pytest` -> `670 passed in 8.23s`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed，`99 source files`
- `git diff --check` -> passed
- Gitleaks -> passed，no leaks found，167 commits scanned

v2.2 focused validation:

- Batch 2.2-A：`67 passed`，Ruff、Mypy、`git diff --check` 通過
- Batch 2.2-B：`96 passed`，Ruff、Mypy、`git diff --check` 通過

## v1.3 — Evidence and Incident Capability / 證據與事件能力

狀態：已完成。

已交付：

- Evidence / Finding / Incident schemas
- Stable EV-ID and F-ID references
- Time-window authentication sequence correlation
- `possible_account_compromise` scenario with `HIGH / MONITOR`
- JSON Incident Report export
- Report-aware follow-up
- Evidence-grounded LLMAssist with safety guardrails
- Scenario A mixed auth log integration coverage
- 11 篇 `report_explainer` KB docs
- 102 passed quality gate

## v1.4 — Detection-as-Code Lite / YAML 規則式偵測

狀態：已完成。

已交付：

- YAML-based deterministic detection rules
- `DetectionRule` Pydantic schema
- YAML rule loader with schema validation
- Detector adapter using YAML rules as the primary path
- XSS / SQL Injection / Path Traversal / Command Injection signatures migrated to YAML
- Rule metadata: IDs、source paths、severity、confidence、MITRE techniques、references
- Hard-coded signatures retained as conservative fallback
- 141 passed quality gate

邊界：
v1.4 不包含 ML detection、LLM-generated rules、Sigma/YARA compatibility、production SIEM integration 或 real enforcement。

## v1.5 - ControllerAgent and Tool Registry / ControllerAgent 與 Tool Registry

狀態：已完成。

規劃：

- Typed `ToolSpec` contracts and `ToolRegistry`
- Deterministic `ControllerAgent` dispatch by explicit route/tool name
- Six wrapper skills
- No Auto Route, Smart Router, or LLM-driven tool selection
- 240 passed quality gate

重要限制：
ControllerAgent 可以負責 routing 與 tool requests，但 final triage decisions 仍必須遵守 deterministic policy boundaries。

## 非目標

Roadmap 不包含 offensive automation 或真實 enforcement actions。
除非未來另行設計 production-safe environment，所有 response decisions 都維持 simulated。
## v1.6 - RAG v2 Foundation / RAG v2 基礎

Status: Completed on `v1.6-rag-v2-foundation`.

- RAG v2 boundary types: `AnswerWithSources`, `SourceCitation`, `RAGRetrievalPlan`, `ExtractedIds`
- 11 份 `report_explainer` docs 的 frontmatter metadata
- rule-based RAG intent classification
- EV-ID / F-ID / INC-ID / rule ID / MITRE technique ID extraction 與 lookup helpers
- metadata-aware retrieval planner
- SourceCitation / AnswerWithSources source assembly
- deterministic Report Explainer v2 與 Rule Explainer v2 helpers
- 366 passed quality gate
- 不包含 AnswerGuardrails、Smart Router、Investigation Planner、LLM-based routing，也未取代既有 `RAGQA` runtime

## v1.7 - Answer Safety, Evaluation, and Smart Router / 答案安全、評估與 Smart Router

Status: Foundation completed.

- eval_cases/ small regression datasets
- deterministic AnswerGuardrails
- deterministic Evaluation Runner
- isolated rule-based Smart Router
- 已記錄 RAG v2 protected-wiring strategy 與 follow-up ownership decisions
- Boundary: Smart Router is not CLI-wired; no LLM-based routing; RAGQA is not replaced

## v1.8 - Protected Runtime Wiring and Analyst UX Polish

- Status: release-ready foundation
- protected report/rule explanation helpers
- guarded fallback behavior
- Smart Router preview only; no automatic tool execution
- deterministic analyst follow-up suggestions
- Boundary: `RAGQA` is not replaced; no LLM routing; no real enforcement

## v1.9 - Architecture Cleanup and Orchestration Contracts

- Status: release-ready documentation and contract milestone
- architecture ownership map
- ADR foundation
- Tool Permission Contract and tests
- Workflow Plan Contract and tests
- Testing Strategy documentation
- Package Migration Plan
- Controlled `modules/rag/` and `modules/controller/` migrations with flat compatibility shims
- Manual LLM/RAG smoke checklist documented as manual-only, not CI, and not executed
- Boundary: contracts stay separate from runtime automation; no Graph RAG, Knowledge Capture, Agent Skill Orchestration runtime, LLM tool selection, runtime auto-execution, RAGQA replacement, AI verdict override, or real enforcement

## v2.0 - 知識圖譜基礎

- Status: 已發布為 `v2.0.0`
- 已新增圖譜型別契約、決定性圖譜建構器、唯讀查詢輔助函式，以及可序列化為 JSON 的匯出輔助函式
- 目前不新增 `rule_graph.py`；KnowledgeDoc 圖譜種子延後到 metadata 盤點後再處理
- Graph RAG retrieval、Knowledge Capture、LLM graph extraction、Neo4j / vector search、runtime orchestration、tool execution、`RAGQA` replacement，以及 detector / risk / decision override 仍維持延後

## v2.1 - Graph-Backed Explanation MVP

- Status: release gate 已於前一里程碑通過
- 新增 `modules/graph/explainers.py` 與 `explain_graph_reference(snapshot, reference_id) -> AnswerWithSources`
- 支援 EV-ID、F-ID、rule ID 與 INC-ID 的明確圖譜關係解釋，僅跟隨既有節點與邊
- 圖譜 provenance 透過既有 `SourceCitation.metadata` 表示，沒有擴充 RAG schema
- 新增 `explain_graph_followup_protected(...)`，讓 graph-backed answer 通過既有 `AnswerGuardrails`
- Scenario A 覆蓋 `EV-003` 明確支援 `F-001`，且 `Decision` 維持 `MONITOR`
- Boundary: 這不是 Graph RAG retrieval，也不是 CLI auto-routing、`app.py` 新模式、Knowledge Capture、LLM graph extraction、Neo4j / NetworkX、vector search、runtime orchestration、tool execution、`RAGQA` replacement、Risk Level / Decision override 或 real enforcement

## v2.2 - Curated RAG Graph Seed Foundation

- Status: 已發布為 `v2.2.0`
- 9 篇 reviewed Traditional Chinese report-explainer KB 文件已提升到 live `knowledge/blue_team/report_explainer/`
- live report-explainer coverage 從 11 篇擴充到 20 篇
- 新增 `title`、`review_status`、`finding_types`、`evidence_types`、`decision_labels`、`tags` 的最小 typed metadata 支援
- `build_knowledge_doc_seed(...)` 只接收 parsed `KnowledgeDocMetadata` 與明確提供的 `DetectionRule` objects
- reviewed graph seed candidates 只從 `attack_types` / `rule_ids` 產生，並需通過 explicit `DetectionRule` cross-validation
- retrieval-only authentication docs 不產生 graph seed output
- seed helper 只建立 `RELATED_TO_ATTACK` 與 `MAPS_TO_RULE` 兩種邊
- `combine_hybrid_explanation_protected(...)` 只組合已建立的 graph context 與 curated knowledge context，保留 citations，並套用既有 deterministic guardrails
- Scenario A authentication hybrid context 的 `Decision` 維持 simulated `MONITOR`
- Command Injection hybrid context 的 `Decision` 維持 simulated `BLOCK`
- Boundary: v2.2 不包含 automatic Graph RAG retrieval、vector-to-graph expansion、Knowledge Capture、LLM graph extraction、`RAGQA` replacement、CLI auto-route、Risk Level / Decision override、tool execution、real enforcement 或 real monitoring deployment
