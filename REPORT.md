# Demo & Evaluation Report

> Project: AI-driven Security Threat Detection and Response System  
> Version: Stable Demo Milestone  
> Purpose: Demonstrate known-attack detection, LLM-assisted behavior analysis, anomaly-based possible zero-day detection, and fail-safe fallback behavior.

[English](#english) | [繁體中文](#繁體中文)

---

<a id="english"></a>

# English

## 1. Report Overview

This report documents the current demo and evaluation results of the AI-driven Security Threat Detection and Response System.

The system is designed as a blue-team security analysis prototype. It combines:

- Rule-based detection for known attack patterns
- Signal extraction for suspicious indicators
- LLM-assisted threat judgment
- Hybrid decision fusion
- Structured RAG knowledge support
- Anomaly-based possible zero-day detection
- LLM fail-safe fallback

This report focuses on functional demonstration rather than large-scale benchmark testing.

---

## 2. Evaluation Goals

The demo is designed to verify six core capabilities:

| Goal | Description |
|---|---|
| Known Attack Detection | Detect clear SQL Injection and XSS payloads |
| Behavior-based Detection | Detect suspicious login behavior that is not a simple payload |
| Normal Input Handling | Avoid treating benign input as a high-risk threat |
| Anomaly Detection | Identify suspicious unknown or unusual inputs |
| RAG Knowledge Support | Answer security knowledge questions |
| Fail-safe Behavior | Continue conservative analysis when the LLM is unavailable |

---

## 3. Test Environment

| Item | Configuration |
|---|---|
| Operating System | Windows |
| Runtime | Python virtual environment |
| Interface | Command-line interface |
| Vector Database | ChromaDB |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| RAG LLM | `qwen2.5:7b` |
| Agent / Threat Judge LLM | `gemma4:e4b` |
| Local LLM Runtime | Ollama |
| Output Control | OpenCC / Traditional Chinese output normalization |

---

## 4. Demo Cases Summary

| ID | Category | Test Input | Expected Behavior | Result |
|---|---|---|---|---|
| D01 | SQL Injection | `?id=1' OR '1'='1` | Rule-based SQL Injection detection, BLOCK | Passed |
| D02 | XSS | `<script>alert(1)</script>` | Rule-based XSS detection, defensive recommendations | Passed |
| D03 | Brute Force Log | `login failed 50 times from same IP in 1 minute` | LLM-assisted suspicious finding, BLOCK | Passed |
| D04 | Normal Input | `user login success` | Not treated as high-risk | Passed |
| D05 | Anomaly / Possible Zero-Day | `xJ12#@!$ unusual pattern ??? exec??` | Anomaly-based detection, possible zero-day | Passed |
| D06 | LLM Unavailable | Brute force log while Ollama is off | Fail-safe fallback suspicious report | Passed |
| D07 | Security Knowledge QA | `什麼是 XSS` | RAG-based knowledge answer | Passed |
| D08 | Contextual Follow-up | `詳細說明` after a security answer | Context-aware follow-up answer | Passed |

---

## 5. Detailed Demo Results

## D01 — SQL Injection Detection

### Input

```text
?id=1' OR '1'='1
```

### Expected Result

The system should identify the payload as SQL Injection through rule-based detection and recommend a high-risk response.

### Observed Result

```text
攻擊類型：SQL Injection
命中簽章：
- SQL Injection: ' or '1'='1
風險等級：HIGH
判定動作：BLOCK
```

### Evaluation

Passed.

The payload contains a high-confidence SQL Injection pattern. The rule-based detector correctly identifies the attack and the system recommends `BLOCK`.

---

## D02 — XSS Detection

### Input

```html
<script>alert(1)</script>
```

### Expected Result

The system should identify the input as XSS and provide defensive recommendations.

### Observed Result

```text
攻擊類型：XSS
命中簽章：
- XSS: <script>, alert(
風險等級：MEDIUM
判定動作：MONITOR

防禦建議：
- 輸出到 HTML 前先做適當跳脫
- 啟用 Content Security Policy (CSP)
- 避免直接信任使用者輸入
```

### Evaluation

Passed.

The system correctly identifies known XSS indicators and provides blue-team defensive recommendations.

---

## D03 — Brute Force Behavior Detection

### Input

```text
login failed 50 times from same IP in 1 minute
```

### Expected Result

This input does not contain a traditional web attack payload. The system should use signal extraction and LLM-assisted judgment to classify it as suspicious login behavior.

### Observed Result

```text
LLM-assisted suspicious finding
Suggested Attack Types: Brute Force
Recommended Risk: HIGH
Recommended Action: BLOCK
Confidence: 0.90
LLM Status: ACTIVE
Final Risk: HIGH
Final Decision: BLOCK
Decision influenced by AI analysis
```

### Detected Signals

```text
same ip, 50 times, login failed
```

### Evaluation

Passed.

The system successfully detects behavior-based suspicious activity. This demonstrates that the system is not limited to fixed payload signatures.

---

## D04 — Normal Input Handling

### Input

```text
user login success
```

### Expected Result

The system should not treat this as a high-risk threat.

### Observed Result

```text
請提出資安相關問題，或直接貼上可疑 payload 讓我協助判斷。
```

### Evaluation

Passed.

The input is not treated as a high-risk event. This helps verify basic false-positive control.

---

## D05 — Anomaly / Possible Zero-Day Detection

### Input

```text
xJ12#@!$ unusual pattern ??? exec??
```

### Expected Result

The input does not directly match a known rule-based signature, but it contains suspicious structure and command-related hints. The system should mark it as an anomaly or possible zero-day-like behavior.

### Observed Result

```text
LLM-assisted suspicious finding
Suggested Attack Types: Command Injection, Injection
Recommended Risk: HIGH
Recommended Action: BLOCK
Confidence: 0.80
Final Risk: HIGH
Final Decision: MONITOR
Anomaly-based detection triggered (possible zero-day)
```

### Evaluation

Passed.

The system identifies the input as suspicious even without a direct rule-based match. The final decision remains conservative by selecting `MONITOR`, which is appropriate for uncertain anomaly-based findings.

---

## D06 — Fail-safe Behavior When LLM Is Unavailable

### Setup

Ollama was intentionally stopped before running the test.

Example command:

```powershell
taskkill /IM ollama.exe /F
```

### Input

```text
login failed 50 times from same IP in 1 minute
```

### Expected Result

The system should not silently fail or treat the input as a normal question. It should return a fallback suspicious report.

### Observed Result

```text
Fallback Suspicious Finding (LLM unavailable)
Reasoning: High-frequency failed logins from the same IP may indicate brute-force activity.
Recommended Action: BLOCK
Risk: HIGH
Note: LLM unavailable, heuristic fallback used
LLM Status: FALLBACK
```

### Evaluation

Passed.

The system continues to provide conservative defensive analysis even when the LLM service is unavailable.

---

## D07 — RAG Security Knowledge QA

### Input

```text
什麼是 XSS
```

### Expected Result

The system should answer as a security knowledge question using RAG-supported context.

### Observed Result

```text
XSS，即跨站腳本攻擊（Cross-Site Scripting），是指攻擊者將惡意腳本注入可被其他使用者瀏覽的內容中，藉此竊取 Session、操控頁面或冒用使用者行為。
```

### Evaluation

Passed.

The system successfully handles security knowledge questions separately from attack payload detection.

---

## D08 — Contextual Follow-up

### Input Sequence

```text
什麼是 XSS
詳細說明
```

### Expected Result

The second query should be treated as a follow-up question and remain within the XSS context.

### Observed Result

```text
XSS 攻擊主要分為三種類型：反射型 XSS、儲存型 XSS 和基於 DOM 的 XSS...
```

### Evaluation

Passed.

The system maintains conversational context and answers follow-up questions without requiring the user to repeat the full topic.

---

## 6. Overall Evaluation

| Capability | Result |
|---|---|
| Known payload detection | Passed |
| Behavior-based suspicious detection | Passed |
| Normal input rejection / non-high-risk handling | Passed |
| Anomaly-based possible zero-day detection | Passed |
| LLM fail-safe fallback | Passed |
| RAG security QA | Passed |
| Contextual follow-up | Passed |

Overall result:

```text
Stable demo milestone achieved.
```

---

## 7. Key Findings

1. Rule-based detection is effective for clear SQL Injection and XSS payloads.
2. Signal extraction improves LLM-assisted judgment by providing structured indicators.
3. LLMThreatJudge can identify suspicious behavior that does not match static signatures.
4. Decision Fusion allows LLM analysis to influence clean-detector suspicious cases while preserving rule-based safety.
5. Anomaly-based detection provides an initial possible zero-day analysis path.
6. Fail-safe fallback prevents suspicious log-like inputs from being ignored when Ollama is unavailable.
7. RAG remains useful for explanation and knowledge support, but it is not used as the primary detection layer.

---

## 8. Limitations

This demo is a functional prototype and does not yet include:

- Large-scale benchmark dataset
- Precision / recall / F1-score measurement
- Real network traffic ingestion
- Real firewall or WAF integration
- Web dashboard
- Multi-user authentication
- Long-term event storage
- Production-grade monitoring

The current `BLOCK`, `MONITOR`, and `ALLOW` outputs are simulated decisions.

---

## 9. Suggested Next Steps

Recommended next development tasks:

1. Add more realistic log formats.
2. Create a structured JSON incident report output.
3. Build a small benchmark dataset for SQL Injection, XSS, Brute Force, normal traffic, and anomaly cases.
4. Add evaluation metrics such as:
   - detection accuracy
   - false positive rate
   - false negative rate
   - fallback success rate
5. Add a simple web dashboard for demo presentation.
6. Build a separate red-team simulator in a later phase.

---

<a id="繁體中文"></a>

# 繁體中文

## 1. 報告概述

本文件記錄目前 AI 驅動之資安威脅偵測與應變系統的 demo 測試案例與結果。

本系統是一個藍隊導向的資安分析 prototype，整合：

- 規則式偵測
- 訊號萃取
- LLM 威脅判斷
- Hybrid Decision Fusion
- 結構化 RAG 知識檢索
- Anomaly-based possible zero-day detection
- LLM 不可用時的 fail-safe fallback

本報告重點是展示系統功能，而不是大規模量化 benchmark。

---

## 2. 測試目標

本 demo 主要驗證六項能力：

| 目標 | 說明 |
|---|---|
| 已知攻擊偵測 | 偵測 SQL Injection 與 XSS |
| 行為型攻擊判斷 | 判斷非 payload 型的登入異常行為 |
| 正常輸入處理 | 避免將正常輸入誤判為高風險 |
| 異常偵測 | 判斷疑似未知攻擊或 abnormal input |
| RAG 知識支援 | 回答資安知識問題 |
| Fail-safe | LLM 不可用時仍能保守判斷 |

---

## 3. 測試環境

| 項目 | 設定 |
|---|---|
| 作業系統 | Windows |
| 執行環境 | Python virtual environment |
| 介面 | Command-line interface |
| 向量資料庫 | ChromaDB |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| RAG LLM | `qwen2.5:7b` |
| Agent / Threat Judge LLM | `gemma4:e4b` |
| LLM Runtime | Ollama |
| 輸出控制 | OpenCC / 繁體中文輸出控制 |

---

## 4. Demo 測試總表

| ID | 類型 | 測試輸入 | 預期結果 | 結果 |
|---|---|---|---|---|
| D01 | SQL Injection | `?id=1' OR '1'='1` | Rule-Based 命中，BLOCK | 通過 |
| D02 | XSS | `<script>alert(1)</script>` | Rule-Based 命中，產生防禦建議 | 通過 |
| D03 | Brute Force Log | `login failed 50 times from same IP in 1 minute` | LLM 判斷可疑，BLOCK | 通過 |
| D04 | 正常輸入 | `user login success` | 不應判為高風險 | 通過 |
| D05 | 疑似未知攻擊 | `xJ12#@!$ unusual pattern ??? exec??` | 觸發 anomaly-based detection | 通過 |
| D06 | LLM 不可用 | 關閉 Ollama 後輸入 Brute Force log | 啟用 fallback suspicious report | 通過 |
| D07 | 資安知識問答 | `什麼是 XSS` | RAG 知識回答 | 通過 |
| D08 | 上下文追問 | `詳細說明` | 延續前一個資安主題回答 | 通過 |

---

## 5. 詳細測試結果

## D01 — SQL Injection 偵測

### 輸入

```text
?id=1' OR '1'='1
```

### 預期結果

系統應透過 Rule-Based Detector 判斷為 SQL Injection，並給出 BLOCK 建議。

### 實際結果

```text
攻擊類型：SQL Injection
命中簽章：
- SQL Injection: ' or '1'='1
風險等級：HIGH
判定動作：BLOCK
```

### 評估

通過。

此 payload 包含高信心 SQL Injection 特徵，系統可正確偵測並給出封鎖建議。

---

## D02 — XSS 偵測

### 輸入

```html
<script>alert(1)</script>
```

### 預期結果

系統應辨識為 XSS，並提供防禦建議。

### 實際結果

```text
攻擊類型：XSS
命中簽章：
- XSS: <script>, alert(
風險等級：MEDIUM
判定動作：MONITOR

防禦建議：
- 輸出到 HTML 前先做適當跳脫
- 啟用 Content Security Policy (CSP)
- 避免直接信任使用者輸入
```

### 評估

通過。

系統成功辨識 XSS pattern，並提供藍隊防禦建議。

---

## D03 — Brute Force 行為偵測

### 輸入

```text
login failed 50 times from same IP in 1 minute
```

### 預期結果

此輸入不是傳統 payload，而是行為描述。系統應透過 Signal Extraction 與 LLMThreatJudge 判斷為可疑。

### 實際結果

```text
LLM-assisted suspicious finding
Suggested Attack Types: Brute Force
Recommended Risk: HIGH
Recommended Action: BLOCK
Confidence: 0.90
LLM Status: ACTIVE
Final Risk: HIGH
Final Decision: BLOCK
Decision influenced by AI analysis
```

### 偵測到的訊號

```text
same ip, 50 times, login failed
```

### 評估

通過。

系統可分析非 payload 型行為，證明其不只依賴固定簽章。

---

## D04 — 正常輸入處理

### 輸入

```text
user login success
```

### 預期結果

系統不應將此輸入判斷為高風險攻擊。

### 實際結果

```text
請提出資安相關問題，或直接貼上可疑 payload 讓我協助判斷。
```

### 評估

通過。

此輸入沒有被誤判為攻擊，有助於降低誤報。

---

## D05 — 異常 / 疑似 Zero-Day 偵測

### 輸入

```text
xJ12#@!$ unusual pattern ??? exec??
```

### 預期結果

此輸入未直接命中規則，但具有異常結構與疑似命令執行線索，系統應標示為 anomaly 或 possible zero-day。

### 實際結果

```text
LLM-assisted suspicious finding
Suggested Attack Types: Command Injection, Injection
Recommended Risk: HIGH
Recommended Action: BLOCK
Confidence: 0.80
Final Risk: HIGH
Final Decision: MONITOR
Anomaly-based detection triggered (possible zero-day)
```

### 評估

通過。

系統可針對規則未命中的可疑輸入進行 anomaly-based 判斷。由於未知攻擊存在不確定性，系統採取較保守的 `MONITOR` 作為最終決策。

---

## D06 — LLM 不可用時的 Fail-safe

### 測試設定

測試前先關閉 Ollama。

範例指令：

```powershell
taskkill /IM ollama.exe /F
```

### 輸入

```text
login failed 50 times from same IP in 1 minute
```

### 預期結果

系統不應直接失效，也不應將明顯可疑的 log 當成一般問題處理，而應回傳 fallback suspicious report。

### 實際結果

```text
Fallback Suspicious Finding (LLM unavailable)
Reasoning: High-frequency failed logins from the same IP may indicate brute-force activity.
Recommended Action: BLOCK
Risk: HIGH
Note: LLM unavailable, heuristic fallback used
LLM Status: FALLBACK
```

### 評估

通過。

即使 LLM 不可用，系統仍能使用 heuristic fallback 做保守判斷，避免可疑事件被忽略。

---

## D07 — RAG 資安知識問答

### 輸入

```text
什麼是 XSS
```

### 預期結果

系統應將此視為資安知識問題，使用 RAG 支援回答。

### 實際結果

```text
XSS，即跨站腳本攻擊（Cross-Site Scripting），是指攻擊者將惡意腳本注入可被其他使用者瀏覽的內容中，藉此竊取 Session、操控頁面或冒用使用者行為。
```

### 評估

通過。

系統可正確區分知識問答與攻擊偵測流程。

---

## D08 — 上下文追問

### 輸入順序

```text
什麼是 XSS
詳細說明
```

### 預期結果

第二句應被視為上下文追問，並延續 XSS 主題回答。

### 實際結果

```text
XSS 攻擊主要分為三種類型：反射型 XSS、儲存型 XSS 和基於 DOM 的 XSS...
```

### 評估

通過。

系統可保留對話上下文，處理短句追問。

---

## 6. 整體評估

| 能力 | 結果 |
|---|---|
| 已知 payload 偵測 | 通過 |
| 行為型可疑事件判斷 | 通過 |
| 正常輸入處理 | 通過 |
| Anomaly-based possible zero-day detection | 通過 |
| LLM fail-safe fallback | 通過 |
| RAG 資安知識問答 | 通過 |
| 上下文追問 | 通過 |

整體結果：

```text
已達成穩定 demo milestone。
```

---

## 7. 測試觀察

1. Rule-Based Detector 適合偵測明確 SQL Injection 與 XSS payload。
2. Signal Extraction 能提供更結構化的可疑訊號，輔助 LLM 判斷。
3. LLMThreatJudge 能處理沒有固定簽章的行為型攻擊。
4. Decision Fusion 可讓 LLM 在安全限制下影響最終決策。
5. Anomaly Detection 提供初步 possible zero-day 分析能力。
6. Fail-safe fallback 可避免 LLM 不可用時系統失去判斷能力。
7. RAG 適合做解釋與知識支援，不作為主要偵測依據。

---

## 8. 限制

目前仍屬於 prototype，尚未包含：

- 大規模 benchmark dataset
- precision / recall / F1-score
- 真實網路流量輸入
- 真實防火牆或 WAF 串接
- Web dashboard
- 長期事件儲存
- 多人權限控管
- production-grade monitoring

目前 `BLOCK`、`MONITOR`、`ALLOW` 皆為模擬決策。

---

## 9. 後續建議

建議下一階段工作：

1. 加入更多真實 log 格式。
2. 支援 JSON incident report。
3. 建立小型測試資料集。
4. 加入基本評估指標：
   - detection accuracy
   - false positive rate
   - false negative rate
   - fallback success rate
5. 建立簡易 Web dashboard。
6. 將紅隊模擬器作為獨立模組於後續階段開發。
