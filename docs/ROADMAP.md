# Roadmap

This roadmap describes planned development after the v1.7 Answer Safety / Evaluation / Smart Router Foundation milestone.

## Current Baseline

Current release: tag `v1.6.0` on `main`.

Current development branch: `v1.7-answer-safety-eval-router`.

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
- pytest / ruff / mypy / GitHub Actions CI

Current v1.7 quality gate:

- `python -m pytest` -> `445 passed`
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

Status: Next.

Planned:

- Protected runtime wiring for narrow report/rule explanations
- Smart Router CLI integration only after route safety is proven
- Optional Investigation Planner after safety coverage is mature
- Analyst UX polish
- Advanced `AnswerGuardrails` only if deterministic coverage is insufficient

## v1.9 - Analyst UX and Demo Polish

Status: Later.

Planned:

- Analyst UX improvements
- Demo polish
- Dashboard / demo exploration

## Non-Goals

The roadmap does not include offensive automation or real enforcement actions.
All response decisions remain simulated unless explicitly redesigned in a future production-safe environment.

# 後續規劃

此 roadmap 描述 v1.6 RAG v2 Foundation 完成後的後續開發方向。

## 目前基準

目前 release：`main` 上的 tag `v1.6.0`。

目前 development branch: `v1.7-answer-safety-eval-router`。

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
- pytest / ruff / mypy / GitHub Actions CI

目前 v1.7 quality gate：

- `python -m pytest` -> `445 passed`
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

- protected runtime wiring
- narrow report/rule explanation integration
- optional Investigation Planner after safety coverage
- analyst UX polish

## v1.9 - Analyst UX and Demo Polish

- Analyst UX / demo polish
