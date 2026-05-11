# Roadmap

This roadmap describes planned development after the current unified triage and testing milestone.

## Current Baseline

Completed:

- Unified Security Triage Report
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- Single raw auth log translation
- Log ingestion and brute-force candidate aggregation
- RAGQueryPlanner for knowledge QA
- LLMAssist as advisory-only reasoning
- Pydantic boundary types
- Expanded golden smoke tests and direct log pipeline tests
- pytest / ruff / mypy / GitHub Actions CI

Current quality gate:

- `python -m pytest` → `30 passed`
- `python -m ruff check .`
- `python -m mypy app.py modules tests`

## v1.3 — Evidence and Incident Capability

Goal:
Move from single-event triage toward incident-style evidence handling.

Planned:

- Time-window aggregation
- Sequence-based findings, such as repeated failures followed by login success
- Possible Account Compromise scenario
- JSON incident report export
- MITRE ATT&CK mapping

## v1.4 — Controller Agent and Tool Registry

Goal:
Introduce a higher-level controller without weakening deterministic safety boundaries.

Planned:

- Smart input router
- ControllerAgent
- Tool registry
- Typed tool input/output contracts using Pydantic boundary models
- Safer tool-call validation

Important constraint:
The ControllerAgent may route work and request tools, but final triage decisions must still respect deterministic policy boundaries.

## v1.5+ — Evaluation, RAG Improvements, and Simulation

Goal:
Improve measurement, retrieval quality, and demo realism.

Planned:

- Small benchmark dataset for payload, log, benign, and anomaly cases
- Detection quality metrics
- Retrieval quality checks
- More realistic log formats
- Metadata-driven RAG
- Web dashboard exploration
- Red / blue simulation lab as a later, separate scope

## Non-Goals

The roadmap does not include offensive automation or real enforcement actions.
All response decisions remain simulated unless explicitly redesigned in a future production-safe environment.

# 後續規劃

本 roadmap 記錄目前 unified triage 與 testing milestone 之後的開發方向。

## 目前基準

已完成：

- Unified Security Triage Report
- Rule-based detection for XSS、SQL Injection、Path Traversal、Command Injection
- Single raw auth log translation
- Log ingestion and brute-force candidate aggregation
- RAGQueryPlanner knowledge QA
- LLMAssist advisory-only reasoning
- Pydantic boundary types
- Expanded golden smoke tests and direct log pipeline tests
- pytest / ruff / mypy / GitHub Actions CI

目前品質檢查：

- `python -m pytest` → `30 passed`
- `python -m ruff check .`
- `python -m mypy app.py modules tests`

## v1.3 — Evidence and Incident Capability

目標：
從單一事件分流，往 incident-style evidence handling 推進。

規劃：

- Time-window aggregation
- Sequence-based finding，例如多次登入失敗後接著登入成功
- Possible Account Compromise scenario
- JSON incident report export
- MITRE ATT&CK mapping

## v1.4 — Controller Agent and Tool Registry

目標：
加入更高層的 ControllerAgent，但不削弱 deterministic safety boundaries。

規劃：

- Smart input router
- ControllerAgent
- Tool registry
- 使用 Pydantic boundary models 定義 typed tool input/output contracts
- 更安全的 tool-call validation

重要限制：
ControllerAgent 可以負責路由與呼叫工具，但最終 triage decision 仍必須遵守 deterministic policy boundaries。

## v1.5+ — Evaluation, RAG Improvements, and Simulation

目標：
改善評估方式、檢索品質與展示真實感。

規劃：

- 小型 benchmark dataset
- Detection quality metrics
- Retrieval quality checks
- 更真實的 log formats
- Metadata-driven RAG
- Web dashboard exploration
- Red / blue simulation lab as later separate scope

## 非目標

此 roadmap 不包含 offensive automation 或真實 enforcement actions。
除非未來進入 production-safe redesign，否則所有 response decisions 都維持模擬性質。
