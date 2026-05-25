# Roadmap

This roadmap describes planned development after the v2.0 Knowledge Graph Foundation milestone.

## Current Baseline

Current release baseline: tag `v1.8.0`.

Current phase: v2.0 Knowledge Graph Foundation release gate passed.

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
- 11 `report_explainer` KB docs
- YAML detection rules with schema validation and metadata
- v1.5 ControllerAgent and Tool Registry infrastructure
- v1.6 RAG v2 Foundation
- v1.7 Answer Safety / Evaluation / Smart Router Foundation
- v1.8 Protected Runtime Wiring and Analyst UX
- v1.9 Architecture Cleanup and Orchestration Contracts
- v2.0 Knowledge Graph Foundation
- pytest / ruff / mypy / GitHub Actions CI

Last full quality gate (v2.0):

- `python -m pytest` -> `585 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed
- CI includes Gitleaks secret scanning

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
- RAG v2 runtime integration and follow-up ownership decisions documented
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

Status: Release gate passed; ready to tag.

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

## Non-Goals

The roadmap does not include offensive automation or real enforcement actions.
All response decisions remain simulated unless explicitly redesigned in a future production-safe environment.

# 後續規劃

此 roadmap 描述目前 v2.0 知識圖譜基礎完成後的後續開發方向。

## 目前基準

目前 release baseline：tag `v1.8.0`。

目前里程碑：v2.0 知識圖譜基礎 release gate 已通過，準備 tag。

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
- 11 篇 `report_explainer` KB docs
- YAML detection rules、schema validation 與 rule metadata
- v1.5 ControllerAgent and Tool Registry infrastructure
- v1.6 RAG v2 Foundation
- v1.7 Answer Safety / Evaluation / Smart Router Foundation
- v1.8 Protected Runtime Wiring and Analyst UX
- v1.9 Architecture Cleanup and Orchestration Contracts
- v2.0 知識圖譜基礎
- pytest / ruff / mypy / GitHub Actions CI

Last full quality gate (v2.0):

- `python -m pytest` -> `585 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed

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
- RAG v2 runtime integration and follow-up ownership decisions documented
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

- Status: release gate 已通過，準備 tag
- 已新增圖譜型別契約、決定性圖譜建構器、唯讀查詢輔助函式，以及可序列化為 JSON 的匯出輔助函式
- 目前不新增 `rule_graph.py`；KnowledgeDoc 圖譜種子延後到 metadata 盤點後再處理
- Graph RAG retrieval、Knowledge Capture、LLM graph extraction、Neo4j / vector search、runtime orchestration、tool execution、`RAGQA` replacement，以及 detector / risk / decision override 仍維持延後
