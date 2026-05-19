# Demo Outputs / Demo 輸出範例

This document shows representative output excerpts for the `v1.7-answer-safety-eval-router` branch, based on tag `v1.6.0` on `main`.

本文件整理 v1.7 開發分支在 `v1.6.0` release baseline 之後的代表性輸出摘錄。

The current system emits a unified `[Security Triage Report]` for triage output. Older standalone formats are outdated and should not be used as the expected demo output.

目前系統的分流輸出使用統一 `[Security Triage Report]`。舊版獨立輸出格式已退役，不應作為目前 demo 的預期輸出。

## Current CLI Modes / 目前 CLI 模式

```text
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

## Demo Case 1: Mode 1 XSS Payload Triage / 範例 1：Mode 1 XSS Payload 分流

Status / 狀態: Passed

Input / 輸入:

```text
<script>alert(1)</script>
```

Expected / observed output excerpt / 預期與實際輸出摘錄:

```text
[Mode 1] Running payload/event analysis...

AI:
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

The input contains a script tag and JavaScript alert pattern consistent with an XSS payload.

2. Evidence
Input / Payload:
<script>alert(1)</script>

Matched Signatures:
- XSS: <script>, alert(

3. Why It Matters
XSS can allow attacker-controlled script execution in a user's browser, potentially affecting session data, page integrity, or user actions.

4. Recommended Response
Immediate Actions:
- Treat the payload as suspicious and monitor the related request path, source, and user/session context.

Mitigation:
- Apply output encoding for HTML, JavaScript, and attribute contexts.
- Validate and sanitize untrusted input.
- Review Content Security Policy coverage.

Follow-up:
- Check whether the payload was reflected, stored, or executed.
- Review nearby events from the same source or session.

5. Simulation Notice
This is a simulated training decision, not an enforcement action.

6. AI Assist
LLM Suggested Attack Type: XSS
LLM Suggested Decision: BLOCK
Note: Decision above is the final system decision; LLM Suggested Decision is AI assist only.
```

## Demo Case 2: Mode 1 Command Injection Payload Triage / 範例 2：Mode 1 Command Injection Payload 分流

Status / 狀態: Passed

Input / 輸入:

```text
test; rm -rf /tmp/test
```

Expected / observed output excerpt / 預期與實際輸出摘錄:

```text
[Security Triage Report]

0. Quick Verdict
Verdict: This event is likely Command Injection.
Risk Level: HIGH
Decision: BLOCK
Reason: Matched Command Injection indicators: ; rm , ; rm -rf

1. Summary
Status: ALERT
Attack Type: Command Injection
Risk Level: HIGH
Decision: BLOCK
Detection Source: rule_based_detector (rule_based)
```

This is a representative excerpt. Detailed LLMAssist wording is intentionally omitted because the stable regression contract is rule-based detection, `HIGH` risk, and `BLOCK` decision.

此段為代表性摘錄。LLMAssist 詳細文字刻意省略，穩定回歸契約是規則式偵測、`HIGH` 風險與 `BLOCK` 決策。

## Demo Case 3: Mode 1 Single Raw Auth Log Translation / 範例 3：Mode 1 單筆原始登入失敗日誌轉譯

Status / 狀態: Passed

Input / 輸入:

```text
2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401
```

Observed translation block / 實際轉譯區塊:

```text
[Input Translation]
Detected Input Type: raw_log
Normalized Event Type: auth_failure
Converted SecurityAgent Input:
login failed from source_ip 10.0.0.5 against /login for user admin
```

Expected / observed triage summary / 預期與實際分流摘要:

```text
[Security Triage Report]

0. Quick Verdict
Verdict: This is a failed login event. A single failure is not enough to confirm brute force.
Risk Level: LOW
Decision: MONITOR
Reason: Single auth_failure event should be reviewed, but repeated-failure evidence is required before labeling it Brute Force or Credential Stuffing.

1. Summary
Status: REVIEW
Attack Type: Authentication Failure
Risk Level: LOW
Decision: MONITOR
Detection Source: raw_log_translation

A single failed login was observed for user admin from source IP 10.0.0.5 against /login.

2. Evidence
- Event Type: auth_failure
- Source IP: 10.0.0.5
- User: admin
- Target: /login
- Status: 401

3. Why It Matters
Authentication failures are useful security signals, but one failed login is not enough to confirm Brute Force.

4. Recommended Response
Immediate Actions:
- Monitor for repeated failures from the same source IP, user, or endpoint.

Mitigation:
- Ensure rate limiting, lockout policy, and alert thresholds are configured.

Follow-up:
- Correlate with nearby login successes, repeated 401 / 403 responses, and other users targeted by the same source.
```

## Demo Case 4: Mode 2 auth_bruteforce.log / 範例 4：Mode 2 brute force 日誌聚合

Status / 狀態: Passed

Input / 輸入:

```text
demo_logs\auth_bruteforce.log
```

Observed log ingestion summary / 實際日誌匯入摘要:

```text
[Log Ingestion Summary]

File: demo_logs\auth_bruteforce.log
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

Expected / observed SecurityAgent output summary / 預期與實際 SecurityAgent 輸出摘要:

```text
[SecurityAgent Analysis for Aggregated Event 1]
[Security Triage Report]

0. Quick Verdict
Verdict: This event is suspicious for Brute Force / Credential Stuffing.
Risk Level: HIGH
Decision: MONITOR
Reason: Multiple failed login events were aggregated from the same source against the same target.

1. Summary
Status: SUSPICIOUS
Attack Type: Brute Force / Credential Stuffing
Risk Level: HIGH
Decision: MONITOR
Detection Source: llm_assist + signal_extraction

Multiple authentication failures were aggregated from source IP 192.168.1.10 against /login.

2. Evidence
- Event Type: brute_force_candidate
- Source IP: 192.168.1.10
- Target: /login
- Failed Count: 10
- Normalized auth_failure events: 10

3. Why It Matters
Repeated failed logins from the same source against the same endpoint are consistent with brute force or credential stuffing behavior.

4. Recommended Response
Immediate Actions:
- Monitor the source IP and target endpoint.
- Review whether any successful login occurred after the failure sequence.

Mitigation:
- Apply rate limiting, temporary lockout, MFA, and suspicious source monitoring.

Follow-up:
- Check time window, usernames attempted, user-agent patterns, and related 401 / 403 responses.
```

This mode should not show any retired standalone output header.

此模式不應出現任何已退役的獨立輸出標題。

## Demo Case 5: Mode 3 RAG QA / 範例 5：Mode 3 RAG 資安知識問答

Status / 狀態: Passed

Mode 3 is for security knowledge explanation. RAG QA now uses `RAGQueryPlanner` plus preferred source selection. RAG does not decide attack type, `Risk Level`, or `Decision`; those fields come from the triage pipeline.

Mode 3 用於資安知識解釋。RAG QA 目前使用 `RAGQueryPlanner` 與 preferred source selection。RAG 不決定 attack type、`Risk Level` 或 `Decision`；這些欄位由 triage pipeline 產生。

### Question / 問題：brute force 是什麼？

Expected / observed behavior / 預期與實際行為:

- Explains brute force as repeated credential guessing.
- Frames it from a blue-team perspective.
- Mentions useful context such as source identity, source IP, endpoint, account/user, and time-sequence patterns.

Representative answer excerpt / 代表性回答摘錄:

```text
Brute force is an attack pattern where an actor repeatedly tries credentials until one succeeds. From a blue-team view, the useful evidence is not one failed login by itself, but repeated failures across a time window, often tied to the same source_ip, target endpoint, user identity, or sequence of related authentication events.
```

### Question / 問題：如何分析重複登入失敗？

Expected / observed behavior / 預期與實際行為:

- Mentions time window.
- Mentions `source_ip`.
- Mentions target / endpoint.
- Mentions user or account.
- Mentions HTTP `401` / `403`.
- Names brute force / credential stuffing.
- Includes false-positive considerations.

Representative answer excerpt / 代表性回答摘錄:

```text
To judge whether repeated login failures are attack-like, compare failures within a time window and group by source_ip, target endpoint, and user. Many 401 or 403 responses from the same source against /login can indicate brute force or credential stuffing, but false positives are possible, such as a user with an expired password, a broken client, or a scheduled integration using stale credentials.
```

### Question / 問題：如何閱讀 Security Triage Report？

Expected / observed behavior / 預期與實際行為:

- Explains `Quick Verdict`.
- Explains `Summary`.
- Explains `Evidence`.
- Explains `Why It Matters`.
- Explains `Recommended Response`.
- Explains `Simulation Notice`.
- Explains `AI Assist`.
- Explains `Risk Level`.
- Explains `Decision`.
- Clarifies that `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions.
- Clarifies that `LLM Suggested Decision` is assist-only.

Representative answer excerpt / 代表性回答摘錄:

```text
Read the Security Triage Report from top to bottom. Quick Verdict gives the compact status, attack type, risk level, decision, and detection source. Summary explains what happened. Evidence shows the concrete signals. Why It Matters explains the security impact. Recommended Response separates immediate actions, mitigation, and follow-up. Simulation Notice reminds you that BLOCK, MONITOR, and ALLOW are simulated decisions. AI Assist shows model suggestions, but LLM Suggested Decision is assist-only and is not the final system decision.
```

## Demo Case 6: Scenario A — Possible Account Compromise / 情境 A：疑似帳號入侵

Status / 狀態: Passed

Input / 輸入:

- `demo_logs/scenario_a_mixed_auth.log`
- benign + attack mixed authentication log

Pipeline / 流程:

```text
parse → normalize → time-window correlation → sequence detection
→ EvidenceBundle → TriagePolicy → LLMAssist advisory assessment
→ LLMGuardrails → Security Triage Report + JSON Incident Report
```

Output excerpt / 輸出摘要:

```text
Incident Type: Possible Account Compromise
Finding: possible_account_compromise
Risk Level: HIGH
Decision: MONITOR
Evidence:
EV-001 failed_count
EV-002 time_window
EV-003 success_after_failures
```

Follow-up demo / 追問示範:

```text
User: EV-003 是什麼意思？
System: explains that EV-003 is the successful authentication after repeated failures.
User: 為什麼是 MONITOR？
System: explains that the event is suspicious but not confirmed compromise; analyst review is required.
```

Status / 驗證:

- Covered by `tests/test_scenario_a_integration.py`
- Current verification: `141 passed`

Boundary note / 邊界說明:

`MONITOR` is used because the sequence is suspicious but not confirmed compromise. LLMAssist remains advisory and cannot override the deterministic final decision. No real enforcement action is performed.

## Demo Case 7: YAML Detection-as-Code / YAML 規則式偵測

Status / 狀態: Passed

Input payload / 輸入 payload:

```text
; rm -rf /tmp/test
```

Detection result / 偵測結果:

```text
Status: ALERT
Attack Type: Command Injection
Matched Rule: CMD-001
Rule Source: detections/blue_team/command_injection/command_injection_basic.yml
Severity: HIGH
Confidence: 0.9
MITRE Techniques: T1059
Decision: BLOCK
```

Notes / 說明:

- XSS, SQL Injection, Path Traversal, and Command Injection rules are loaded from YAML.
- If YAML loading fails, hard-coded fallback keeps detector behavior stable.
- This is deterministic detection, not LLM detection.

## Demo Case 8: ControllerAgent Deterministic Dispatch / ControllerAgent deterministic dispatch

Status / 狀態: Passed

This case documents the v1.5 ControllerAgent infrastructure. It is currently tested through deterministic unit and integration tests, not wired into the CLI menu yet.

Representative dispatch excerpt:

```text
route: payload_triage
selected_tool: payload_triage
output_status: ok
response_text: payload triage done
```

Mode hint excerpt:

```text
route: mode_1
selected_tool: payload_triage
output_status: ok
```

Notes:

- Dispatch is deterministic by explicit route or tool name.
- `mode_1` maps to `payload_triage` through the default route map.
- No Auto Route mode is present.
- No Smart Router is used by this v1.5 dispatch path.
- No LLM-driven tool routing is used.
- Final verdicts remain deterministic and policy-controlled.

## Demo Case 9: RAG v2 Source-Cited Explanation Helper

Status: Passed

This case documents the v1.6 RAG v2 helper infrastructure. It is covered by deterministic tests and is not connected to the CLI menu yet.

Question:

```text
為什麼是 MONITOR？
```

RAG v2 helper excerpt:

```text
intent: report_question
selected source: knowledge/blue_team/report_explainer/...
answer type: AnswerWithSources
evidence/rule IDs: preserved when present
limitation: helper-only, not CLI-wired yet
```

Notes:

- The helper path uses metadata-aware planning, `SourceCitation`, and `AnswerWithSources`.
- It does not call Chroma, Ollama, embeddings, Torch, or LLM generation.
- It is explanation-only and does not override deterministic Risk Level, Decision, or simulated policy output.

## Demo Case 10: Smart Router and Answer Safety Foundation

Status: Passed

This case documents the v1.7 reliability foundation. It is covered by deterministic tests and is not connected to the CLI menu yet.

Input:

```text
為什麼是 MONITOR？
```

Smart Router excerpt:

```text
input_kind: report_followup
route: report_followup
confidence: HIGH
note: route decision only; no tool execution
```

AnswerGuardrails excerpt:

```text
checks: unsafe enforcement claims, RAG-as-detection claims, LLM final verdict override claims
classifier: deterministic rules only, no LLM safety classifier
enforcement: no real firewall, WAF, SIEM, or SOAR action
```

Notes:

- Smart Router is rule-based and not CLI-wired yet.
- The route decision does not change Risk Level or Decision.
- Final verdicts remain deterministic and policy-controlled.

## Appendix: Deprecated Output Formats

Historical reference only. These formats are no longer emitted by the current system and are kept to document output schema evolution.

僅作為歷史參考。目前系統已不再輸出這些格式，保留此段是為了記錄輸出格式的演進。

The following older labels are retained here only as a migration note and should not appear as the current final demo output:

以下舊版標籤僅作為遷移註記保留，不應出現在目前最終 demo 輸出中：

- `LLM-assisted suspicious finding`
- `Threat Intelligence Analysis` as a standalone final format
- `[Security Triage Result]`
- `Final Risk`
- `Final Decision`
