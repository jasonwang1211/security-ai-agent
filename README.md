# AI-driven Security Threat Detection and Response System

> AI-assisted log-based blue-team triage prototype for suspicious payload analysis, log ingestion, RAG-supported security Q&A, and simulated incident response.

[English](#english) | [繁體中文](#繁體中文)

---

<a id="english"></a>

# English

## Overview

This project is an AI-assisted blue-team security analysis system.

It helps analysts review suspicious payloads, security event descriptions, log files, security knowledge questions, and follow-up questions during analysis.

The system is **not an offensive automation tool**. It is a defensive, academic prototype that demonstrates how rule-based detection, RAG, LLM-assisted analysis, and log triage can be combined into a readable blue-team workflow.

The current version focuses on this flow:

```text
Payload / Log / Knowledge / Follow-up
→ SecurityAgent
→ Security Triage Report
```

---

## Key Idea

A pure rule-based system is stable for known attacks, but it is limited when handling ambiguous behavior or log-like events.

A pure LLM-based system is flexible, but it may hallucinate, misclassify security events, or weaken deterministic security decisions.

This project uses a hybrid design:

| Component | Role |
|---|---|
| Mode Router | Routes CLI input to payload analysis, log ingestion, knowledge Q&A, or follow-up mode |
| Skill Layer | Keeps mode-specific CLI flows thin and separated from `app.py` |
| Rule-Based Detector | Detects known attack signatures and remains the primary detection layer |
| RiskScorer | Maps detected attack types to risk levels |
| DecisionEngine | Maps risk levels to simulated decisions |
| DefenseSimulator | Simulates blue-team response actions without modifying real systems |
| RAGQA | Retrieves structured blue-team knowledge from ChromaDB |
| LLMThreatJudge | Provides advisory judgment for clean-but-suspicious inputs |
| LLMSecurityAnalyzer | Adds optional secondary AI assist notes for detected incidents |
| Log Parser | Parses supported raw log formats |
| Event Normalizer | Converts parsed logs into normalized security events |
| Event Aggregator | Aggregates repeated events such as brute-force candidates |
| Event-to-Agent Adapter | Converts normalized / aggregated events into SecurityAgent inputs |
| Responder | Builds the final `[Security Triage Report]` |
| CLI Progress Output | Shows started / elapsed-time / complete messages for long-running calls |

The goal is to create a system that is explainable, safer than LLM-only security judgment, and suitable for blue-team demo workflows.

---

## CLI Modes

After running `python app.py`, the system shows:

```text
請選擇模式：
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

| Mode | Purpose |
|---|---|
| 1. Payload / event analysis | Analyze a suspicious payload or event description directly |
| 2. Log file ingestion demo | Read a log file, summarize parsed events, and optionally send events to SecurityAgent |
| 3. Security knowledge Q&A | Ask security knowledge questions through RAG-supported Q&A |
| 4. Follow-up / more details | Continue from previous context and ask for more explanation |
| 0. Exit | Close the CLI |

---

## Current Pipelines

### Payload Analysis Flow

```text
User Payload / Event Description
        |
        v
Rule-Based Detector
        |
        v
RiskScorer
        |
        v
DecisionEngine
        |
        v
DefenseSimulator
        |
        v
Optional AI Assist
        |
        v
Security Triage Report
```

### Log Ingestion Flow

```text
Raw Log File
        |
        v
Log Parser
        |
        v
Event Normalizer
        |
        v
Event Aggregator
        |
        v
Event-to-Agent Adapter
        |
        v
SecurityAgent
        |
        v
Security Triage Report
```

### RAG Knowledge Flow

```text
Security Question
        |
        v
RAGQA
        |
        v
ChromaDB Retrieval
        |
        v
LLM Answer Generation
        |
        v
Traditional Chinese Answer
```

---

## Example Security Triage Report

```text
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
Detection Source: rule_based_detector (rule_based)

2. Evidence
Input / Payload:
<script>alert(1)</script>

Matched Signatures:
- XSS: <script>, alert(

3. Why It Matters
- XSS: XSS 可能讓攻擊者把腳本注入頁面，影響使用者瀏覽器、竊取 session 或執行未授權操作。

4. Recommended Response
1. 檢查可疑輸入是否被反射到 response body 或頁面模板。
2. 確認輸出點已依 HTML、JavaScript 或 attribute context 正確 encoding。
3. 檢查 Content Security Policy (CSP) 是否啟用並限制不可信腳本來源。

5. Simulation Notice
已模擬將此事件加入監控與告警佇列，未實際部署監控規則。

6. AI Assist
LLM Suggested Attack Type: XSS
LLM Suggested Decision: BLOCK
Confidence: 0.99
Note: Final Decision is determined by the system decision flow.
```

Important distinction:

```text
Decision = final system decision
LLM Suggested Decision = AI assist suggestion only
```

---

## Example Demo Cases

| Case | Input / Action | Expected Behavior |
|---|---|---|
| Mode 1 XSS | `<script>alert(1)</script>` | XSS / MEDIUM / MONITOR with `[Security Triage Report]` |
| Mode 2 Log Summary | `demo_logs\web_attack.log` | Shows parsed logs, normalized events, aggregated events, and preserved payloads |
| Mode 2 First Event | `web_attack.log`, scope `1` | Only first event is analyzed as XSS |
| Mode 2 All Events | `web_attack.log`, scope `2` | XSS, SQL Injection, and Path Traversal reports are generated |
| Mode 3 Q&A | `什麼是 XSS` | RAG-supported security knowledge answer |
| Mode 4 Follow-up | `詳細說明` | Context-aware follow-up explanation |
| Blank Input | Empty menu / scope / JSON prompt | CLI gives clear prompt or safe default |

For raw CLI transcripts and evaluation details, see:

- [Demo Outputs](demo_outputs.md)
- [Demo & Evaluation Report](REPORT.md)

---

## Technologies Used

- Python
- LangChain
- ChromaDB
- Hugging Face `sentence-transformers`
- Ollama
- OpenCC
- Local CLI interface

### Model Configuration

| Purpose | Model |
|---|---|
| RAG answer generation | `qwen2.5:7b` |
| Agent / Threat Judge | `gemma4:e4b` |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |

---

## Project Structure

```text
sentinel_project/
├── app.py
├── config.py
├── ingest_knowledge.py
├── demo_log_ingestion.py
├── demo_outputs.md
├── README.md
├── REPORT.md
├── requirements.txt
├── chroma_db/
├── demo_logs/
│   ├── web_attack.log
│   └── auth_bruteforce.log
├── docs/
│   ├── architecture_en.png
│   └── architecture_zh.png
├── knowledge/
│   └── blue_team/
│       ├── attack_techniques/
│       ├── detection_rules/
│       ├── response_playbooks/
│       ├── security_controls/
│       └── anomaly_analysis/
└── modules/
    ├── agent.py
    ├── detector.py
    ├── rag_qa.py
    ├── llm_threat_judge.py
    ├── llm_analyzer.py
    ├── followup_handler.py
    ├── responder.py
    ├── risk_scorer.py
    ├── decision_engine.py
    ├── defense_simulator.py
    ├── log_parser.py
    ├── event_normalizer.py
    ├── event_aggregator.py
    ├── event_to_agent_input.py
    ├── ingest.py
    └── skills/
        ├── __init__.py
        ├── payload_analysis_skill.py
        ├── log_ingestion_skill.py
        ├── knowledge_qa_skill.py
        └── followup_skill.py
```

---

## How to Run

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If activation is blocked, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If needed, install the main packages manually:

```bash
pip install langchain langchain-community langchain-core langchain-text-splitters chromadb sentence-transformers opencc-python-reimplemented ollama
```

Depending on your LangChain version, you may also need:

```bash
pip install langchain-ollama
```

### 3. Start Ollama and prepare models

Check installed models:

```bash
ollama list
```

Required models:

```text
qwen2.5:7b
gemma4:e4b
```

If a model is missing:

```bash
ollama pull qwen2.5:7b
ollama pull gemma4:e4b
```

### 4. Build the RAG knowledge base

```bash
python ingest_knowledge.py
```

### 5. Run the system

```bash
python app.py
```

---

## Safety Constraints

This system is intentionally designed as a defensive simulation system.

- It does not attack real targets.
- It does not modify firewall rules.
- It does not perform real blocking.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions.
- Rule-Based Detector remains the primary detection layer for known attacks.
- Rule-based `ALERT` results cannot be downgraded by the LLM.
- RAG is used for explanation and knowledge support, not primary detection.
- LLM output is used as assisted analysis and controlled decision support.
- This is a defensive academic prototype, not an offensive automation tool.

---

## Current Project Status

Current milestone:

```text
v1.1.4-event-to-agent-adapter
```

Completed:

- Mode Router
- Lightweight Skill Layer
- Rule-based attack detection
- Risk scoring and simulated decision flow
- Defense simulation
- Structured RAG v2 knowledge base
- LLM-assisted threat judgment
- Optional AI assist note for detected incidents
- Signal extraction
- Anomaly-based possible zero-day path
- LLM fail-safe fallback
- Contextual follow-up support
- Traditional Chinese output normalization
- Log parser / normalizer / aggregator
- Log Ingestion Summary
- Event-to-Agent Adapter
- Mode 2 first / all / cancel analysis scope
- CLI progress and input handling
- Numbered `[Security Triage Report]`
- Successful `web_attack.log` demo for:
  - XSS
  - SQL Injection
  - Path Traversal

---

## Future Work

- Test and improve `auth_bruteforce.log` behavior.
- Standardize LLM-assisted suspicious findings into the same `[Security Triage Report]` format.
- Add structured JSON incident report output.
- Add more realistic log input formats.
- Add a small benchmark dataset.
- Add evaluation metrics such as accuracy, false positive rate, false negative rate, and fallback success rate.
- Add a web dashboard for analysts.
- Add a red-team simulator module.
- Add round-based red-team vs blue-team interaction.
- Explore real-time traffic or log ingestion.

---

<a id="繁體中文"></a>

# 繁體中文

## 專案簡介

本專案是一套 AI 輔助的藍隊資安分析系統，目前定位為：

```text
AI-assisted log-based blue-team triage prototype
```

它可以協助分析：

- 可疑 payload
- 安全事件描述
- web / authentication log files
- 資安知識問題
- 上下文追問

本系統是**防禦分析、學術展示與模擬應變系統**，不是攻擊工具，也不是要取代 IDS / WAF / SIEM。

目前版本重點是建立一個可展示的藍隊分析流程：

```text
Payload / Log / Knowledge / Follow-up
→ SecurityAgent
→ Security Triage Report
```

---

## 核心概念

本系統不是單純依賴 LLM，也不是只靠固定規則。

設計方式是：

| 模組 | 功能 |
|---|---|
| Mode Router | 使用 CLI 選單切分 payload、log、知識問答與追問模式 |
| Skill Layer | 將各模式包成薄 wrapper，讓 `app.py` 專注於路由與輸入 |
| Rule-Based Detector | 偵測已知攻擊特徵，作為主要安全判斷層 |
| RiskScorer | 根據攻擊類型給出風險等級 |
| DecisionEngine | 根據風險等級產生模擬決策 |
| DefenseSimulator | 模擬藍隊防禦回應，不修改真實系統 |
| RAGQA | 從 ChromaDB 檢索結構化藍隊知識 |
| LLMThreatJudge | 對規則未命中但可疑的輸入提供輔助判斷 |
| LLMSecurityAnalyzer | 對已偵測事件提供 optional AI assist note |
| Log Parser | 解析支援格式的 raw log |
| Event Normalizer | 將 parsed log 轉成 normalized security event |
| Event Aggregator | 聚合重複事件，例如 brute-force candidate |
| Event-to-Agent Adapter | 將 log event 轉成 SecurityAgent 可分析的文字輸入 |
| Responder | 產生最後的 `[Security Triage Report]` |
| CLI Progress Output | 對長時間分析顯示 started / elapsed-time / complete |

這樣可以兼顧穩定性、可解釋性與 AI 輔助推理能力。

---

## CLI 模式

執行 `python app.py` 後，系統會顯示：

```text
請選擇模式：
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

| 模式 | 說明 |
|---|---|
| 1. Payload / event analysis | 直接分析可疑 payload 或事件描述 |
| 2. Log file ingestion demo | 讀取 log 檔案，顯示 summary，並可選擇是否送進 SecurityAgent |
| 3. Security knowledge Q&A | 透過 RAG 回答資安知識問題 |
| 4. Follow-up / more details | 延續前一個上下文做追問 |
| 0. Exit | 離開系統 |

---

## 目前流程

### Payload 分析流程

```text
User Payload / Event Description
        |
        v
Rule-Based Detector
        |
        v
RiskScorer
        |
        v
DecisionEngine
        |
        v
DefenseSimulator
        |
        v
Optional AI Assist
        |
        v
Security Triage Report
```

### Log Ingestion 流程

```text
Raw Log File
        |
        v
Log Parser
        |
        v
Event Normalizer
        |
        v
Event Aggregator
        |
        v
Event-to-Agent Adapter
        |
        v
SecurityAgent
        |
        v
Security Triage Report
```

### RAG 知識問答流程

```text
Security Question
        |
        v
RAGQA
        |
        v
ChromaDB Retrieval
        |
        v
LLM Answer Generation
        |
        v
繁體中文回答
```

---

## Security Triage Report 範例

```text
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
Detection Source: rule_based_detector (rule_based)

2. Evidence
Input / Payload:
<script>alert(1)</script>

Matched Signatures:
- XSS: <script>, alert(

3. Why It Matters
- XSS: XSS 可能讓攻擊者把腳本注入頁面，影響使用者瀏覽器、竊取 session 或執行未授權操作。

4. Recommended Response
1. 檢查可疑輸入是否被反射到 response body 或頁面模板。
2. 確認輸出點已依 HTML、JavaScript 或 attribute context 正確 encoding。
3. 檢查 Content Security Policy (CSP) 是否啟用並限制不可信腳本來源。

5. Simulation Notice
已模擬將此事件加入監控與告警佇列，未實際部署監控規則。

6. AI Assist
LLM Suggested Attack Type: XSS
LLM Suggested Decision: BLOCK
Confidence: 0.99
Note: Final Decision is determined by the system decision flow.
```

注意：

```text
Decision = 系統最終決策
LLM Suggested Decision = AI 輔助建議，不代表最終動作
```

---

## Demo 測試案例

| 類型 | 測試輸入 / 操作 | 預期結果 |
|---|---|---|
| Mode 1 XSS | `<script>alert(1)</script>` | XSS / MEDIUM / MONITOR，輸出 `[Security Triage Report]` |
| Mode 2 Log Summary | `demo_logs\web_attack.log` | 顯示 parsed logs、normalized events、aggregated events、preserved payloads |
| Mode 2 First Event | `web_attack.log`，scope `1` | 只分析第一筆事件，結果為 XSS |
| Mode 2 All Events | `web_attack.log`，scope `2` | 產生 XSS、SQL Injection、Path Traversal 三份報告 |
| Mode 3 Q&A | `什麼是 XSS` | RAG-supported 資安知識回答 |
| Mode 4 Follow-up | `詳細說明` | 根據上下文延伸回答 |
| Blank Input | 空白選單 / scope / JSON prompt | CLI 顯示明確提示或採取安全預設 |

完整 CLI 輸出與評估請參考：

- [Demo Outputs](demo_outputs.md)
- [Demo & Evaluation Report](REPORT.md)

---

## 使用技術

- Python
- LangChain
- ChromaDB
- Hugging Face `sentence-transformers`
- Ollama
- OpenCC
- Local CLI interface

### 模型設定

| 用途 | 模型 |
|---|---|
| RAG 回答生成 | `qwen2.5:7b` |
| Agent / Threat Judge | `gemma4:e4b` |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |

---

## 專案結構

```text
sentinel_project/
├── app.py
├── config.py
├── ingest_knowledge.py
├── demo_log_ingestion.py
├── demo_outputs.md
├── README.md
├── REPORT.md
├── requirements.txt
├── chroma_db/
├── demo_logs/
│   ├── web_attack.log
│   └── auth_bruteforce.log
├── docs/
│   ├── architecture_en.png
│   └── architecture_zh.png
├── knowledge/
│   └── blue_team/
│       ├── attack_techniques/
│       ├── detection_rules/
│       ├── response_playbooks/
│       ├── security_controls/
│       └── anomaly_analysis/
└── modules/
    ├── agent.py
    ├── detector.py
    ├── rag_qa.py
    ├── llm_threat_judge.py
    ├── llm_analyzer.py
    ├── followup_handler.py
    ├── responder.py
    ├── risk_scorer.py
    ├── decision_engine.py
    ├── defense_simulator.py
    ├── log_parser.py
    ├── event_normalizer.py
    ├── event_aggregator.py
    ├── event_to_agent_input.py
    ├── ingest.py
    └── skills/
        ├── __init__.py
        ├── payload_analysis_skill.py
        ├── log_ingestion_skill.py
        ├── knowledge_qa_skill.py
        └── followup_skill.py
```

---

## 執行方式

### 1. 建立並啟動虛擬環境

Windows PowerShell：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

如果 PowerShell 阻擋啟動：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然後再次啟動：

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. 安裝套件

```bash
pip install -r requirements.txt
```

必要時可手動安裝主要套件：

```bash
pip install langchain langchain-community langchain-core langchain-text-splitters chromadb sentence-transformers opencc-python-reimplemented ollama
```

視 LangChain 版本而定，可能還需要：

```bash
pip install langchain-ollama
```

### 3. 啟動 Ollama 並確認模型

確認模型存在：

```bash
ollama list
```

需要：

```text
qwen2.5:7b
gemma4:e4b
```

如果缺少模型：

```bash
ollama pull qwen2.5:7b
ollama pull gemma4:e4b
```

### 4. 建立 RAG 知識庫

```bash
python ingest_knowledge.py
```

### 5. 啟動系統

```bash
python app.py
```

---

## 安全限制

本系統只做防禦分析與模擬：

- 不攻擊真實目標
- 不修改防火牆規則
- 不進行真實封鎖
- `BLOCK / MONITOR / ALLOW` 都是模擬決策
- Rule-Based Detector 仍是已知攻擊的主要偵測層
- Rule-Based `ALERT` 不會被 LLM 降級
- RAG 只用於解釋與知識支援，不作為主要偵測依據
- LLM 僅作為輔助判斷與受控決策支援
- 這是防禦導向學術 prototype，不是攻擊自動化工具

---

## 專案目前狀態

目前 milestone：

```text
v1.1.4-event-to-agent-adapter
```

已完成：

- Mode Router
- Lightweight Skill Layer
- Rule-based attack detection
- Risk scoring and simulated decision flow
- Defense simulation
- Structured RAG v2 knowledge base
- LLM-assisted threat judgment
- Optional AI assist note for detected incidents
- Signal extraction
- Anomaly-based possible zero-day path
- LLM fail-safe fallback
- Contextual follow-up support
- Traditional Chinese output normalization
- Log parser / normalizer / aggregator
- Log Ingestion Summary
- Event-to-Agent Adapter
- Mode 2 first / all / cancel analysis scope
- CLI progress and input handling
- Numbered `[Security Triage Report]`
- `web_attack.log` demo 已成功展示：
  - XSS
  - SQL Injection
  - Path Traversal

---

## 未來規劃

- 測試並改善 `auth_bruteforce.log` 行為
- 將 LLM-assisted suspicious finding 統一成 `[Security Triage Report]` 格式
- 加入 structured JSON incident report output
- 支援更多真實 log input 格式
- 建立小型 benchmark dataset
- 加入 detection accuracy、false positive rate、false negative rate、fallback success rate 等評估指標
- 加入 Web dashboard
- 建立 Red-Team Simulator
- 做紅隊 vs 藍隊回合制模擬
- 探索 real-time traffic 或 log ingestion
