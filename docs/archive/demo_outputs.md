# Demo Outputs / Demo 輸出範例

> **Historical / legacy (through v2.4). 歷史檔案（至 v2.4）。** This file captures older CLI/runtime demo output excerpts (v2.3-v2.4) and is **not** the current v2.8 demo entry point; the test counts and CLI-only framing below are historical and do not reflect the current v2.8 validation summary. For the current demo and validation, see [README](../../README.md), [UI walkthrough](../UI_WALKTHROUGH.md), and [Test report](../TEST_REPORT.md). / 本檔為舊版 CLI/runtime demo 輸出摘錄（v2.3-v2.4），並非目前 v2.8 的 demo 入口；以下測試數與純 CLI 描述皆為歷史內容，不代表目前 v2.8 驗證摘要。目前 demo 與驗證請見 README、UI walkthrough 與 Test report。

This document shows representative output excerpts for the current CLI/runtime demo flows, including the v2.4 deterministic direct-input Agent Skill Orchestration implementation.

本文件整理目前 CLI/runtime demo flows 的代表性輸出摘錄，包含 v2.3 controlled retrieval and structured follow-up 實作。

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

## Demo Case 11: Protected Explanation and Analyst Suggestions

Status: Passed

This case documents the v1.8 protected helper foundation. It is covered by deterministic tests and is not a full CLI auto-route.

Input:

```text
為什麼是 MONITOR？
```

Protected explanation excerpt:

```text
path: protected report/rule explanation helper
guardrail: AnswerGuardrails applied before returning helper output
fallback: unsafe output returns conservative Traditional Chinese safety wording
verdict: Risk Level and Decision are unchanged
```

Smart Router preview excerpt:

```text
input_kind: report_followup
route: report_followup
would_execute: false
```

Suggested questions:

```text
為什麼是 MONITOR？
EV-003 是什麼意思？
下一步要查什麼？
```

Notes:

- Smart Router preview does not execute tools.
- No LLM routing is used.
- This is not CLI auto-route behavior.

## Demo Case 12: Tool Permission and Workflow Plan Contracts

Status: Passed

This case documents the v1.9 orchestration contract foundation. It is covered by deterministic contract tests and is not a CLI workflow execution feature.

Tool Permission Contract excerpt:

```text
tool_name: report_explainer
permission: READ_ONLY
execution_mode: DIRECT_ALLOWED
risk_level: LOW
requires_human_approval: false
decision: allowed as a read-only helper
```

Forbidden tool excerpt:

```text
tool_name: real_firewall_block
permission: FORBIDDEN
execution_mode: BLOCKED
risk_level: CRITICAL
decision: not allowed
reason: real firewall enforcement is forbidden
```

Workflow Plan Contract excerpt:

```text
plan_id: plan-001
route: report_followup
execution_mode: READ_ONLY
status: READY
steps:
  - tool_name: report_explainer
    permission: READ_ONLY
    execution_mode: READ_ONLY
limitations:
  - Workflow plans are schema-only previews.
  - This plan does not execute tools or change runtime state.
```

Notes:

- This is preview-contract only.
- No tool execution is performed.
- No runtime workflow execution is wired.
- Smart Router is not the default CLI auto-route.
- ControllerAgent does not auto-execute.
- `RAGQA` is not replaced.
- Graph RAG and Knowledge Capture remain deferred.
- AI does not decide attacks or override Risk Level / Decision.
- `BLOCK`, `MONITOR`, and `ALLOW` remain simulated decisions.
- No real firewall/WAF/SIEM/SOAR enforcement is performed.

## Demo Case 13: v2.3 Event-Grounded Payload Follow-Up

Status: Passed by manual runtime smoke.

This excerpt records stable fields and follow-up behavior verified from the real runtime. It is not a full verbatim transcript.

Mode 1 input:

```text
test; rm -rf /tmp/test
```

Observed stable Mode 1 output fields:

```text
Attack Type: Command Injection
Risk Level: HIGH
Decision: BLOCK
Matched Signatures: command-injection indicators including ; rm and ; rm -rf
Simulation Notice: BLOCK is a simulated training decision, not real enforcement.
```

Mode 4 follow-up evidence:

```text
User: BLOCK 是否代表真實封鎖？
Observed: The answer states that BLOCK is simulated and does not mean a real firewall, WAF, EDR, or account action was executed.

User: 這代表命令已經成功執行了嗎？
Observed: The answer states that a payload/rule match does not prove successful command execution; analysts should check server-side execution, process/audit logs, and outbound connections.

User: 我現在應該先做哪些調查與修補？
Observed: The answer gives defensive investigation/remediation guidance such as reviewing command execution sinks, validating inputs, using allowlists, and avoiding shell invocation where possible.
```

