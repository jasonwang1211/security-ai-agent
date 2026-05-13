# Roadmap

This roadmap describes planned development after the v1.3 Evidence and Incident Capability release.

## Current Baseline

Current release baseline: tag `v1.3.0` on `main`.

Completed:

- Unified Security Triage Report
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- Single raw auth log translation
- Log ingestion and brute-force candidate aggregation
- RAGQueryPlanner for knowledge QA
- LLMAssist as advisory-only reasoning
- Pydantic boundary types
- v1.3 Evidence and Incident Capability
- Scenario A integration coverage
- JSON Incident Report export
- Report-aware follow-up
- LLM Safety Layer
- 11 `report_explainer` KB docs
- Expanded golden smoke tests, direct log pipeline tests, and incident tests
- pytest / ruff / mypy / GitHub Actions CI

Current v1.3 quality gate:

- `python -m pytest` -> `102 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed

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

Historical goal:
Move from single-event triage toward incident-style evidence handling.

## v1.4 — Detection-as-Code Lite

Status: Next.

Goal:
Move hard-coded detection signatures toward a small, inspectable detection-as-code layer while preserving deterministic triage boundaries.

Planned:

- YAML-based detection rules
- Rule loader
- Signature metadata
- Severity, confidence, references, and MITRE technique metadata
- Migrate existing XSS / SQL Injection / Path Traversal / Command Injection signatures out of Python

## v1.5+ — Controller Agent, Evaluation, and Simulation

Status: Later.

Planned:

- Tool-calling ControllerAgent
- Tool registry
- Typed tool input/output contracts using Pydantic boundary models
- Benchmark dataset and quality evaluation
- Detection quality metrics
- Retrieval quality checks
- Metadata-driven RAG exploration
- Simulation / dashboard exploration

Important constraint:
The ControllerAgent may route work and request tools, but final triage decisions must still respect deterministic policy boundaries.

## Non-Goals

The roadmap does not include offensive automation or real enforcement actions.
All response decisions remain simulated unless explicitly redesigned in a future production-safe environment.

# 後續規劃

此 roadmap 描述 v1.3 Evidence and Incident Capability 發布後的後續開發方向。

## 目前基準

目前 release baseline：`main` 上的 tag `v1.3.0`。

已完成：

- Unified Security Triage Report
- XSS、SQL Injection、Path Traversal、Command Injection 規則式偵測
- 單筆 raw auth log translation
- Log ingestion 與 brute-force candidate aggregation
- RAGQueryPlanner knowledge QA
- LLMAssist advisory-only reasoning
- Pydantic boundary types
- v1.3 Evidence and Incident Capability
- Scenario A integration coverage
- JSON Incident Report export
- Report-aware follow-up
- LLM Safety Layer
- 11 篇 `report_explainer` KB docs
- pytest / ruff / mypy / GitHub Actions CI

目前 v1.3 quality gate：

- `python -m pytest` -> `102 passed`
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

## v1.4 — Detection-as-Code Lite / 輕量偵測即程式碼

狀態：下一階段。

目標：
將 hard-coded detection signatures 移往小型、可檢視的 detection-as-code layer，同時保留 deterministic triage boundaries。

規劃：

- YAML-based detection rules
- Rule loader
- Signature metadata
- Severity, confidence, references, and MITRE technique metadata
- 將既有 XSS / SQL Injection / Path Traversal / Command Injection signatures 從 Python 搬出

## v1.5+ — Controller Agent, Evaluation, and Simulation / 控制代理、評估與模擬

狀態：後續階段。

規劃：

- Tool-calling ControllerAgent
- Tool registry
- Typed tool input/output contracts using Pydantic boundary models
- Benchmark dataset and quality evaluation
- Detection quality metrics
- Retrieval quality checks
- Metadata-driven RAG exploration
- Simulation / dashboard exploration

重要限制：
ControllerAgent 可以負責 routing 與 tool requests，但 final triage decisions 仍必須遵守 deterministic policy boundaries。

## 非目標

Roadmap 不包含 offensive automation 或真實 enforcement actions。
除非未來另行設計 production-safe environment，所有 response decisions 都維持 simulated。
