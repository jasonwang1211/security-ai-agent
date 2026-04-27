# AI-driven Security Threat Detection and Response System

> Hybrid AI Security Agent for blue-team threat detection, RAG-based explanation, LLM-assisted judgment, anomaly detection, and fail-safe response simulation.

[English](#english) | [繁體中文](#繁體中文)

---

<a id="english"></a>

## English

## Overview

This project is an AI-assisted blue-team security analysis system. It analyzes suspicious payloads, security logs, and security-related questions through a hybrid pipeline that combines deterministic detection, structured RAG, signal extraction, LLM-based judgment, decision fusion, anomaly detection, and fail-safe fallback.

The system is intended for **defensive security analysis, academic demonstration, and simulation**, not offensive automation.

---

## Key Idea

The core idea is to avoid relying on a pure LLM-only approach.

Instead, the system combines:

| Component | Role |
|---|---|
| Rule-Based Detector | Reliable detection for known attack signatures |
| Signal Extraction | Extracts suspicious indicators from input |
| RAGQA | Retrieves blue-team knowledge from ChromaDB |
| LLMThreatJudge | Judges suspicious or behavior-based inputs |
| LLMSecurityAnalyzer | Adds secondary reasoning for detected incidents |
| Decision Fusion | Combines rule-based and LLM-assisted judgment |
| DefenseSimulator | Simulates response actions without changing real systems |

This makes the system more stable, explainable, and safer than an LLM-only security tool.

---

## System Architecture

> Suggested image path after adding your architecture diagram:
>
> `docs/architecture.png`

```text
User Input / Payload / Log
        |
        v
Rule-Based Detector
        |
        v
Signal Extraction
        |
        v
LLM Threat Judge
        |
        v
Decision Fusion
        |
        v
RAG Knowledge Retrieval
        |
        v
Blue-Team Report / Simulated Response
```

After adding an image, use:

```md
![System Architecture](docs/architecture.png)
```

---

## Pipeline Flow

1. The user enters a payload, security log, or security question.
2. The system checks whether the input is a follow-up question.
3. `RuleBasedDetector` checks known attack patterns such as SQL Injection, XSS, Path Traversal, and Command Injection.
4. `extract_signals()` extracts suspicious indicators such as encoded payload patterns, suspicious keywords, repeated login attempts, and anomaly indicators.
5. `LLMThreatJudge` evaluates clean but suspicious inputs.
6. `Decision Fusion` determines final risk and action.
7. `RAGQA` retrieves relevant knowledge from the structured blue-team knowledge base.
8. `LLMSecurityAnalyzer` adds secondary analysis.
9. `DefenseSimulator` outputs simulated defensive action.
10. The final report is normalized to Traditional Chinese using OpenCC.

---

## Features

### Detection and Analysis

- Rule-based detection for known high-confidence attacks
- LLM-assisted judgment for behavior-based or ambiguous inputs
- Signal extraction before LLM judgment
- Anomaly score for possible unknown or zero-day-like behavior
- Hybrid decision fusion between rule-based logic and LLM analysis

### RAG and Knowledge

- Structured RAG v2 knowledge base
- ChromaDB vector storage
- Hugging Face embedding model
- Section-aware retrieval for topics such as detection logic, risk, defense, and incident response

### Reliability and Safety

- Rule-based `ALERT` results cannot be downgraded by the LLM
- LLM decision only affects clean-detector suspicious inputs
- Fail-safe fallback when Ollama or the LLM is unavailable
- LLM status visibility: `ACTIVE` / `FALLBACK`
- Simulated defense only; no real firewall or system changes

### Interaction

- Contextual follow-up support
- Point-based follow-up support
- Traditional Chinese output normalization with OpenCC
- Blue-team focused report generation

---

## Example Demo Cases

| Case | Input | Expected Behavior |
|---|---|---|
| SQL Injection | `?id=1' OR '1'='1` | Rule-based SQL Injection detection, BLOCK |
| XSS | `<script>alert(1)</script>` | Rule-based XSS detection, defensive recommendations |
| Brute Force Log | `login failed 50 times from same IP in 1 minute` | LLM-assisted suspicious finding, BLOCK |
| Normal Input | `user login success` | Not treated as high-risk |
| Anomaly / Possible Zero-Day | `xJ12#@!$ unusual pattern ??? exec??` | Anomaly-based detection, possible zero-day |
| LLM Down | Brute force log while Ollama is off | Fail-safe fallback suspicious report |

---

## Example Output

```text
LLM-assisted suspicious finding
Suggested Attack Types: Brute Force
Recommended Risk: HIGH
Recommended Action: BLOCK
Confidence: 0.90
Reasoning: The input describes a high volume of failed login attempts from a single source.
LLM Status: ACTIVE
Final Risk: HIGH
Final Decision: BLOCK
Decision influenced by AI analysis

Threat Intelligence Analysis
Why Suspicious: High-frequency failed login attempts from the same IP.
Detected Signals: same ip, 50 times, login failed
Attack Pattern Explanation: Brute Force
Risk Reasoning: Recommended risk is HIGH based on confidence and observed signals.
```

---

## Technologies Used

- Python
- LangChain
- ChromaDB
- Hugging Face sentence-transformers
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
├── README.md
├── REPORT.md
├── chroma_db/
├── docs/
│   └── architecture.png
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
    └── ingest.py
```

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

If OpenCC is not available, install one of the following:

```bash
pip install opencc
```

or

```bash
pip install opencc-python-reimplemented
```

### 2. Start Ollama

Make sure Ollama is running and the required models are available:

```bash
ollama list
```

Required models:

```text
qwen2.5:7b
gemma4:e4b
```

### 3. Build the RAG knowledge base

```bash
python ingest_knowledge.py
```

### 4. Run the system

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
- Rule-based alerts cannot be downgraded by the LLM.
- LLM output is used as assisted analysis and controlled decision support.

---

## Current Project Status

This version represents a stable milestone.

Completed:

- Rule-based attack detection
- RAG v2 structured knowledge base
- LLM-assisted threat judgment
- Signal extraction
- Hybrid decision fusion
- Anomaly-based possible zero-day detection
- LLM fail-safe fallback
- Contextual follow-up support
- Traditional Chinese output normalization

---

## Future Work

- Add `REPORT.md` with full demo cases and evaluation results
- Add architecture diagrams under `docs/`
- Add a web dashboard for security analysts
- Add structured JSON incident reports
- Add red-team simulation module
- Add round-based red-team vs blue-team interaction
- Add benchmark testing for retrieval and detection quality
- Add more realistic log input formats

---

<a id="繁體中文"></a>

## 繁體中文

## 專案簡介

本專案是一套 AI 輔助的藍隊資安威脅偵測與應變系統，主要用於分析可疑 payload、安全日誌與資安問題。

系統結合：

- Rule-Based Detector
- 結構化 RAG 知識庫
- Signal Extraction 訊號萃取
- LLM Threat Judge
- Hybrid Decision Fusion
- Anomaly Detection
- LLM fail-safe fallback

本系統定位為**防禦分析、學術展示與模擬應變系統**，不是攻擊工具。

---

## 核心概念

本系統不是單純依賴 LLM 判斷，也不是只靠固定規則。

設計方式是：

| 模組 | 功能 |
|---|---|
| Rule-Based Detector | 偵測已知攻擊特徵 |
| Signal Extraction | 萃取可疑訊號 |
| RAGQA | 從藍隊知識庫檢索相關內容 |
| LLMThreatJudge | 判斷模糊或行為型攻擊 |
| LLMSecurityAnalyzer | 對已偵測事件提供輔助分析 |
| Decision Fusion | 融合規則判斷與 AI 分析 |
| DefenseSimulator | 模擬防禦回應 |

這樣可以兼顧穩定性、可解釋性與 AI 推理能力。

---

## 系統架構

```text
使用者輸入 / Payload / Log
        |
        v
Rule-Based Detector
        |
        v
Signal Extraction
        |
        v
LLM Threat Judge
        |
        v
Decision Fusion
        |
        v
RAG Knowledge Retrieval
        |
        v
Blue-Team Report / Simulated Response
```

未來可將架構圖放在：

```text
docs/architecture.png
```

並在 README 中加入：

```md
![System Architecture](docs/architecture.png)
```

---

## 主要功能

- 偵測 SQL Injection、XSS、Path Traversal、Command Injection
- 使用 RAG 提供資安知識解釋
- 使用 LLM 判斷行為型或模糊攻擊
- 使用 signals 輔助 AI 判斷
- 對疑似未知攻擊產生 anomaly score
- AI 掛掉時仍可使用 fallback 判斷
- 支援上下文追問
- 使用 OpenCC 強制繁體中文輸出
- 輸出藍隊分析報告與模擬應變建議

---

## Demo 測試案例

| 類型 | 測試輸入 | 預期結果 |
|---|---|---|
| SQL Injection | `?id=1' OR '1'='1` | Rule-Based 命中，BLOCK |
| XSS | `<script>alert(1)</script>` | Rule-Based 命中，產生防禦建議 |
| Brute Force | `login failed 50 times from same IP in 1 minute` | LLM 判斷為可疑，BLOCK |
| 正常輸入 | `user login success` | 不應誤判為高風險 |
| 疑似未知攻擊 | `xJ12#@!$ unusual pattern ??? exec??` | 觸發 anomaly-based detection |
| LLM 關閉 | 關閉 Ollama 後輸入 Brute Force log | 啟用 fallback |

---

## 執行方式

### 1. 安裝套件

```bash
pip install -r requirements.txt
```

### 2. 啟動 Ollama

確認模型存在：

```bash
ollama list
```

需要：

```text
qwen2.5:7b
gemma4:e4b
```

### 3. 建立 RAG 知識庫

```bash
python ingest_knowledge.py
```

### 4. 啟動系統

```bash
python app.py
```

---

## 安全限制

本系統只做防禦分析與模擬：

- 不攻擊真實目標
- 不修改防火牆
- 不進行真實封鎖
- `BLOCK / MONITOR / ALLOW` 都是模擬決策
- LLM 不會覆蓋 Rule-Based ALERT
- LLM 僅作為輔助判斷與決策融合來源

---

## 專案目前狀態

目前已完成：

- Rule-Based 偵測
- RAG v2 結構化知識庫
- LLM Threat Judge
- Signal Extraction
- Hybrid Decision Fusion
- Anomaly-based possible zero-day detection
- LLM fail-safe fallback
- Contextual follow-up
- OpenCC 繁體中文輸出控制

---

## 未來規劃

- 補上 `REPORT.md`，整理完整 demo 與測試結果
- 補上系統架構圖
- 加入 Web dashboard
- 支援 JSON incident report
- 建立 Red-Team Simulator
- 做紅隊 vs 藍隊回合制模擬
- 建立 retrieval / detection benchmark
