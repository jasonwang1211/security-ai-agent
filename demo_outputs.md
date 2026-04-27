# Demo Outputs

## Startup Output

Status: Passed

```text
(venv) PS C:\Users\jason\Desktop\sentinel_project> python app.py
正在啟動 Security AI...
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|███████████████████████████████████████████████████████████████| 103/103 [00:00<00:00, 7718.80it/s]
BertModel LOAD REPORT from: sentence-transformers/all-MiniLM-L6-v2
Key                     | Status     |  | 
------------------------+------------+--+-
embeddings.position_ids | UNEXPECTED |  | 

Notes:
- UNEXPECTED:   can be ignored when loading from different task/architecture; not ok if you expect identical arch.
Failed to send telemetry event ClientStartEvent: capture() takes 1 positional argument but 3 were given
Failed to send telemetry event ClientCreateCollectionEvent: capture() takes 1 positional argument but 3 were given

Security AI 已啟動。
```

## Demo Case 1: SQL Injection

Status: Passed

```text
你: ?id=1' OR '1'='1
分析中...
Failed to send telemetry event CollectionQueryEvent: capture() takes 1 positional argument but 3 were given

AI: 藍隊分析報告
攻擊摘要：偵測到可能的攻擊類型：SQL Injection
攻擊類型：SQL Injection
命中簽章：
- SQL Injection: ' or '1'='1
風險等級：HIGH
判定動作：BLOCK
模擬防禦：已模擬封鎖這次可疑請求，未實際修改任何系統或防火牆設定。

防禦建議：
SQL Injection:
- 使用參數化查詢或 prepared statements，避免字串拼接 SQL。
- 驗證與限制使用者輸入格式，避免危險字元直接進入查詢。
- 優先使用 ORM 或安全的資料存取層來降低手寫 SQL 風險。

Incident Response Checklist:
1. 先確認影響範圍並保留相關請求、日誌與證據。
2. 暫時阻擋或限制可疑來源、輸入點或受影響功能。
3. 檢查是否已有資料外洩、權限提升或檔案讀取跡象。
4. 修補對應弱點後再重新驗證是否仍可重現。
5. 補上監控、告警與輸入驗證，避免同類事件再次發生。

補充說明：
根據提供的內容，此可疑輸入 `?id=1' OR '1'='1` 屬於 SQL Injection 攻擊。此 Payload 通常被用來進行布爾繞過攻擊（boolean-based blind SQL injection），通過修改查詢條件使資料庫返回預期結果，進而獲取敏感信息或繞過驗證。

攻擊類型：SQL Injection

AI-Assisted Analysis
Reasoning: Rule-based detection identified a classic SQL Injection payload (' OR '1'='1') in the query parameter.
Possible Attack Types: SQL Injection
Recommended Decision: BLOCK
Confidence: 0.95
```

## Demo Case 2: XSS

Status: Passed

```text
你: <script>alert(1)</script>
分析中...

AI: 藍隊分析報告
攻擊摘要：偵測到可能的攻擊類型：XSS
攻擊類型：XSS
命中簽章：
- XSS: <script>, alert(
風險等級：MEDIUM
判定動作：MONITOR
模擬防禦：已模擬將此事件加入監控與告警佇列，未實際部署監控規則。

防禦建議：
XSS:
- 輸出到 HTML 前先做適當跳脫，避免惡意腳本被瀏覽器執行。
- 啟用 Content Security Policy (CSP) 限制可執行腳本來源。
- 避免直接信任使用者輸入，特別是可回顯到頁面的欄位。

Incident Response Checklist:
1. 先確認影響範圍並保留相關請求、日誌與證據。
2. 暫時阻擋或限制可疑來源、輸入點或受影響功能。
3. 檢查是否已有資料外洩、權限提升或檔案讀取跡象。
4. 修補對應弱點後再重新驗證是否仍可重現。
5. 補上監控、告警與輸入驗證，避免同類事件再次發生。

AI-Assisted Analysis
Reasoning: Rule-based detector flagged the input as suspicious. Detected attack types: XSS. Current risk level: MEDIUM.
Possible Attack Types: XSS
Recommended Decision: MONITOR
Confidence: 0.90
```

## Demo Case 3: Brute Force Behavior

Status: Passed

