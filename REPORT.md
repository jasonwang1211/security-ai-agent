# Demo & Evaluation Report

> Project: AI-driven Security Threat Detection and Response System  
> Branch: `v1.1.4-event-to-agent-adapter`  
> Purpose: Summarize the current CLI demo, log ingestion workflow, event-to-agent adapter, and SecurityAgent triage output.

[English](#english) | [繁體中文](#繁體中文)

Raw CLI transcripts are available in [demo_outputs.md](demo_outputs.md).

---

<a id="english"></a>

# English

## 1. Report Overview

The current system is a command-line blue-team security demo with four CLI modes:

1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details

The latest milestone adds a mode router, a lightweight skill layer, a concise log ingestion summary, an Event-to-Agent Adapter, scoped SecurityAgent analysis for aggregated log events, CLI progress / elapsed-time indicators, and a numbered `[Security Triage Report]` format.

This report summarizes current demo behavior. Full terminal transcripts remain in [demo_outputs.md](demo_outputs.md).

---

## 2. Current Capability Summary

| Capability | Current Behavior |
|---|---|
| Mode Router | CLI menu routes users into payload analysis, log ingestion, knowledge Q&A, or follow-up flows. |
| Skill Layer | Mode-specific wrappers keep `app.py` focused on CLI routing and user input. |
| Rule-based Detection | Known payloads such as XSS, SQL Injection, and Path Traversal are detected deterministically. |
| Risk / Decision Flow | Risk and final decisions remain system-controlled: `HIGH`, `MEDIUM`, `LOW`; `BLOCK`, `MONITOR`, `ALLOW`. |
| Security Triage Report | Mode 1 and SecurityAgent log-event analysis produce numbered `[Security Triage Report]` output. |
| Log Parser / Normalizer / Aggregator | Raw log files are parsed, normalized, and aggregated without changing the ingestion pipeline. |
| Event-to-Agent Adapter | Aggregated log events are converted into SecurityAgent text inputs. |
| SecurityAgent Analysis Scope | Mode 2 supports first-event, all-events, or cancel behavior before sending events to SecurityAgent. |
| CLI Progress Indicators | Long-running SecurityAgent / RAG / LLM calls show started, elapsed-time, and complete messages. |
| RAG Knowledge Q&A | Security knowledge questions are handled in Mode 3 through RAG-supported answers. |
| Follow-up Handling | Mode 4 preserves conversational context for more details. |

---

## 3. Evaluation Goals

| Goal | Description |
|---|---|
| Payload Triage | Show concise final result, evidence, and response guidance for suspicious payloads. |
| Log Ingestion Review | Summarize parsed logs, normalized events, aggregated events, event types, and preserved payloads. |
| Event-to-Agent Analysis | Demonstrate the full path from aggregated log events to SecurityAgent reports. |
| UX Clarity | Show menu, scope selection, blank-input messages, and progress indicators clearly. |
| Knowledge Support | Keep Mode 3 RAG Q&A separate from attack analysis. |
| Follow-up Support | Keep Mode 4 context-aware follow-up behavior. |

---

## 4. Demo Cases Summary

| ID | Category | Input | Expected Behavior | Result |
|---|---|---|---|---|
| D01 | Mode 1 XSS payload | `<script>alert(1)</script>` | XSS, MEDIUM, MONITOR, `[Security Triage Report]` | Passed |
| D02 | Mode 2 Log Ingestion Summary | `demo_logs\web_attack.log` | 3 parsed logs, 3 normalized events, 3 aggregated events, preserved payloads | Passed |
| D03 | Mode 2 Analyze First Event | `demo_logs\web_attack.log`, scope `1` | Only first event analyzed as XSS | Passed |
| D04 | Mode 2 Analyze All Events | `demo_logs\web_attack.log`, scope `2` | Event 1: XSS / MEDIUM / MONITOR; Event 2: SQL Injection / HIGH / BLOCK; Event 3: Path Traversal / HIGH / BLOCK | Passed |
| D05 | Blank Input Handling | Blank menu / scope / JSON prompt | Menu prompts user; blank scope cancels SecurityAgent analysis; blank JSON prompt defaults to not showing JSON | Passed |
| D06 | Mode 3 Security Knowledge Q&A | `什麼是 XSS` | RAG-supported XSS explanation | Passed |
| D07 | Mode 4 Follow-up | `詳細說明` | Context-aware follow-up answer | Passed |
| D08 | LLM Unavailable Fallback | Brute-force-like log behavior while LLM is unavailable | Existing fallback capability returns conservative suspicious analysis | Existing capability; not retested in latest run |

---

## 5. Detailed Demo Results

### D01 — Mode 1 XSS Payload

Input:

```html
<script>alert(1)</script>
```

Observed summary:

```text
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
Detection Source: rule_based_detector (rule_based)
```

Evaluation: Passed.

The system keeps the final system decision as `MONITOR` while separating any AI assist suggestion from the final decision flow.

---

### D02 — Mode 2 Log Ingestion Summary

Input:

```text
demo_logs\web_attack.log
```

Observed summary:

```text
[Log Ingestion Summary]

File: demo_logs\web_attack.log
Total Lines: 3
Parsed Logs: 3
Normalized Events: 3
Aggregated Events: 3

Detected Event Types:
- web_request: 3

Preserved Payloads:
1. q=<script>alert(1)</script>
2. id=1' or '1'='1
3. file=../../etc/passwd

Current Stage:
Log ingestion only. Events are not sent into SecurityAgent yet.
```

Evaluation: Passed.

Mode 2 now presents concise review output before optionally sending events to SecurityAgent.

---

### D03 — Mode 2 Analyze First Event

Input:

```text
demo_logs\web_attack.log
SecurityAgent scope: 1
```

Observed behavior:

```text
[Analyzing Log Event 1/3]
Input: q=<script>alert(1)</script>
Processing Log Event 1/3 started...
Processing Log Event 1/3 complete.
[SecurityAgent Analysis for Log Event 1]
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
```

Evaluation: Passed.

Only the first converted event is analyzed. The adapter converts the web payload into `q=<script>alert(1)</script>`, and SecurityAgent returns an XSS triage report.

---

### D04 — Mode 2 Analyze All Events

Input:

```text
demo_logs\web_attack.log
SecurityAgent scope: 2
```

Observed results:

| Log Event | Converted Input | Classification | Risk Level | Decision |
|---|---|---|---|---|
| 1/3 | `q=<script>alert(1)</script>` | XSS | MEDIUM | MONITOR |
| 2/3 | `id=1' or '1'='1` | SQL Injection | HIGH | BLOCK |
| 3/3 | `file=../../etc/passwd` | Path Traversal | HIGH | BLOCK |

Evaluation: Passed.

The system demonstrates the complete log-to-agent path:

```text
Raw Log
→ Log Parser
→ Event Normalizer
→ Event Aggregator
→ Event-to-Agent Adapter
→ SecurityAgent
→ Security Triage Report
```

---

### D05 — Blank Input Handling

Observed behavior:

```text
請輸入模式編號，或輸入 0 離開。
未輸入分析範圍，已取消 SecurityAgent 分析。
未顯示 detailed JSON output。
```

Evaluation: Passed.

The CLI now provides clear feedback instead of silently redisplaying menus or prompts.

---

### D06 — Mode 3 Security Knowledge Q&A

Input:

```text
什麼是 XSS
```

Expected result:

```text
RAG-supported XSS explanation
```

Evaluation: Passed.

Mode 3 remains separate from payload detection and routes security knowledge questions to RAG-supported Q&A.

---

### D07 — Mode 4 Follow-up

Input:

```text
詳細說明
```

Expected result:

```text
Context-aware follow-up answer
```

Evaluation: Passed.

Mode 4 preserves existing follow-up behavior.

---

## 6. Overall Evaluation

| Capability | Result |
|---|---|
| Mode router and skill-layer CLI | Passed |
| Mode 1 Security Triage Report | Passed |
| Mode 2 log ingestion summary | Passed |
| Event-to-Agent Adapter | Passed |
| Scoped SecurityAgent log-event analysis | Passed |
| CLI progress / elapsed-time output | Passed |
| Blank input handling | Passed |
| Mode 3 RAG Q&A | Passed |
| Mode 4 follow-up | Passed |

Overall result:

```text
v1.1.4-event-to-agent-adapter demo behavior is ready for presentation.
```

---

## 7. Key Findings

1. The CLI mode router makes the demo easier to explain and operate.
2. The skill layer keeps mode-specific behavior separated from the entry point.
3. Log ingestion now produces a concise summary suitable for review before deeper analysis.
4. The Event-to-Agent Adapter enables the full path from log files to SecurityAgent triage.
5. The `web_attack.log` demo clearly shows XSS, SQL Injection, and Path Traversal across three log events.
6. Progress and elapsed-time messages reduce the appearance of CLI stalls during RAG / LLM / SecurityAgent work.
7. `[Security Triage Report]` is more presentation-friendly than the older blue-team report output.

---

## 8. Limitations

This demo remains a functional prototype and does not yet include:

- Real firewall or WAF control
- Production SIEM integration
- Large-scale benchmark dataset
- Precision / recall / F1-score measurement
- Long-term event storage
- Multi-user authentication
- Web dashboard

The current `BLOCK`, `MONITOR`, and `ALLOW` outputs are simulated decisions only.

---

## 9. Suggested Next Steps

Recommended next development tasks:

1. Test and improve `auth_bruteforce.log` behavior.
2. Convert LLM-assisted suspicious findings into the same `[Security Triage Report]` style.
3. Update `README.md` after this report.
4. Add structured JSON incident report output.
5. Add a small benchmark dataset.
6. Add a web dashboard later.

---

<a id="繁體中文"></a>

# 繁體中文

## 1. 報告概述

目前系統是以 CLI 呈現的藍隊資安分析 demo，支援四種模式：

1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details

最新版本加入 Mode Router、Skill Layer、Log Ingestion Summary、Event-to-Agent Adapter、Mode 2 的 first/all/cancel 分析範圍、CLI progress / elapsed-time 提示，以及新的 `[Security Triage Report]` 編號格式。

原始終端機輸出紀錄請參考：[demo_outputs.md](demo_outputs.md)。

---

## 2. 系統能力摘要

| 能力 | 目前行為 |
|---|---|
| Mode Router | CLI 選單將使用者導向 payload 分析、log ingestion、知識問答或追問流程。 |
| Skill Layer | 各模式以薄 wrapper 拆分，讓 `app.py` 專注於 CLI routing 與輸入處理。 |
| 規則式偵測 | 可穩定偵測 XSS、SQL Injection、Path Traversal 等已知 payload。 |
| 風險與決策流程 | `HIGH` / `MEDIUM` / `LOW` 與 `BLOCK` / `MONITOR` / `ALLOW` 仍由系統流程決定。 |
| Security Triage Report | Mode 1 與 Mode 2 SecurityAgent 分析皆輸出編號式 `[Security Triage Report]`。 |
| Log Parser / Normalizer / Aggregator | 保留既有 pipeline，將 raw logs 轉為 normalized 與 aggregated events。 |
| Event-to-Agent Adapter | 將 aggregated events 轉為 SecurityAgent 可分析的文字輸入。 |
| SecurityAgent 分析範圍 | Mode 2 可選擇只分析第一筆、分析全部或取消。 |
| CLI Progress | 長時間 RAG / LLM / SecurityAgent 呼叫會顯示 started、elapsed-time、complete。 |
| RAG 知識問答 | Mode 3 處理資安知識問題。 |
| 上下文追問 | Mode 4 保留 follow-up 行為。 |

---

## 3. 測試目標

| 目標 | 說明 |
|---|---|
| Payload Triage | 對可疑 payload 顯示最終結果、證據與建議應變。 |
| Log Ingestion Review | 顯示 parsed logs、normalized events、aggregated events、event type counts 與 preserved payloads。 |
| Event-to-Agent Analysis | 展示從 aggregated log event 到 SecurityAgent report 的完整流程。 |
| CLI 可讀性 | 驗證選單、scope selection、空白輸入提示與 progress messages。 |
| 知識支援 | 保持 Mode 3 RAG Q&A 與攻擊分析分離。 |
| 追問支援 | 保持 Mode 4 context-aware follow-up。 |

---

## 4. Demo 測試總表

| ID | 類型 | 測試輸入 | 預期結果 | 結果 |
|---|---|---|---|---|
| D01 | Mode 1 XSS payload | `<script>alert(1)</script>` | XSS、MEDIUM、MONITOR、`[Security Triage Report]` | 通過 |
| D02 | Mode 2 Log Ingestion Summary | `demo_logs\web_attack.log` | 3 parsed logs、3 normalized events、3 aggregated events、preserved payloads | 通過 |
| D03 | Mode 2 Analyze First Event | `demo_logs\web_attack.log`，scope `1` | 只分析第一筆事件，結果為 XSS | 通過 |
| D04 | Mode 2 Analyze All Events | `demo_logs\web_attack.log`，scope `2` | Event 1: XSS / MEDIUM / MONITOR；Event 2: SQL Injection / HIGH / BLOCK；Event 3: Path Traversal / HIGH / BLOCK | 通過 |
| D05 | Blank Input Handling | 空白主選單 / scope / JSON prompt | 主選單提示；空白 scope 取消 SecurityAgent 分析；空白 JSON prompt 不顯示 JSON | 通過 |
| D06 | Mode 3 資安知識問答 | `什麼是 XSS` | RAG-supported XSS explanation | 通過 |
| D07 | Mode 4 追問 | `詳細說明` | context-aware follow-up answer | 通過 |
| D08 | LLM unavailable fallback | LLM 不可用時的 brute-force-like input | 既有 fallback capability 可回傳保守 suspicious analysis | 既有能力，本次最新流程未重測 |

---

## 5. 詳細測試結果

### D01 — Mode 1 XSS Payload

輸入：

```html
<script>alert(1)</script>
```

觀察摘要：

```text
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
Detection Source: rule_based_detector (rule_based)
```

評估：通過。

系統維持最終決策為 `MONITOR`，並將 LLM suggestion 與 final system decision 清楚分開。

---

### D02 — Mode 2 Log Ingestion Summary

輸入：

```text
demo_logs\web_attack.log
```

觀察摘要：

```text
[Log Ingestion Summary]

File: demo_logs\web_attack.log
Total Lines: 3
Parsed Logs: 3
Normalized Events: 3
Aggregated Events: 3

Detected Event Types:
- web_request: 3

Preserved Payloads:
1. q=<script>alert(1)</script>
2. id=1' or '1'='1
3. file=../../etc/passwd
```

評估：通過。

Mode 2 先提供可讀 summary，讓使用者先確認 ingestion 結果，再決定是否送入 SecurityAgent。

---

### D03 — Mode 2 Analyze First Event

輸入：

```text
demo_logs\web_attack.log
SecurityAgent scope: 1
```

觀察摘要：

```text
[Analyzing Log Event 1/3]
Input: q=<script>alert(1)</script>
[SecurityAgent Analysis for Log Event 1]
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
```

評估：通過。

系統只分析第一筆轉換後事件，符合 scope `1` 的預期。

---

### D04 — Mode 2 Analyze All Events

輸入：

```text
demo_logs\web_attack.log
SecurityAgent scope: 2
```

觀察結果：

| Log Event | Converted Input | Classification | Risk Level | Decision |
|---|---|---|---|---|
| 1/3 | `q=<script>alert(1)</script>` | XSS | MEDIUM | MONITOR |
| 2/3 | `id=1' or '1'='1` | SQL Injection | HIGH | BLOCK |
| 3/3 | `file=../../etc/passwd` | Path Traversal | HIGH | BLOCK |

評估：通過。

此案例展示完整流程：

```text
Raw Log
→ Log Parser
→ Event Normalizer
→ Event Aggregator
→ Event-to-Agent Adapter
→ SecurityAgent
→ Security Triage Report
```

---

### D05 — Blank Input Handling

觀察結果：

```text
請輸入模式編號，或輸入 0 離開。
未輸入分析範圍，已取消 SecurityAgent 分析。
未顯示 detailed JSON output。
```

評估：通過。

CLI 對空白輸入提供明確提示，避免使用者誤以為程式卡住或重複執行。

---

### D06 — Mode 3 資安知識問答

輸入：

```text
什麼是 XSS
```

預期結果：

```text
RAG-supported XSS explanation
```

評估：通過。

Mode 3 保持知識問答與 payload/event analysis 分離。

---

### D07 — Mode 4 追問

輸入：

```text
詳細說明
```

預期結果：

```text
Context-aware follow-up answer
```

評估：通過。

Mode 4 保留既有上下文追問能力。

---

## 6. 整體評估

| 能力 | 結果 |
|---|---|
| Mode Router / Skill Layer CLI | 通過 |
| Mode 1 Security Triage Report | 通過 |
| Mode 2 Log Ingestion Summary | 通過 |
| Event-to-Agent Adapter | 通過 |
| Scoped SecurityAgent log-event analysis | 通過 |
| CLI progress / elapsed-time output | 通過 |
| Blank input handling | 通過 |
| Mode 3 RAG Q&A | 通過 |
| Mode 4 follow-up | 通過 |

整體結果：

```text
v1.1.4-event-to-agent-adapter demo 行為已可用於展示。
```

---

## 7. 測試觀察

1. Mode Router 讓 demo 操作流程更容易說明。
2. Skill Layer 讓各模式邏輯與 CLI entry point 分離。
3. Log Ingestion Summary 可在送入 SecurityAgent 前提供清楚檢視。
4. Event-to-Agent Adapter 讓 log file 能進入既有 SecurityAgent 分析流程。
5. `web_attack.log` 可清楚展示 XSS、SQL Injection、Path Traversal 三種事件。
6. CLI progress / elapsed-time messages 降低 RAG、LLM 或 SecurityAgent 長時間等待時的卡住感。
7. `[Security Triage Report]` 較適合專題展示與 SOC-style triage 閱讀。

---

## 8. 限制

目前仍屬 prototype，尚未包含：

- 真實 firewall / WAF 控制
- production SIEM integration
- 大規模 benchmark dataset
- precision / recall / F1-score
- 長期事件儲存
- 多使用者權限控管
- Web dashboard

目前 `BLOCK`、`MONITOR`、`ALLOW` 皆為模擬決策。

---

## 9. 後續建議

建議下一階段工作：

1. Test and improve `auth_bruteforce.log` behavior。
2. Convert LLM-assisted suspicious finding into the same `[Security Triage Report]` style。
3. Update `README.md` after `REPORT.md`。
4. Add JSON incident report output。
5. Add small benchmark dataset。
6. Add web dashboard later。

---

Raw CLI transcripts are available in [demo_outputs.md](demo_outputs.md).
