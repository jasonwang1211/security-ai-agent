# Demo Walkthrough and Verification Report

[English](#english) | [繁體中文](#繁體中文)

<a id="english"></a>
# English

> Project: AI-assisted Security Threat Detection and Response System  
> Current target: tag `v1.3.0` on `main`  
> Milestone: Evidence and Incident Capability

Full CLI excerpts are available in [demo_outputs.md](demo_outputs.md).

This report documents representative CLI workflows and pass/fail verification against the current unified `Security Triage Report` contract. It is not a statistical benchmark. Precision / recall, false positive rate, and retrieval quality evaluation are planned for a later milestone.

---

## v1.3 Evidence and Incident Capability

What changed:

- Added `EvidenceItem`, `EvidenceBundle`, `Finding`, `Incident`, `GenerationMetadata`, and `LLMAssessment` schemas.
- Added `LLMGuardrails` for evidence references, deterministic downgrade protection, unilateral `BLOCK` caution, attack-type allowlisting, and confidence sanity.
- Added `auth_success` normalization in the log pipeline.
- Added deterministic time-window and sequence correlation for `possible_account_compromise`.
- Added JSON Incident Report export utilities.
- Added report-aware follow-up helpers for EV-ID / F-ID lookup and report explanation.
- Added evidence-grounded LLMAssist fallback/advisory assessment with guardrail validation.
- Added Scenario A mixed authentication demo log and integration coverage.
- Added 11 `report_explainer` KB docs for report-aware explanation.

Verification:

- `python -m pytest` -> `102 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed

Representative Scenario A:

```text
Mixed auth log
-> parse / normalize
-> time-window + sequence correlation
-> possible_account_compromise
-> Risk Level: HIGH
-> Decision: MONITOR
-> JSON Incident Report
-> EV-003 follow-up explanation
-> LLMAssist advisory assessment with guardrails
```

Boundary note:

This is not confirmed compromise. `MONITOR` means analyst review / simulated monitoring. The prototype does not perform real firewall, WAF, EDR, SIEM, or SOAR action. LLMAssist remains advisory and cannot override the deterministic final decision.

### v1.3 證據與事件能力

v1.3 將系統從單一事件分析推進到 incident-style evidence handling。系統現在能使用 EV-ID / F-ID 保存證據與 finding，針對 authentication log 進行 time-window sequence correlation，偵測 repeated auth_failure followed by auth_success 的 `possible_account_compromise` 情境，並輸出 JSON Incident Report。

驗證結果：`pytest` 為 `102 passed`，`ruff` 通過，`mypy app.py modules tests` 通過。此判定仍是 deterministic correlation；`possible_account_compromise` 代表可疑但未確認的 compromise，因此 v1.3 預設為 `HIGH / MONITOR`。LLMAssist 只提供 advisory reasoning，並受到 guardrails 限制；最終 decision 不會被 LLM 覆蓋，也不會執行真實 enforcement。

---

## 1. Report Overview

The current system is an AI-assisted blue-team security triage prototype. It supports:

- Suspicious payload / event analysis
- Single raw log translation
- Log file ingestion and aggregation
- RAG-based security knowledge Q&A
- Follow-up explanation
- Unified `[Security Triage Report]` output

The latest milestone stabilizes a single triage report format across deterministic and LLM-assisted analysis paths, adds raw authentication log translation, demonstrates aggregated brute-force candidate analysis, and improves Mode 3 knowledge Q&A routing with `RAGQueryPlanner` and preferred source selection.

---

## 2. System Overview

| Capability | Current Behavior |
|---|---|
| CLI Modes | The menu routes users to payload/event analysis, log file ingestion, security knowledge Q&A, follow-up explanation, or exit. |
| Unified Triage Output | Security analysis results use `[Security Triage Report]` with Quick Verdict, Summary, Evidence, Why It Matters, Recommended Response, Simulation Notice, and AI Assist sections. |
| Payload / Event Analysis | Known suspicious payloads are routed by CLI mode handlers, analyzed by SecurityAgent, scored by `TriagePolicy`, and optionally enriched by `LLMAssist`. |
| Single Raw Log Translation | Raw authentication log lines are handled by the consolidated log pipeline and triaged as authentication failures. |
| Log File Ingestion | Log files are parsed, normalized, aggregated, and adapted by `modules/log_pipeline.py`, then optionally sent to SecurityAgent. |
| Brute Force Candidate Analysis | Repeated authentication failures can aggregate into a `brute_force_candidate` event for SecurityAgent triage. |
| RAG Knowledge Q&A | Mode 3 uses a dedicated knowledge route, `RAGQueryPlanner`, preferred source selection, and Chroma fallback for explanatory answers. |
| Follow-up Explanation | Mode 4 remains available for additional explanation based on previous context. |

---

## 3. Architecture

### A. Payload Flow

```text
User Input
-> CLI Mode Handler
-> SecurityAgent
-> Rule-Based Detector
-> TriagePolicy
-> LLMAssist
-> Security Triage Report
```

### B. Single Raw Log Flow

```text
Raw Log Line
-> Consolidated Log Pipeline
-> Raw Log Translation
-> Authentication Failure Triage Report
```

### C. Log File Flow

```text
Log File
-> Consolidated Log Pipeline
-> Aggregated Event
-> SecurityAgent
-> Security Triage Report
```

### D. RAG QA Flow

```text
Security Question
-> Dedicated Knowledge Q&A route
-> RAGQueryPlanner
-> Preferred source selection / Chroma fallback
-> RAG Answer
```

Mode 3 RAG is used for knowledge explanation only. It does not decide attack type, risk level, or final simulated action.

---

## 4. Demo Cases Summary

| ID | Category | Input | Expected Behavior | Result |
|---|---|---|---|---|
| D01 | Mode 1 XSS Payload | `<script>alert(1)</script>` | `ALERT / XSS / MEDIUM / MONITOR` | Passed |
| D02 | Mode 1 Single Raw Auth Log | `2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401` | Input Translation plus `REVIEW / Authentication Failure / LOW / MONITOR` | Passed |
| D03 | Mode 2 `auth_bruteforce.log` Summary | `demo_logs\auth_bruteforce.log` | 10 `auth_failure` events aggregated into 1 `brute_force_candidate` | Passed |
| D04 | Mode 2 `auth_bruteforce.log` SecurityAgent Analysis | `demo_logs\auth_bruteforce.log` | `SUSPICIOUS / Brute Force or Brute Force + Credential Stuffing / MONITOR` | Passed |
| D05 | Mode 3 Brute Force Q&A | Brute force question | RAG answer about brute force and blue-team interpretation | Passed |
| D06 | Mode 3 Login Failure Analysis Q&A | Login failure analysis question | Mentions `source_ip`, endpoint, user, time window, HTTP `401` / `403`, brute force / credential stuffing | Passed |
| D07 | Mode 3 Security Triage Report Guide | Security Triage Report guide question | Explains Quick Verdict, Summary, Evidence, Why It Matters, Recommended Response, Simulation Notice, AI Assist, Risk Level, Decision, and simulated decisions | Passed |
| D08 | Mode 1 XSS Regression | `<script>alert(1)</script>` | Rule-based report still works | Passed |
| D09 | Mode 1 Command Injection Regression | `test; rm -rf /tmp/test` | Rule-based Command Injection detection with `HIGH / BLOCK` | Passed |

---

## 5. Detailed Demo Results

### D01 - Mode 1 XSS Payload

Input:

```html
<script>alert(1)</script>
```

Observed summary:

```text
[Security Triage Report]

0. Quick Verdict
Verdict: This event is likely XSS.
Risk Level: MEDIUM
Decision: MONITOR
Reason: Matched XSS indicators: <script>, alert(

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
Detection Source: rule_based_detector (rule_based)
```

Evaluation: Passed.

The rule-based path still detects XSS and emits the current unified report format.

### D02 - Mode 1 Single Raw Auth Log

Input:

```text
2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401
```

Observed summary:

```text
[Input Translation]
Detected Input Type: raw_log
Normalized Event Type: auth_failure
Converted SecurityAgent Input:
login failed from source_ip 10.0.0.5 against /login for user admin

[Security Triage Report]

0. Quick Verdict
Verdict: This is a failed login event. A single failure is not enough to confirm brute force.
Risk Level: LOW
Decision: MONITOR

1. Summary
Status: REVIEW
Attack Type: Authentication Failure
Risk Level: LOW
Decision: MONITOR
Detection Source: raw_log_translation
```

Evaluation: Passed.

A single failed login is treated as a reviewable authentication signal, not enough evidence by itself to confirm brute force.

### D03 - Mode 2 auth_bruteforce.log Summary

Input:

```text
demo_logs\auth_bruteforce.log
```

Observed summary:

```text
[Log Ingestion Summary]

Total Lines: 10
Parsed Logs: 10
Normalized Events: 10
Aggregated Events: 1

Detected Event Types:
- auth_failure: 10

Aggregated Finding:
- Event Type: brute_force_candidate
- Source IP: 192.168.1.10
- Target: /login
- Failed Count: 10
```

Evaluation: Passed.

Mode 2 now demonstrates that repeated authentication failures can be aggregated before SecurityAgent analysis.

### D04 - Mode 2 auth_bruteforce.log SecurityAgent Analysis

Observed summary:

```text
[Security Triage Report]

0. Quick Verdict
Verdict: This event is suspicious for Brute Force or Credential Stuffing.
Risk Level: HIGH
Decision: MONITOR

1. Summary
Status: SUSPICIOUS
Attack Type: Brute Force / Credential Stuffing
Risk Level: HIGH
Decision: MONITOR
Detection Source: llm_assist + signal_extraction
```

Evaluation: Passed.

Aggregated failures from the same source and target become suspicious brute-force or credential-stuffing evidence while the final decision remains a simulated `MONITOR`.

### D05 - Mode 3 Brute Force Q&A

Question:

```text
What is brute force?
```

Expected result:

```text
RAG-supported explanation of repeated credential guessing from a blue-team perspective.
```

Evaluation: Passed.

### D06 - Mode 3 Login Failure Analysis Q&A

Question:

```text
How should repeated login failures be analyzed?
```

Expected result:

```text
Mentions time window, source_ip, endpoint, user, HTTP 401 / 403, brute force / credential stuffing, and false-positive considerations.
```

Evaluation: Passed.

### D07 - Mode 3 Security Triage Report Guide

Question:

```text
How should I read a Security Triage Report?
```

Expected result:

```text
Explains the report sections and clarifies that BLOCK, MONITOR, and ALLOW are simulated decisions.
```

Evaluation: Passed.

### D08 - Mode 1 XSS Regression

Input:

```html
<script>alert(1)</script>
```

Expected result:

```text
Rule-based XSS report remains stable.
```

Evaluation: Passed.

### D09 - Mode 1 Command Injection Regression

Input:

```text
test; rm -rf /tmp/test
```

Observed summary:

```text
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: Command Injection
Risk Level: HIGH
Decision: BLOCK
Detection Source: rule_based_detector (rule_based)
```

Evaluation: Passed.

The rule-based detector now recognizes high-signal command injection payload indicators and routes them through the current unified report format.

---

## 6. Quality Foundation

The current branch also includes a small but important quality foundation:

- Architecture consolidation around `SecurityAgent`, `TriagePolicy`, `LLMAssist`, `mode_handlers.py`, `log_pipeline.py`, and `RAGQueryPlanner`
- Expanded golden smoke tests for payload regressions, benign input, malformed raw logs, and empty input
- Direct consolidated log pipeline tests for parsing, normalization, and brute-force aggregation
- Pydantic boundary model tests for `modules/types.py`
- Evidence / incident model, guardrail, correlator, exporter, follow-up, LLMAssist, and Scenario A integration tests
- `pytest` for regression checks; current expected result is `102 passed`
- `ruff` for linting and import hygiene
- Lenient `mypy` as a gradual typing baseline
- GitHub Actions CI for automated quality checks

---

## 7. Overall Evaluation

| Capability | Result |
|---|---|
| Unified Security Triage Report | Passed |
| Mode 1 payload triage | Passed |
| Mode 1 raw log translation | Passed |
| Single `auth_failure` triage | Passed |
| Mode 2 log ingestion and aggregation | Passed |
| Mode 2 `brute_force_candidate` SecurityAgent analysis | Passed |
| Mode 3 dedicated knowledge Q&A routing | Passed |
| `RAGQueryPlanner` and preferred source selection | Passed |
| Rule-based Command Injection detection | Passed |
| Quality checks and CI foundation | Passed |

Overall result:

```text
Unified Security Triage Output and RAG QA Stabilization milestone is ready for demo documentation.
```

---

## 8. Key Findings

1. The system now separates a single `auth_failure` from an aggregated `brute_force_candidate`.
2. A single authentication failure is triaged as `REVIEW / LOW / MONITOR`.
3. Aggregated repeated failures can become suspicious Brute Force / Credential Stuffing evidence.
4. Rule-based detections and LLMAssist suggestions now both use the unified `[Security Triage Report]`.
5. Mode 3 RAG QA is no longer driven by the old keyword fallback in the active routing path.
6. RAG is used for security knowledge explanation, while detection, risk, and decision fields remain part of the triage pipeline.

---

## 9. Limitations

This demo remains a functional prototype with the following limitations:

- Not all real-world log formats are supported.
- There is no real firewall, WAF, EDR, or production SIEM action.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions only.
- LLM suggestions do not override the final system `Decision`.
- RAG is not used for primary detection.
- The current CLI is still menu-based and is not yet a full Main Controller Agent.
- Startup still initializes heavy RAG, embedding, and Chroma components.
- Smart Input Router / Main Controller Agent behavior remains future work.
- `RAGQueryPlanner` improves retrieval, but answer quality still depends on the quality of knowledge files and local LLM output.

For planned future work, see [docs/ROADMAP.md](docs/ROADMAP.md).

---

<a id="繁體中文"></a>
# 繁體中文

> 專案：AI 輔助安全威脅偵測與回應系統  
> 目前目標：`main` 上的 tag `v1.3.0`  
> 里程碑：Evidence and Incident Capability

完整 CLI 範例可參考 [demo_outputs.md](demo_outputs.md)。

本報告記錄代表性的 CLI 流程與 pass/fail 驗證，用來確認目前統一 `Security Triage Report` 契約是否穩定。這不是統計式 benchmark；precision / recall、false positive rate 與 retrieval quality evaluation 會留到後續里程碑。

---

## 1. 報告概述

目前系統是一個 AI-assisted blue-team security triage prototype，支援：

- Suspicious payload / event analysis
- Single raw log translation
- Log file ingestion and aggregation
- RAG-based security knowledge Q&A
- Follow-up explanation
- Unified Security Triage Report

本里程碑的重點是穩定統一的 Security Triage Report 格式，讓規則式偵測、日誌轉譯、聚合事件分析，以及 LLMAssist 輔助建議都能以一致格式呈現。同時，Mode 3 已透過 `RAGQueryPlanner` 與 preferred source selection 改善知識問答路由。

---

## 2. 系統概覽

| 能力 | 目前行為 |
|---|---|
| CLI 模式 | 選單可進入 payload / event analysis、log file ingestion、security knowledge Q&A、follow-up explanation 或離開。 |
| 統一分流輸出 | 安全分析結果使用 `[Security Triage Report]`，包含 Quick Verdict、Summary、Evidence、Why It Matters、Recommended Response、Simulation Notice 與 AI Assist。 |
| Payload / Event Analysis | 可疑 payload 由 CLI Mode Handler 送入 `SecurityAgent`，透過 Rule-Based Detector、`TriagePolicy` 與選用 `LLMAssist` 產生報告。 |
| Single Raw Log Translation | 單筆原始 authentication log 由 Consolidated Log Pipeline 轉譯，並以 authentication failure 進行分流。 |
| Log File Ingestion | `modules/log_pipeline.py` 負責解析、正規化、聚合與轉接日誌，再視情況送入 SecurityAgent。 |
| Brute Force Candidate Analysis | 重複登入失敗可聚合為 `brute_force_candidate`，再交由 SecurityAgent 分析。 |
| RAG Knowledge Q&A | Mode 3 使用 `RAGQueryPlanner`、preferred source selection 與 Chroma fallback 提供知識解釋。 |
| Follow-up Explanation | Mode 4 可根據前文提供補充說明。 |

---

## 3. 架構

目前架構使用下列核心元件：

- CLI Mode Handler
- SecurityAgent
- Rule-Based Detector
- TriagePolicy
- LLMAssist
- Consolidated Log Pipeline
- RAGQueryPlanner
- Unified Security Triage Report

整體流程：

```text
使用者輸入
-> CLI Mode Handler
-> SecurityAgent
-> Rule-Based Detector / Consolidated Log Pipeline / RAGQueryPlanner
-> TriagePolicy
-> LLMAssist
-> Unified Security Triage Report
```

Payload flow:

```text
User Input
-> CLI Mode Handler
-> SecurityAgent
-> Rule-Based Detector
-> TriagePolicy
-> LLMAssist
-> Security Triage Report
```

Single raw log flow:

```text
Raw Log Line
-> Consolidated Log Pipeline
-> Raw Log Translation
-> Authentication Failure Triage Report
```

Log file flow:

```text
Log File
-> Consolidated Log Pipeline
-> Aggregated Event
-> SecurityAgent
-> Security Triage Report
```

RAG QA flow:

```text
Security Question
-> Dedicated Knowledge Q&A route
-> RAGQueryPlanner
-> Preferred source selection / Chroma fallback
-> RAG Answer
```

Mode 3 RAG 只負責知識解釋，不決定 attack type、risk level 或模擬 action。

---

## 4. Demo 摘要

| ID | 類別 | 輸入 | 預期行為 | 結果 |
|---|---|---|---|---|
| D01 | Mode 1 XSS payload | `<script>alert(1)</script>` | `ALERT / XSS / MEDIUM / MONITOR` | Passed |
| D02 | Mode 1 single raw auth log | `login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401` | Input Translation 加上 `REVIEW / Authentication Failure / LOW / MONITOR` | Passed |
| D03 | Mode 2 `auth_bruteforce.log` summary | `demo_logs\auth_bruteforce.log` | 10 筆 `auth_failure` 聚合成 1 筆 `brute_force_candidate` | Passed |
| D04 | Mode 2 `auth_bruteforce.log` SecurityAgent analysis | `demo_logs\auth_bruteforce.log` | `SUSPICIOUS / Brute Force or Credential Stuffing / MONITOR` | Passed |
| D05 | Mode 3 brute force Q&A | brute force 問題 | 以藍隊角度解釋重複 credential guessing | Passed |
| D06 | Mode 3 login failure analysis Q&A | 登入失敗分析問題 | 提到 `source_ip`、endpoint、user、time window、HTTP `401` / `403`、brute force / credential stuffing | Passed |
| D07 | Mode 3 Security Triage Report guide | Security Triage Report 閱讀問題 | 解釋 Quick Verdict、Summary、Evidence、Why It Matters、Recommended Response、Simulation Notice、AI Assist、Risk Level、Decision 與模擬決策 | Passed |
| D08 | Mode 1 XSS regression | `<script>alert(1)</script>` | 規則式 XSS 報告維持穩定 | Passed |
| D09 | Mode 1 Command Injection regression | `test; rm -rf /tmp/test` | Rule-Based Detector 偵測 Command Injection，風險 `HIGH`，決策 `BLOCK` | Passed |

---

## 5. 品質基礎

此分支已完成下列品質基礎：

- architecture consolidation
- expanded golden smoke tests
- direct consolidated log pipeline tests
- Pydantic boundary model tests
- `pytest` (`102 passed`)
- `ruff`
- lenient `mypy`
- GitHub Actions CI

這些檢查讓目前的 demo flow、Pydantic boundary types 與 consolidated architecture 在後續導入 ControllerAgent / Tool Registry 前有更穩定的回歸基礎。

---

## 6. 整體評估

| 能力 | 結果 |
|---|---|
| Unified Security Triage Report | Passed |
| Mode 1 payload triage | Passed |
| Mode 1 raw log translation | Passed |
| Single `auth_failure` triage | Passed |
| Mode 2 log ingestion and aggregation | Passed |
| Mode 2 `brute_force_candidate` SecurityAgent analysis | Passed |
| Mode 3 dedicated knowledge Q&A routing | Passed |
| `RAGQueryPlanner` and preferred source selection | Passed |
| Rule-based Command Injection detection | Passed |
| pytest / ruff / mypy / GitHub Actions CI | Passed |

整體結果：

```text
Unified Security Triage Output and RAG QA Stabilization milestone is ready for demo documentation.
```

---

## 7. 主要觀察

1. 系統已能區分單筆 `auth_failure` 與聚合後的 `brute_force_candidate`。
2. 單筆登入失敗會被分流為 `REVIEW / LOW / MONITOR`。
3. 多筆重複登入失敗可形成 Brute Force / Credential Stuffing 的可疑證據。
4. 規則式偵測與 LLMAssist 建議都會透過統一 `[Security Triage Report]` 呈現。
5. Mode 3 RAG QA 已走 dedicated knowledge route 與 `RAGQueryPlanner`。
6. RAG 用於知識解釋；偵測、風險與決策仍由 triage pipeline 產生。

---

## 8. 限制

- 尚未支援所有真實世界日誌格式。
- 沒有真實 firewall、WAF、EDR 或 production SIEM action。
- `BLOCK`、`MONITOR`、`ALLOW` 都是模擬決策。
- LLMAssist 建議不覆蓋最終系統 `Decision`。
- RAG 不作為主要偵測層。
- 目前 CLI 仍是選單式，尚未成為完整 Main Controller Agent。
- 啟動時仍可能初始化較重的 RAG、embedding 與 Chroma 元件。
- Smart Input Router / Main Controller Agent 仍是未來工作。
- `RAGQueryPlanner` 可改善檢索，但答案品質仍取決於知識檔與本地 LLM 輸出。

後續規劃請見 [docs/ROADMAP.md](docs/ROADMAP.md)。

---

完整 CLI 範例可參考 [demo_outputs.md](demo_outputs.md)。
