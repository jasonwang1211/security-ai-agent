# Demo Outputs

This document shows representative CLI output for the current `v1.1.4-event-to-agent-adapter` demo flow.

The current system emits a unified `[Security Triage Report]` for triage output. Older standalone formats such as `LLM-assisted suspicious finding`, `Threat Intelligence Analysis`, `[Security Triage Result]`, `Final Risk`, and `Final Decision` are outdated and should not be used as the expected demo output.

## Current CLI Modes

```text
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

## Demo Case 1: Mode 1 XSS Payload Triage

Status: Passed

Input:

```text
<script>alert(1)</script>
```

Expected / observed output excerpt:

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

## Demo Case 2: Mode 1 Single Raw Auth Log Translation

Status: Passed

Input:

```text
2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401
```

Observed translation block:

```text
[Input Translation]
Detected Input Type: raw_log
Normalized Event Type: auth_failure
Converted SecurityAgent Input:
login failed from source_ip 10.0.0.5 against /login for user admin
```

Expected / observed triage summary:

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

## Demo Case 3: Mode 2 auth_bruteforce.log

Status: Passed

Input:

```text
demo_logs\auth_bruteforce.log
```

Observed log ingestion summary:

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

Expected / observed SecurityAgent output summary:

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

No old `LLM-assisted suspicious finding` header is expected in this mode.

## Demo Case 4: Mode 3 RAG QA

Status: Passed

Mode 3 is for security knowledge explanation. RAG QA now uses `RAGQueryPlanner` plus preferred source selection. RAG does not decide attack type, `Risk Level`, or `Decision`; those fields come from the triage pipeline.

### Question: 什麼是 brute force？

Expected / observed behavior:

- Explains brute force as repeated credential guessing.
- Frames it from a blue-team perspective.
- Mentions useful context such as source identity, source IP, endpoint, account/user, and time-sequence patterns.

Representative answer excerpt:

```text
Brute force is an attack pattern where an actor repeatedly tries credentials until one succeeds. From a blue-team view, the useful evidence is not one failed login by itself, but repeated failures across a time window, often tied to the same source_ip, target endpoint, user identity, or sequence of related authentication events.
```

### Question: 如何判斷多次登入失敗是不是攻擊？

Expected / observed behavior:

- Mentions time window.
- Mentions `source_ip`.
- Mentions target / endpoint.
- Mentions user or account.
- Mentions HTTP `401` / `403`.
- Names brute force / credential stuffing.
- Includes false-positive considerations.

Representative answer excerpt:

```text
To judge whether repeated login failures are attack-like, compare failures within a time window and group by source_ip, target endpoint, and user. Many 401 or 403 responses from the same source against /login can indicate brute force or credential stuffing, but false positives are possible, such as a user with an expired password, a broken client, or a scheduled integration using stale credentials.
```

### Question: Security Triage Report 怎麼看？

Expected / observed behavior:

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

Representative answer excerpt:

```text
Read the Security Triage Report from top to bottom. Quick Verdict gives the compact status, attack type, risk level, decision, and detection source. Summary explains what happened. Evidence shows the concrete signals. Why It Matters explains the security impact. Recommended Response separates immediate actions, mitigation, and follow-up. Simulation Notice reminds you that BLOCK, MONITOR, and ALLOW are simulated decisions. AI Assist shows model suggestions, but LLM Suggested Decision is assist-only and is not the final system decision.
```

## Retired Output Formats

The following older labels are retained here only as a migration note and should not appear as the current final demo output:

- `LLM-assisted suspicious finding`
- `Threat Intelligence Analysis` as a standalone final format
- `[Security Triage Result]`
- `Final Risk`
- `Final Decision`
