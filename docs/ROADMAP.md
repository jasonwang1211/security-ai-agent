# Roadmap

This roadmap describes planned development after the v1.9 Architecture Cleanup and Orchestration Contracts milestone.

## Current Baseline

Current release baseline: tag `v1.8.0`.

Current release target: v1.9 documentation sync on branch `v1.9-orchestration-contracts`.

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
- pytest / ruff / mypy / GitHub Actions CI

Current v1.9 quality gate:

- `python -m pytest` -> `525 passed`
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
- 525 passed quality gate

Boundary:
v1.9 is contracts-only. It does not implement Graph RAG, Knowledge Capture, LLM tool selection, runtime auto-execution, Smart Router default CLI auto-route, `RAGQA` replacement, AI attack decisions, Risk Level / Decision override, automatic rule changes, or real enforcement.

## v2.0 - Knowledge Graph Foundation / Graph RAG Groundwork

Status: Next.

Planned:

- Knowledge Graph foundation after v1.9 ownership and contract boundaries are stable
- Graph RAG groundwork as retrieval infrastructure, not a detector or policy engine
- Continued preservation of `RAGQA` unless a later phase explicitly replaces it

Deferred beyond initial v2.0 groundwork:

- Graph RAG retrieval as active runtime behavior
- Knowledge Capture implementation
- LLM graph extraction
- automatic rule modification or deployment

## Non-Goals

The roadmap does not include offensive automation or real enforcement actions.
All response decisions remain simulated unless explicitly redesigned in a future production-safe environment.

# 後續規劃

此 roadmap 描述 v1.8 Protected Runtime Wiring and Analyst UX 完成後的後續開發方向。

## 目前基準

目前 release baseline：tag `v1.8.0`。

Current release target: v1.9 documentation sync on branch `v1.9-orchestration-contracts`.

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
- pytest / ruff / mypy / GitHub Actions CI

目前 v1.9 quality gate：

- `python -m pytest` -> `525 passed`
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
- Boundary: contracts only; no Graph RAG, Knowledge Capture, LLM tool selection, runtime auto-execution, RAGQA replacement, AI verdict override, or real enforcement

## v2.0 - Knowledge Graph Foundation / Graph RAG Groundwork

- Status: next
- Knowledge Graph foundation after v1.9 ownership and contract boundaries are stable
- Graph RAG retrieval, Knowledge Capture, and LLM graph extraction remain deferred beyond v1.9
