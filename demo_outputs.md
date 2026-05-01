# Demo Outputs

This document shows representative CLI transcripts for the current `v1.1.4-event-to-agent-adapter` demo flow.

## Startup Output

Status: Passed

```text
(venv) PS <project_path>> python app.py
正在啟動 Security AI...

Security AI 已啟動。

請選擇模式：
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

## Demo Case 1: Mode 1 XSS Payload Analysis

Status: Passed

```text
請輸入模式編號: 1

請輸入 payload 或事件描述: <script>alert(1)</script>
[Mode 1] Running payload/event analysis...
[Mode 1] Payload/event analysis started...
[Mode 1] Payload/event analysis still running... elapsed 5s
[Mode 1] Payload/event analysis complete.

AI:
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
Note: Decision above is the final system decision; LLM Suggested Decision is AI assist only.
```

## Demo Case 2: Mode 2 Log Ingestion Summary

Status: Passed

```text
請輸入模式編號: 2

請輸入 log 檔案路徑: demo_logs\web_attack.log
[Mode 2] Reading and summarizing log file...
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

Send aggregated events to SecurityAgent? (y/n): n
Show detailed JSON output? (y/n): n
```

## Demo Case 3: Mode 2 Analyze First Event

Status: Passed

```text
Send aggregated events to SecurityAgent? (y/n): y
[Mode 2] Preparing SecurityAgent analysis...

Choose SecurityAgent analysis scope:
1. Analyze first event only
2. Analyze all events
0. Cancel

請選擇分析範圍: 1
[Mode 2] Running SecurityAgent analysis...
[Analyzing Log Event 1/3]
Input: q=<script>alert(1)</script>
Processing Log Event 1/3 started...
Processing Log Event 1/3 still running... elapsed 5s
Processing Log Event 1/3 complete.
[SecurityAgent Analysis for Log Event 1]
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
Detection Source: rule_based_detector (rule_based)

2. Evidence
Input / Payload:
q=<script>alert(1)</script>

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
Confidence: 0.98
Note: Decision above is the final system decision; LLM Suggested Decision is AI assist only.

[Mode 2] SecurityAgent analysis complete.
Show detailed JSON output? (y/n): n
```

## Demo Case 4: Mode 2 Analyze All Events

Status: Passed

```text
Send aggregated events to SecurityAgent? (y/n): y
[Mode 2] Preparing SecurityAgent analysis...

Choose SecurityAgent analysis scope:
1. Analyze first event only
2. Analyze all events
0. Cancel

請選擇分析範圍: 2
[Mode 2] Running SecurityAgent analysis...

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
Detection Source: rule_based_detector (rule_based)

2. Evidence
Input / Payload:
q=<script>alert(1)</script>

Matched Signatures:
- XSS: <script>, alert(

3. Why It Matters
- XSS: XSS 可能讓攻擊者把腳本注入頁面，影響使用者瀏覽器、竊取 session 或執行未授權操作。

4. Recommended Response
... repeated Recommended Response section omitted for brevity ...

5. Simulation Notice
已模擬將此事件加入監控與告警佇列，未實際部署監控規則。

[Analyzing Log Event 2/3]
Input: id=1' or '1'='1
Processing Log Event 2/3 started...
Processing Log Event 2/3 complete.
[SecurityAgent Analysis for Log Event 2]
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: SQL Injection
Risk Level: HIGH
Decision: BLOCK
Detection Source: rule_based_detector (rule_based)

2. Evidence
Input / Payload:
id=1' or '1'='1

Matched Signatures:
- SQL Injection: ' or '1'='1

3. Why It Matters
- SQL Injection: SQL Injection 可能讓攻擊者改變資料庫查詢邏輯，造成資料外洩、驗證繞過或資料破壞。

4. Recommended Response
... repeated Recommended Response section omitted for brevity ...

5. Simulation Notice
已模擬封鎖這次可疑請求，未實際修改任何系統或防火牆設定。

[Analyzing Log Event 3/3]
Input: file=../../etc/passwd
Processing Log Event 3/3 started...
Processing Log Event 3/3 complete.
[SecurityAgent Analysis for Log Event 3]
[Security Triage Report]

1. Summary
Status: ALERT
Attack Type: Path Traversal
Risk Level: HIGH
Decision: BLOCK
Detection Source: rule_based_detector (rule_based)

2. Evidence
Input / Payload:
file=../../etc/passwd

Matched Signatures:
- Path Traversal: /etc/passwd, ../

3. Why It Matters
- Path Traversal: Path Traversal 可能讓攻擊者嘗試讀取應用程式目錄外的敏感檔案，例如系統密碼檔或設定檔。

4. Recommended Response
... repeated Recommended Response section omitted for brevity ...

5. Simulation Notice
已模擬封鎖這次可疑請求，未實際修改任何系統或防火牆設定。

[Mode 2] SecurityAgent analysis complete.
Show detailed JSON output? (y/n): n
```

## Demo Case 5: Blank Input Handling

Status: Passed

```text
請輸入模式編號:
請輸入模式編號，或輸入 0 離開。

請選擇分析範圍:
未輸入分析範圍，已取消 SecurityAgent 分析。

Show detailed JSON output? (y/n):
未顯示 detailed JSON output。
```

## Demo Case 6: Mode 3 Security Knowledge Q&A

Status: Passed

```text
請輸入模式編號: 3

請輸入資安知識問題: 什麼是 XSS
[Mode 3] Running security knowledge Q&A...
[Mode 3] Security knowledge Q&A started...
[Mode 3] Security knowledge Q&A still running... elapsed 5s
[Mode 3] Security knowledge Q&A complete.

AI: XSS，即跨站腳本攻擊（Cross-Site Scripting），是指攻擊者將惡意腳本注入可被其他使用者瀏覽的內容中，藉此竊取 Session、操控頁面或冒用使用者行為。
```

## Demo Case 7: Mode 4 Follow-up / More Details

Status: Passed

```text
請輸入模式編號: 4

請輸入追問或想了解的細節: 詳細說明
[Mode 4] Running follow-up analysis...
[Mode 4] Follow-up analysis started...
[Mode 4] Follow-up analysis complete.

AI: XSS 攻擊主要分為反射型 XSS、儲存型 XSS 和基於 DOM 的 XSS。防禦重點包括輸入驗證、依輸出情境做 encoding，以及設定 Content Security Policy (CSP)。
```

## Demo Case 8: Exit

Status: Passed

```text
請輸入模式編號: 0
再見。
```