Boundaries:

- Follow-up uses the current in-memory `ActiveEventContext`.
- It does not fabricate `EV-*`, `F-*`, or `INC-*` IDs for Mode 1 payload events.
- It does not claim confirmed compromise, successful command execution, real blocking, or real enforcement.

## Demo Case 14: v2.3 Graph-Grounded Authentication Incident Follow-Up

Status: Passed by manual runtime smoke.

This excerpt records stable fields and follow-up behavior verified from the real runtime. It is not a full verbatim transcript.

Mode 2 input:

```text
demo_logs\scenario_a_mixed_auth.log
```

Observed structured incident summary fields:

```text
Incident ID: INC-20260501-001
Status: SUSPICIOUS
Attack Type: Possible Account Compromise
Risk Level: HIGH
Decision: MONITOR (simulated decision)
Evidence IDs: includes EV-003
Finding IDs: F-001
```

Mode 4 follow-up evidence:

```text
User: EV-003 是什麼意思？
Observed: The answer explains EV-003 as the successful authentication after repeated failures.

User: EV-003 和 F-001 有什麼關係？
Observed: The answer uses explicit current GraphSnapshot facts and states that F-001 is explicitly supported by EV-003.

User: 為什麼是 MONITOR？
Observed: The answer keeps MONITOR as a simulated decision for analyst review and does not claim real monitoring deployment.

User: 這代表帳號已經被入侵了嗎？
Observed: The answer states that the failure-then-success sequence is suspicious but does not confirm account compromise by itself.
```

Boundaries:

- Follow-up uses the current in-memory `ActiveAuthIncidentContext` and explicit current-incident `GraphSnapshot`.
- It is graph-grounded follow-up for the current structured authentication incident, not Similar-Case Graph RAG.
- It does not use LLM-generated graph reasoning, historical-case retrieval, Knowledge Capture, event write-back, real monitoring deployment, or Risk Level / Decision override.

## Demo Case 15: v2.4 Deterministic Agent Skill Orchestration / Direct-Input Runtime

Status: Passed by manual runtime smoke.

This excerpt records stable fields and behavior verified from the real runtime. It is not a full verbatim transcript.

Direct payload input:

```text
test; rm -rf /tmp/test
```

Observed runtime behavior:

- Without selecting Mode 1, the Agent executed payload analysis.
- Output included `Attack Type: Command Injection`, `Risk Level: HIGH`, and `Decision: BLOCK`.
- Matched signatures included `; rm` and `; rm -rf`.
- The simulation notice stated that no actual system or firewall setting was modified.

Follow-up evidence:

```text
User: follow-up asking whether the matched payload proves execution or compromise
Observed: The answer states that matching a payload, signature, or rule does not prove successful execution, data exfiltration, system compromise, or confirmed intrusion.
Observed: The answer suggests checking command execution sinks, process/audit logs, file changes, privilege changes, outbound connections, and host/container logs.

User: natural follow-up asking what to check next
Observed: The system retained the current Command Injection investigation context and provided additional relevant checks.
```

Direct authentication log input:

```text
demo_logs\scenario_a_mixed_auth.log
```

Observed runtime behavior:

- Without selecting Mode 2, the Agent executed deterministic authentication log correlation.
- Output included `[Structured Authentication Incident]`.
- Output included `Incident ID: INC-20260501-001`.
- Output included `Attack Type: Possible Account Compromise`.
- Output included `Risk Level: HIGH`.
- Output included `Decision: MONITOR` with simulated-decision wording.
- `Evidence IDs` included `EV-003`.
- `Finding IDs` included `F-001`.

Follow-up evidence:

```text
User: EV-003 follow-up
Observed: The answer used the current structured incident and explicit GraphSnapshot facts.

User: EV-003 / F-001 support follow-up
Observed: The answer used explicit current-incident graph edges and preserved the no-confirmed-compromise boundary.

User: MONITOR follow-up
Observed: The answer preserved the no-real-monitoring-deployment boundary and stated that this is graph lookup over current incident edges, not Graph RAG.
```

Knowledge question during active incident context:

```text
User: SQL Injection knowledge question
Observed: The system answered through the protected knowledge path.

User: EV-003 follow-up after the knowledge question
Observed: The system still answered from the previously retained active authentication incident context.
```

Legacy fallback:

```text
menu
```

Observed behavior: The legacy four-mode interface remained available.

Boundaries:

- Direct-input routing is deterministic and not LLM-selected.
- The skill layer reuses existing v2.3 runtime capabilities rather than replacing detector, graph facts, or protected RAG logic.
- It does not implement Similar-Case Graph RAG, Knowledge Capture, event write-back, real enforcement, real monitoring deployment, or Risk Level / Decision override.
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
