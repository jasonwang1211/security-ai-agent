# AI-Assisted Blue-Team Security Triage Prototype

[![CI](https://github.com/jasonwang1211/security-ai-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/jasonwang1211/security-ai-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A hybrid blue-team security triage prototype: deterministic rule-based detection as the safety floor, with LLM and RAG layers used only for explanation and context. The LLM can suggest, but it never overrides the final system verdict. Local-first, defensive-only, and designed for academic SOC-style analysis.

[English](#english) | [繁體中文](#繁體中文)

## English

This project helps analysts review suspicious payloads, translate individual raw log lines, ingest and aggregate log files, ask RAG-based security knowledge questions, and read results through a unified `Security Triage Report`.

The system is a defensive academic prototype. It does not attack real targets or control real security infrastructure.

For detailed evaluation notes and CLI excerpts, see:

- [Demo & Evaluation Report](REPORT.md)
- [Demo Outputs](demo_outputs.md)

### The Problem

SOC-style triage has two common failure modes:

- Pure rule-based detection is stable, but misses contextual or behavior-based signals.
- Pure LLM-based detection is flexible, but can hallucinate and should not be trusted with blocking decisions.

This project explores a hybrid path: deterministic detection and policy produce the final verdict, while LLM and RAG layers explain, contextualize, and support analyst review.

### Key Features

| Layer | Component | Role |
|---|---|---|
| Detection | Rule-Based Detector + YAML Rules | Deterministic XSS, SQL Injection, Path Traversal, and Command Injection detection using YAML-based Detection-as-Code rules. |
| Triage | TriagePolicy | Risk scoring and simulated `BLOCK` / `MONITOR` / `ALLOW` decisions. |
| Pipeline | Log Pipeline | Parses, normalizes, aggregates, and adapts log inputs. |
| Knowledge | RAGQueryPlanner + RAG QA | Local defensive knowledge retrieval and explanation. |
| Assist | LLMAssist | Advisory reasoning only; it never overrides the final verdict. |
| Output | Security Triage Report | Unified report format across payload and log flows. |
| Incident | Evidence / Incident Capability | Stable EV-ID / F-ID evidence handling, sequence correlation, JSON Incident export, and report-aware follow-up. |

### Non-Goals

This prototype deliberately does not:

- Attack real systems or external targets.
- Execute real firewall, WAF, EDR, SIEM, SOAR, or cloud policy actions.
- Let LLM output override deterministic rule-based or policy decisions.
- Treat RAG retrieval as a primary detection layer.
- Replace production security monitoring systems.

`BLOCK`, `MONITOR`, and `ALLOW` are simulated training decisions only.

### Current Flow

```text
User Input
-> CLI Mode Handler
-> SecurityAgent
-> Rule-Based Detection / Log Pipeline / RAGQueryPlanner
-> TriagePolicy
-> LLMAssist
-> Unified Security Triage Report
```

Role separation:

- Rule-Based Detector, Log Pipeline, and TriagePolicy are deterministic.
- RAGQueryPlanner and RAG QA support knowledge retrieval and explanation.
- LLMAssist is advisory only.
- Unified Security Triage Report is the final output format.

### System Architecture

![English architecture diagram](docs/architecture_en.png)

Core modules:

- `app.py`: interactive CLI entry point
- `modules/mode_handlers.py`: CLI mode orchestration
- `modules/agent.py`: `SecurityAgent` coordination layer
- `modules/detector.py`: rule-based payload detection
- `modules/triage_policy.py`: risk, decision, and simulated defense policy
- `modules/llm_assist.py`: optional LLM-assisted explanation and suspicious behavior advice
- `modules/log_pipeline.py`: raw log parsing, normalization, aggregation, adaptation, and translation
- `modules/rag_query_planner.py`: RAG query planning and source preference selection
- `modules/rag_qa.py`: local knowledge retrieval and answer generation
- `modules/types.py`: Pydantic boundary types

### v1.3 Evidence and Incident Capability

v1.3 moves the prototype from single-event triage toward incident-style evidence handling:

- Evidence / Finding / Incident Pydantic schemas
- Stable EV-ID and F-ID references
- Time-window authentication sequence correlation
- `possible_account_compromise` finding
- JSON Incident Report export
- Report-aware follow-up helper
- Evidence-grounded LLMAssist with guardrails
- Scenario A mixed auth log integration test
- 11 `report_explainer` KB docs

Boundaries:

- `possible_account_compromise` is suspicious, not confirmed compromise.
- v1.3 uses `HIGH / MONITOR`, not automatic `BLOCK`.
- LLMAssist remains advisory only.
- Final verdict remains deterministic and policy-controlled.
- No real enforcement actions are performed.

### v1.4 Detection-as-Code Lite

v1.4 moves payload signatures into deterministic YAML detection rules while preserving existing detector behavior:

- YAML-based detection rules under `detections/blue_team/`
- `DetectionRule` Pydantic schema
- YAML rule loader with schema validation
- Detector adapter using YAML as the primary detection path
- XSS / SQL Injection / Path Traversal / Command Injection migrated to YAML
- Rule metadata exposed: rule IDs, source paths, severity, confidence, MITRE techniques, and references
- Hard-coded signatures remain as a conservative fallback
- Current test gate: `141 passed`

Boundaries:

- Detection remains deterministic and rule-based.
- This is not ML anomaly detection.
- Rules are not generated by LLMs.
- No real firewall, WAF, EDR, SIEM, SOAR, or cloud enforcement is performed.
- YAML metadata does not override `TriagePolicy`.

### CLI Modes

```text
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

### Testing And Quality Checks

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Run tests, lint, and gradual typing checks:

```powershell
python -m pytest
python -m ruff check .
python -m mypy app.py modules tests
```

Current expected test result: `141 passed`.

The test suite includes expanded golden smoke tests, direct consolidated log pipeline tests, Pydantic boundary model tests, incident/export/follow-up/guardrail tests, and Scenario A integration coverage for a mixed authentication log. Deterministic tests do not start the full app or initialize RAGQA, Chroma, embeddings, Torch, Ollama, ChatOllama, or local LLM clients. GitHub Actions CI runs the same quality gate.

### Local Model Prerequisites

Ollama should be installed and running locally before using the CLI.

Required local models:

- `qwen2.5:7b`
- `gemma4:e4b`

Exact model names can be changed in `config.py`.

### How To Run

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ingest_knowledge.py
python app.py
```

### Current Status

Current working branch:

```text
main
```

Current release: tag `v1.4.0` on `main`

Completed:

- Unified `Security Triage Report`
- Raw log translation and brute-force candidate aggregation
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- `RAGQueryPlanner`
- Pydantic boundary types for gradual controller and tool registry work
- v1.3 Evidence and Incident Capability, including stable EV-ID/F-ID contracts, `possible_account_compromise` correlation, JSON Incident Report export, report-aware follow-up, LLMAssist guardrails, Scenario A integration coverage, and 11 `report_explainer` KB docs
- v1.4 Detection-as-Code Lite, including YAML rules, schema validation, detector adapter, rule metadata, and hard-coded fallback
- Expanded golden smoke tests, direct log pipeline tests, focused boundary model tests, `pytest`, `ruff`, lenient `mypy`, and GitHub Actions CI

### Further Reading

- [Technical Notes](docs/TECH_NOTES.md) — Engineering deep-dive covering Detection-as-Code, Evidence/Incident modeling, LLM guardrails, MITRE metadata, and testing strategy.
- [Roadmap](docs/ROADMAP.md) — Version plan and future milestones.
- [Architecture Debt Journal](ARCHITECTURE_DEBT.md) — Engineering consolidation notes.
- [Demo & Evaluation Report](REPORT.md) — Demo walkthrough and verification.

### Roadmap

**✅ v1.3 — Evidence and Incident Capability** (Completed)

See [docs/ROADMAP.md](docs/ROADMAP.md) for delivered items.

**✅ v1.4 — Detection-as-Code Lite** (Completed)

- YAML-based detection rules
- `DetectionRule` schema and YAML rule loader
- Detector adapter using YAML as the primary detection path
- Severity, confidence, references, and MITRE technique metadata
- XSS / SQL Injection / Path Traversal / Command Injection migrated to YAML
- Hard-coded signatures retained as conservative fallback

**📋 v1.5+ — Controller Agent, Tool Registry, Evaluation, and Dashboard**

- Tool-calling ControllerAgent and tool registry
- Benchmark dataset and quality evaluation
- Web dashboard / demo exploration

For the full plan, see [docs/ROADMAP.md](docs/ROADMAP.md).

## 繁體中文

這是一個混合式藍隊安全分流原型：以「可重現的規則式偵測」作為安全地板，LLM 與 RAG 只負責解釋、補充脈絡與輔助分析。LLM 可以提出建議，但不能覆蓋最終系統判定。本專案採本地優先、防禦導向設計，適合學術展示與 SOC-style 分析流程。

### 專案簡介

本專案協助分析可疑 payload、轉換單筆原始日誌、匯入並聚合日誌檔案、回答以 RAG 為基礎的資安知識問題，並以統一 Security Triage Report 呈現結果。

這是一個防禦導向的學術原型，不會攻擊真實目標，也不會控制真實安全基礎設施。

詳細評估紀錄與 CLI 範例可參考：

- [Demo & Evaluation Report](REPORT.md)
- [Demo Outputs](demo_outputs.md)

### 問題背景

SOC-style 事件分流常見兩個問題：

- 純規則式偵測穩定，但容易漏掉需要上下文判讀的行為型訊號。
- 純 LLM 偵測彈性高，但可能幻覺，不適合直接決定封鎖或放行。

本專案採混合式設計：由 deterministic detection 與 policy 產生最終判定，LLM 與 RAG 只負責解釋、脈絡補充與輔助分析。

### 主要功能

| 層級 | 元件 | 說明 |
|---|---|---|
| Detection | Rule-Based Detector + YAML Rules | 以 YAML-based Detection-as-Code 規則進行 XSS、SQL Injection、Path Traversal、Command Injection 的 deterministic 偵測。 |
| Triage | TriagePolicy | 負責風險評估與模擬 `BLOCK` / `MONITOR` / `ALLOW` 決策。 |
| Pipeline | Log Pipeline | 解析、正規化、聚合並轉接日誌輸入。 |
| Knowledge | RAGQueryPlanner + RAG QA | 提供本地防禦知識檢索與解釋。 |
| Assist | LLMAssist | 只提供輔助推理，不覆蓋最終系統判定。 |
| Output | Security Triage Report | 在 payload 與 log flow 中提供統一報告格式。 |

### 非目標

本 prototype 明確不做以下事情：

- 不攻擊真實系統或外部目標。
- 不執行真實 firewall、WAF、EDR、SIEM、SOAR 或 cloud policy 動作。
- 不讓 LLM 輸出覆蓋 deterministic rule-based 或 policy 決策。
- 不把 RAG 檢索當作主要偵測層。
- 不取代正式 production security monitoring system。

`BLOCK`、`MONITOR`、`ALLOW` 都是模擬訓練決策。

### 目前流程

```text
使用者輸入
-> CLI 模式處理器
-> SecurityAgent
-> 規則式偵測 / 日誌管線 / RAGQueryPlanner
-> TriagePolicy
-> LLMAssist
-> 統一 Security Triage Report
```

角色分工：

- Rule-Based Detector、Log Pipeline、TriagePolicy 是 deterministic。
- RAGQueryPlanner 與 RAG QA 負責知識檢索與解釋。
- LLMAssist 只提供 advisory 建議。
- 統一 Security Triage Report 是最終輸出格式。

### 系統架構

![繁體中文架構圖](docs/architecture_zh.png)

主要模組：

- `app.py`：互動式 CLI 入口
- `modules/mode_handlers.py`：CLI 模式協調
- `modules/agent.py`：`SecurityAgent` 協調層
- `modules/detector.py`：規則式 payload 偵測
- `modules/triage_policy.py`：風險、決策與模擬防禦策略
- `modules/llm_assist.py`：選用的 LLM 輔助解釋與可疑行為建議
- `modules/log_pipeline.py`：原始日誌解析、正規化、聚合、轉接與轉譯
- `modules/rag_query_planner.py`：RAG 查詢規劃與偏好來源選擇
- `modules/rag_qa.py`：本地知識檢索與回答生成
- `modules/types.py`：Pydantic boundary types

### CLI 模式

```text
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

### 測試與品質檢查

```powershell
python -m pytest
python -m ruff check .
python -m mypy app.py modules tests
```

目前預期測試結果：`141 passed`。

測試使用 dummy RAG 與 LLMAssist 物件，不會啟動完整 CLI，也不會初始化 RAGQA、Chroma、embeddings、Torch、Ollama、ChatOllama 或本地 LLM client。GitHub Actions CI 會執行同一組品質檢查。

### 目前狀態

目前分支：

```text
main
```

Current release: tag `v1.4.0` on `main`

已完成：

- 統一 Security Triage Report
- 原始日誌轉譯與 brute-force candidate 聚合
- XSS、SQL Injection、Path Traversal、Command Injection 的規則式偵測
- `RAGQueryPlanner`
- Pydantic boundary types 基礎
- v1.4 Detection-as-Code Lite：YAML detection rules、`DetectionRule` schema、YAML rule loader、detector adapter、rule metadata，並保留 hard-coded fallback
- 邊界：仍是 deterministic rule-based detection，不是 ML detection，也不是 LLM-generated rules；YAML metadata 不會覆蓋 `TriagePolicy`
- expanded golden smoke tests、direct log pipeline tests、boundary model tests、`pytest`、`ruff`、寬鬆 `mypy` 與 GitHub Actions CI

### 延伸閱讀

- [Technical Notes](docs/TECH_NOTES.md)：整理 Detection-as-Code、Evidence/Incident model、LLM guardrails、MITRE metadata 與測試策略。
- [Roadmap](docs/ROADMAP.md)：版本規劃與後續里程碑。
- [Architecture Debt Journal](ARCHITECTURE_DEBT.md)：架構整理與技術債紀錄。
- [Demo & Evaluation Report](REPORT.md)：Demo 流程與驗證紀錄。

### Roadmap / 後續規劃

**✅ v1.3 — Evidence and Incident Capability / 證據與事件能力**（已完成）

已交付項目請見 [docs/ROADMAP.md](docs/ROADMAP.md)。

**✅ v1.4 — Detection-as-Code Lite / YAML 規則式偵測**（已完成）

- YAML-based detection rules / YAML 偵測規則
- `DetectionRule` schema and YAML rule loader / `DetectionRule` schema 與 YAML rule loader
- Detector adapter using YAML as primary path / detector adapter 以 YAML 作為主要偵測路徑
- Severity, confidence, references, and MITRE technique metadata / 嚴重度、信心值、參考資料與 MITRE 技術 metadata
- XSS / SQL Injection / Path Traversal / Command Injection signatures migrated to YAML / 已將 XSS、SQL Injection、Path Traversal、Command Injection signatures 移至 YAML
- Hard-coded signatures remain as fallback / hard-coded signatures 保留作為保守 fallback

**📋 v1.5+ — Controller Agent, Tool Registry, Evaluation, and Dashboard / 控制代理、工具註冊表、評估與 Dashboard**

- Tool-calling ControllerAgent and tool registry / 可呼叫工具的 ControllerAgent 與工具註冊表
- Benchmark dataset and quality evaluation / 評估資料集與品質評估
- Web dashboard / demo exploration / Web dashboard 與 demo 探索

完整規劃請見 [docs/ROADMAP.md](docs/ROADMAP.md)。
