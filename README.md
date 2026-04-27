# AI-driven Security Threat Detection and Response System

> Hybrid AI Security Agent for blue-team threat detection, RAG-based explanation, LLM-assisted judgment, anomaly detection, decision fusion, and fail-safe response simulation.

[English](#english) | [繁體中文](#繁體中文)

---

<a id="english"></a>

# English

## Overview

This project is an AI-assisted blue-team security analysis system. It analyzes suspicious payloads, security logs, and security-related questions through a hybrid pipeline that combines:

- Rule-based detection
- Signal extraction
- LLM-based threat judgment
- Hybrid decision fusion
- Structured RAG knowledge retrieval
- Anomaly-based possible zero-day detection
- Fail-safe fallback when the LLM is unavailable

The system is designed for **defensive security analysis, academic demonstration, and simulation**. It is not an offensive automation tool.

---

## Key Idea

Pure rule-based systems are reliable for known attacks, but they struggle with behavior-based or ambiguous threats.

Pure LLM-based systems are flexible, but they may hallucinate, misclassify security events, or weaken deterministic security decisions.

This project uses a hybrid design:

| Component | Role |
|---|---|
| Rule-Based Detector | Detects known attack signatures and remains the primary safety layer |
| Signal Extraction | Extracts suspicious indicators before LLM judgment |
| LLMThreatJudge | Judges clean-but-suspicious behavior or log-like inputs |
| Decision Fusion | Combines rule-based results and LLM-assisted analysis |
| RAGQA | Retrieves structured blue-team knowledge from ChromaDB |
| LLMSecurityAnalyzer | Adds secondary analysis for detected incidents |
| DefenseSimulator | Simulates blue-team response actions without modifying real systems |
| OpenCC Output Control | Normalizes generated output into Traditional Chinese |

The goal is to create a system that is **more explainable, safer, and more stable than an LLM-only security tool**.

---

## System Architecture

![System Architecture](docs/architecture_en.png)


---

## Pipeline Flow

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

### Flow Description

1. The user enters a payload, security log, or security question.
2. The system checks whether the input is a follow-up question.
3. `RuleBasedDetector` detects known attack patterns such as SQL Injection, XSS, Path Traversal, and Command Injection.
4. `extract_signals()` extracts suspicious indicators such as encoded payload patterns, suspicious keywords, repeated login attempts, and anomaly indicators.
5. `LLMThreatJudge` evaluates clean but suspicious inputs.
6. `Decision Fusion` determines final risk and action.
7. `RAGQA` retrieves relevant knowledge from the structured blue-team knowledge base.
8. `LLMSecurityAnalyzer` adds secondary reasoning for detected incidents.
9. `DefenseSimulator` outputs simulated defensive actions.
10. The final output is normalized to Traditional Chinese using OpenCC.

---

## Features

### Detection and Analysis

- Rule-based detection for known high-confidence attacks
- LLM-assisted judgment for behavior-based or ambiguous inputs
- Signal extraction before LLM threat judgment
- Anomaly score for possible unknown or zero-day-like behavior
- Hybrid decision fusion between deterministic logic and LLM analysis

### RAG and Knowledge

- Structured RAG v2 knowledge base
- ChromaDB vector storage
- Hugging Face sentence-transformers embedding model
- Section-aware retrieval for:
  - attack explanation
  - detection logic
  - risk analysis
  - defense recommendations
  - incident response procedures

### Reliability and Safety

- Rule-based `ALERT` results cannot be downgraded by the LLM
- LLM decisions only affect clean-detector suspicious inputs
- Fail-safe fallback when Ollama or the LLM is unavailable
- LLM status visibility: `ACTIVE` / `FALLBACK`
- Simulated defense only; no real firewall or system control is performed

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
For full demo outputs and evaluation details, see:

[Demo & Evaluation Report](REPORT.md)
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
    └── ingest.py
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

If `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

If `requirements.txt` does not exist yet, install the main packages manually:

```bash
pip install langchain langchain-community langchain-core langchain-text-splitters chromadb sentence-transformers opencc-python-reimplemented
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
- Rule-based alerts cannot be downgraded by the LLM.
- RAG is used for explanation and knowledge support, not primary detection.
- LLM output is used as assisted analysis and controlled decision support.

---

## Current Project Status

This version represents a stable milestone.

Completed:

- Rule-based attack detection
- Structured RAG v2 knowledge base
- LLM-assisted threat judgment
- Signal extraction
- Hybrid decision fusion
- Anomaly-based possible zero-day detection
- LLM fail-safe fallback
- Contextual follow-up support
- Traditional Chinese output normalization
- GitHub README architecture documentation

---

## Future Work

- Expand `REPORT.md` with more benchmark cases and raw test logs
- Add more realistic log input formats
- Add structured JSON incident reports
- Add a web dashboard for analysts
- Add benchmark testing for retrieval and detection quality
- Add red-team simulation module
- Add round-based red-team vs blue-team interaction
- Explore real-time traffic or log ingestion

---

<a id="繁體中文"></a>

# 繁體中文

## 專案簡介

本專案是一套 AI 輔助的藍隊資安威脅偵測與應變系統，主要用於分析可疑 payload、安全日誌與資安相關問題。

系統結合：

- Rule-Based Detector
- Signal Extraction 訊號萃取
- LLM Threat Judge
- Hybrid Decision Fusion
- 結構化 RAG 知識庫
- Anomaly-based possible zero-day detection
- LLM fail-safe fallback

本系統定位為**防禦分析、學術展示與模擬應變系統**，不是攻擊工具。

---

## 核心概念

本系統不是單純依賴 LLM 判斷，也不是只靠固定規則。

設計方式是：

| 模組 | 功能 |
|---|---|
| Rule-Based Detector | 偵測已知攻擊特徵，作為主要安全判斷層 |
| Signal Extraction | 萃取可疑關鍵字、編碼痕跡與異常訊號 |
| LLMThreatJudge | 判斷模糊攻擊、行為型攻擊與可疑日誌 |
| Decision Fusion | 融合規則判斷與 AI 分析，形成最終風險與決策 |
| RAGQA | 從藍隊知識庫檢索相關內容 |
| LLMSecurityAnalyzer | 對已偵測事件提供輔助分析 |
| DefenseSimulator | 模擬藍隊防禦回應，不修改真實系統 |
| OpenCC Output Control | 將輸出穩定轉為繁體中文 |

這樣可以兼顧穩定性、可解釋性與 AI 推理能力。

---

## 系統架構

![系統架構](docs/architecture_zh.png)


---

## 流程說明

```text
使用者輸入 / Payload / 日誌
        |
        v
規則式偵測器
        |
        v
訊號萃取
        |
        v
LLM 威脅判斷器
        |
        v
決策融合
        |
        v
RAG 知識檢索
        |
        v
藍隊報告 / 模擬應變輸出
```

### 詳細流程

1. 使用者輸入 payload、日誌或資安問題。
2. 系統先判斷是否為上下文追問。
3. `RuleBasedDetector` 偵測 SQL Injection、XSS、Path Traversal、Command Injection 等已知攻擊。
4. `extract_signals()` 萃取可疑訊號，例如編碼痕跡、可疑關鍵字、登入失敗次數與異常指標。
5. `LLMThreatJudge` 分析規則未命中但仍可疑的輸入。
6. `Decision Fusion` 融合規則判斷與 LLM 分析，產生最終風險與最終決策。
7. `RAGQA` 從結構化藍隊知識庫檢索相關知識。
8. `LLMSecurityAnalyzer` 對已偵測事件提供輔助分析。
9. `DefenseSimulator` 產生模擬藍隊應變輸出。
10. 最終輸出使用 OpenCC 控制為繁體中文。

---

## 主要功能

### 偵測與分析

- 偵測 SQL Injection、XSS、Path Traversal、Command Injection
- 使用 LLM 判斷行為型或模糊攻擊
- 使用 signals 輔助 AI 判斷
- 對疑似未知攻擊產生 anomaly score
- 使用 Hybrid Decision Fusion 產生最終風險與決策

### RAG 與知識庫

- 結構化 RAG v2 知識庫
- ChromaDB 向量資料庫
- Hugging Face embedding model
- 支援攻擊解釋、偵測邏輯、風險分析、防禦建議與應變流程檢索

### 可靠性與安全性

- Rule-Based `ALERT` 不會被 LLM 降級
- LLM 只會影響規則未命中但具可疑性的輸入
- Ollama / LLM 不可用時會啟用 fail-safe fallback
- 顯示 LLM 狀態：`ACTIVE` / `FALLBACK`
- 防禦動作皆為模擬，不會修改真實系統或防火牆

### 互動能力

- 支援上下文追問
- 支援「第幾點」延伸說明
- 使用 OpenCC 強制繁體中文輸出
- 產生藍隊導向分析報告

---

## Demo 測試案例

| 類型 | 測試輸入 | 預期結果 |
|---|---|---|
| SQL Injection | `?id=1' OR '1'='1` | Rule-Based 命中，BLOCK |
| XSS | `<script>alert(1)</script>` | Rule-Based 命中，產生防禦建議 |
| Brute Force | `login failed 50 times from same IP in 1 minute` | LLM 判斷為可疑，BLOCK |
| 正常輸入 | `user login success` | 不應誤判為高風險 |
| 疑似未知攻擊 | `xJ12#@!$ unusual pattern ??? exec??` | 觸發 anomaly-based detection |
| LLM 關閉 | 關閉 Ollama 後輸入 Brute Force log | 啟用 fallback suspicious report |
完整 demo 輸出與測試結果請參考：

[Demo & Evaluation Report](REPORT.md)
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

如果專案內已有 `requirements.txt`：

```bash
pip install -r requirements.txt
```

如果還沒有 `requirements.txt`，可先手動安裝主要套件：

```bash
pip install langchain langchain-community langchain-core langchain-text-splitters chromadb sentence-transformers opencc-python-reimplemented
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
- 不修改防火牆
- 不進行真實封鎖
- `BLOCK / MONITOR / ALLOW` 都是模擬決策
- LLM 不會覆蓋 Rule-Based ALERT
- RAG 只用於解釋與知識支援，不作為主要偵測依據
- LLM 僅作為輔助判斷與受控決策融合來源

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
- GitHub README 架構文件

---

## 未來規劃

- 擴充 `REPORT.md`，加入更多 benchmark case 與原始測試紀錄
- 支援更真實的 log input 格式
- 支援 JSON incident report
- 加入 Web dashboard
- 建立 retrieval / detection benchmark
- 建立 Red-Team Simulator
- 做紅隊 vs 藍隊回合制模擬
- 探索即時流量或日誌輸入
