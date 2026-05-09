# Demo & Evaluation Report

> Project: AI-assisted Security Threat Detection and Response System  
> Branch: `v1.1.4-event-to-agent-adapter`  
> Current milestone: `v1.1.5-unified-triage-rag-routing`  
> Milestone name: Unified Security Triage Output and RAG QA Stabilization

Full CLI excerpts are available in [demo_outputs.md](demo_outputs.md).

---

## 1. Report Overview

The current system is an AI-assisted blue-team security triage prototype. It supports:

- Suspicious payload / event analysis
- Single raw log translation
- Log file ingestion and aggregation
- RAG-based security knowledge Q&A
- Follow-up explanation
- Unified `[Security Triage Report]` output

The latest milestone stabilizes a single triage report format across deterministic and LLM-assisted analysis paths, adds raw authentication log translation, demonstrates aggregated brute-force candidate analysis, and improves Mode 3 knowledge Q&A routing with `RAGQueryPlanner` and preferred source selection.

---

## 2. System Overview

| Capability | Current Behavior |
|---|---|
| CLI Modes | The menu routes users to payload/event analysis, log file ingestion, security knowledge Q&A, follow-up explanation, or exit. |
| Unified Triage Output | Security analysis results use `[Security Triage Report]` with Quick Verdict, Summary, Evidence, Why It Matters, Recommended Response, Simulation Notice, and AI Assist sections. |
| Payload / Event Analysis | Known suspicious payloads are detected with rule-based signatures, risk scoring, simulated decision logic, and response guidance. |
| Single Raw Log Translation | Raw authentication log lines can be parsed, normalized, translated into SecurityAgent input, and triaged as authentication failures. |
| Log File Ingestion | Log files are parsed, normalized, aggregated, and optionally sent to SecurityAgent. |
| Brute Force Candidate Analysis | Repeated authentication failures can aggregate into a `brute_force_candidate` event for SecurityAgent triage. |
| RAG Knowledge Q&A | Mode 3 uses a dedicated knowledge route, `RAGQueryPlanner`, preferred source selection, and Chroma fallback for explanatory answers. |
| Follow-up Explanation | Mode 4 remains available for additional explanation based on previous context. |

---

## 3. Architecture

### A. Payload Flow

```text
User Input
-> Mode Router / Skill Layer
-> Rule-Based Detector
-> Risk Scoring
-> Decision Engine
-> Defense Simulation
-> Security Triage Report
```

### B. Single Raw Log Flow

```text
Raw Log Line
-> Log Input Adapter
-> Log Parser
-> Event Normalizer
-> Event-to-Agent Input
-> Authentication Failure Triage Report
```

### C. Log File Flow

```text
Log File
-> Log Parser
-> Event Normalizer
-> Event Aggregator
-> Event-to-Agent Adapter
-> SecurityAgent
-> Security Triage Report
```

### D. RAG QA Flow

```text
Security Question
-> Dedicated Knowledge Q&A route
-> RAGQueryPlanner
-> Preferred source selection / Chroma fallback
-> RAG Answer
```

Mode 3 RAG is used for knowledge explanation only. It does not decide attack type, risk level, or final simulated action.

---

## 4. Demo Cases Summary

| ID | Category | Input | Expected Behavior | Result |
|---|---|---|---|---|
| D01 | Mode 1 XSS Payload | `<script>alert(1)</script>` | `ALERT / XSS / MEDIUM / MONITOR` | Passed |
| D02 | Mode 1 Single Raw Auth Log | `2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401` | Input Translation plus `REVIEW / Authentication Failure / LOW / MONITOR` | Passed |
| D03 | Mode 2 `auth_bruteforce.log` Summary | `demo_logs\auth_bruteforce.log` | 10 `auth_failure` events aggregated into 1 `brute_force_candidate` | Passed |
| D04 | Mode 2 `auth_bruteforce.log` SecurityAgent Analysis | `demo_logs\auth_bruteforce.log` | `SUSPICIOUS / Brute Force or Brute Force + Credential Stuffing / MONITOR` | Passed |
| D05 | Mode 3 Brute Force Q&A | `什麼是 brute force？` | RAG answer about brute force and blue-team interpretation | Passed |
| D06 | Mode 3 Login Failure Analysis Q&A | `如何判斷多次登入失敗是不是攻擊？` | Mentions `source_ip`, endpoint, user, time window, HTTP `401` / `403`, brute force / credential stuffing | Passed |
| D07 | Mode 3 Security Triage Report Guide | `Security Triage Report 怎麼看？` | Explains Quick Verdict, Summary, Evidence, Why It Matters, Recommended Response, Simulation Notice, AI Assist, Risk Level, Decision, and simulated decisions | Passed |
| D08 | Mode 1 XSS Regression | `<script>alert(1)</script>` | Rule-based report still works | Passed |

---

## 5. Detailed Demo Results

### D01 - Mode 1 XSS Payload

Input:

```html
<script>alert(1)</script>
```

Observed summary:

```text
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
```

Evaluation: Passed.

The rule-based path still detects XSS and emits the current unified report format.

### D02 - Mode 1 Single Raw Auth Log