```text
你: login failed 50 times from same IP in 1 minute
分析中...

AI: LLM-assisted suspicious finding
Suggested Attack Types: Brute Force, Credential Stuffing
Recommended Risk: HIGH
Recommended Action: BLOCK
Confidence: 0.85
Reasoning: The query describes repeated failed login attempts (50 times in 1 minute) from a single source, which is a classic indicator of a brute force or credential stuffing attack, regardless of the detector's CLEAN status.
LLM Status: ACTIVE
Final Risk: HIGH
Final Decision: BLOCK
Decision influenced by AI analysis

Threat Intelligence Analysis
Why Suspicious: The query describes repeated failed login attempts (50 times in 1 minute) from a single source, which is a classic indicator of a brute force or credential stuffing attack, regardless of the detector's CLEAN status.
Detected Signals: same ip, 50 times, login failed
Attack Pattern Explanation: Brute Force, Credential Stuffing
Risk Reasoning: Recommended risk is HIGH based on confidence 0.85 and observed signals.
```

## Demo Case 4: Normal Input

Status: Passed

```text
你: user login success
分析中...

AI: 請提出資安相關問題，或直接貼上可疑 payload 讓我協助判斷。
```

## Demo Case 5: Anomaly / Possible Zero-Day

Status: Passed

```text
你: xJ12#@!$ unusual pattern ??? exec??
分析中...

AI: LLM-assisted suspicious finding
Suggested Attack Types: Command Injection, Path Traversal
Recommended Risk: MEDIUM
Recommended Action: MONITOR
Confidence: 0.90
Reasoning: The query contains highly unusual characters, mixed case, and explicit command-like sequences ('exec??'), indicating potential command injection or path traversal attempts, despite the detector being CLEAN.
LLM Status: ACTIVE
Final Risk: HIGH
Final Decision: MONITOR
Decision influenced by AI analysis
Anomaly-based detection triggered (possible zero-day)

Threat Intelligence Analysis
Why Suspicious: The query contains highly unusual characters, mixed case, and explicit command-like sequences ('exec??'), indicating potential command injection or path traversal attempts, despite the detector being CLEAN.
Detected Signals: unusual
Attack Pattern Explanation: Command Injection, Path Traversal
Risk Reasoning: Recommended risk is MEDIUM based on confidence 0.90 and observed signals.
```

## Demo Case 6: RAG Security QA

Status: Passed

```text
你: 什麼是 XSS
分析中...

AI: XSS，即跨站腳本攻擊（Cross-Site Scripting），是指攻擊者將惡意腳本注入可被其他使用者瀏覽的內容中，藉此竊取 Session、操 控頁面或冒用使用者行為。
```

## Demo Case 7: Contextual Follow-up

Status: Passed

```text
你: 詳細說明
分析中...

AI: XSS 攻擊主要分為三種類型：反射型 XSS、儲存型 XSS 和基於 DOM 的 XSS。攻擊者利用這些漏洞，將惡意腳本注入到網頁中，當其他使用者瀏覽該頁面時，瀏覽器會執行這些腳本。

1. **反射型 XSS**：惡意腳本通過 URL 反射回伺服器，例如在留言板或搜索欄輸入惡意代碼後按送出。攻擊者可以利用這種方式竊取其他使用者的 Cookie 或 Session 信息。
2. **儲存型 XSS**：惡意腳本被永久儲存在伺服器端資料庫中，當其他使用者訪問相關頁面時，瀏覽器會執行這些已儲存的腳本。
3. **基於 DOM 的 XSS**：這種攻擊方式不涉及伺服器端代碼，而是利用 JavaScript 來操控頁面內容。攻擊者通過注入惡意 JavaScript 代碼，影響客戶端渲染。

防禦措施包括：
- 使用輸入驗證和過濾。
- 設置 Content-Security-Policy (CSP) 頭部。
- 使用同源策略限制跨站腳本的執行環境。
```

## Demo Case 8: LLM Fail-safe Fallback

Status: Passed with note

```text
你: login failed 50 times from same IP in 1 minute
分析中...

AI: Fallback Suspicious Finding (LLM unavailable)
Reasoning: High-frequency failed logins from the same IP may indicate brute-force activity.
Recommended Action: BLOCK
Risk: HIGH
Note: LLM unavailable, heuristic fallback used
LLM Status: FALLBACK

你: exit
再見。
```