Input:

```text
2026-05-01T10:00:00Z login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401
```

Observed summary:

```text
[Input Translation]
Detected Input Type: raw_log
Normalized Event Type: auth_failure
Converted SecurityAgent Input:
login failed from source_ip 10.0.0.5 against /login for user admin

[Security Triage Report]

0. Quick Verdict
Verdict: This is a failed login event. A single failure is not enough to confirm brute force.
Risk Level: LOW
Decision: MONITOR

1. Summary
Status: REVIEW
Attack Type: Authentication Failure
Risk Level: LOW
Decision: MONITOR
Detection Source: raw_log_translation
```

Evaluation: Passed.

A single failed login is treated as a reviewable authentication signal, not enough evidence by itself to confirm brute force.

### D03 - Mode 2 auth_bruteforce.log Summary

Input:

```text
demo_logs\auth_bruteforce.log
```

Observed summary:

```text
[Log Ingestion Summary]

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

Evaluation: Passed.

Mode 2 now demonstrates that repeated authentication failures can be aggregated before SecurityAgent analysis.

### D04 - Mode 2 auth_bruteforce.log SecurityAgent Analysis

Observed summary:

```text
[Security Triage Report]

0. Quick Verdict
Verdict: This event is suspicious for Brute Force or Credential Stuffing.
Risk Level: HIGH
Decision: MONITOR

1. Summary
Status: SUSPICIOUS
Attack Type: Brute Force / Credential Stuffing
Risk Level: HIGH
Decision: MONITOR
Detection Source: llm_threat_judge + signal_extraction
```

Evaluation: Passed.

Aggregated failures from the same source and target become suspicious brute-force or credential-stuffing evidence while the final decision remains a simulated `MONITOR`.

### D05 - Mode 3 Brute Force Q&A

Question:

```text
什麼是 brute force？
```

Expected result:

```text
RAG-supported explanation of repeated credential guessing from a blue-team perspective.
```

Evaluation: Passed.

### D06 - Mode 3 Login Failure Analysis Q&A

Question:

```text
如何判斷多次登入失敗是不是攻擊？
```

Expected result:

```text
Mentions time window, source_ip, endpoint, user, HTTP 401 / 403, brute force / credential stuffing, and false-positive considerations.
```

Evaluation: Passed.

### D07 - Mode 3 Security Triage Report Guide

Question:

```text
Security Triage Report 怎麼看？
```

Expected result:

```text
Explains the report sections and clarifies that BLOCK, MONITOR, and ALLOW are simulated decisions.
```

Evaluation: Passed.

### D08 - Mode 1 XSS Regression

Input:

```html
<script>alert(1)</script>
```

Expected result:

```text
Rule-based XSS report remains stable.
```

Evaluation: Passed.

---

## 6. Overall Evaluation

| Capability | Result |
|---|---|
| Unified Security Triage Report | Passed |
| Mode 1 payload triage | Passed |
| Mode 1 raw log translation | Passed |
| Single `auth_failure` triage | Passed |
| Mode 2 log ingestion and aggregation | Passed |
| Mode 2 `brute_force_candidate` SecurityAgent analysis | Passed |
| Mode 3 dedicated knowledge Q&A routing | Passed |
| `RAGQueryPlanner` and preferred source selection | Passed |

Overall result:

```text
Unified Security Triage Output and RAG QA Stabilization milestone is ready for demo documentation.
```

---

## 7. Key Findings

1. The system now separates a single `auth_failure` from an aggregated `brute_force_candidate`.
2. A single authentication failure is triaged as `REVIEW / LOW / MONITOR`.
3. Aggregated repeated failures can become suspicious Brute Force / Credential Stuffing evidence.
4. Rule-based detections and LLM-assisted suspicious findings now both use the unified `[Security Triage Report]`.
5. Mode 3 RAG QA is no longer driven by the old keyword fallback in the active routing path.
6. RAG is used for security knowledge explanation, while detection, risk, and decision fields remain part of the triage pipeline.

---

## 8. Limitations

This demo remains a functional prototype with the following limitations:

- Not all real-world log formats are supported.
- There is no real firewall, WAF, EDR, or production SIEM action.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions only.
- LLM suggestions do not override the final system `Decision`.
- RAG is not used for primary detection.
- The current CLI is still menu-based and is not yet a full Main Controller Agent.
- Startup still initializes heavy RAG, embedding, and Chroma components.
- Smart Input Router / Main Controller Agent behavior remains future work.
- `RAGQueryPlanner` improves retrieval, but answer quality still depends on the quality of knowledge files and local LLM output.

---

## 9. Suggested Next Steps

Recommended next development tasks:

1. Freeze and document the current demo.
2. Add a Smart Input Router / Main Controller Agent.
3. Add lazy initialization for heavy RAG / embedding / Chroma components.
4. Add JSON Incident Report export.
5. Support more realistic log formats.
6. Explore a Hybrid Multi-Agent architecture.
7. Add a web dashboard.
8. Build a Red / Blue simulation lab later.

---

Full CLI excerpts are available in [demo_outputs.md](demo_outputs.md).
