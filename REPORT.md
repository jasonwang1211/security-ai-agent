# Sentinel Project Report

## Abstract

Sentinel Project is an AI-assisted blue-team security triage prototype. It demonstrates a safe architecture for adding AI and retrieval-assisted context to a SOC-style workflow while preserving deterministic detection authority.

The system uses a Rule-Based Detector and deterministic policy logic to classify supported security inputs, assign Risk Level, and produce simulated BLOCK / MONITOR / ALLOW decisions. AI/RAG features such as AI Analyst Brief, Evidence Gap Analyzer, Knowledge Q&A, Similar Cases, and Relationship Graph provide analyst context only. They do not override the current event's Risk Level or Decision.

## Problem Statement

Security triage requires speed, consistency, and clear evidence. AI tools can help summarize findings and surface context, but they become unsafe if they are treated as final detection authority or allowed to trigger real operational action.

The project addresses this problem by separating deterministic security authority from AI advisory support. It shows how an analyst-facing UI can make this boundary visible during a demo.

## Motivation

Many AI security demos blur the line between explanation and authority. A model may produce fluent text that sounds confident even when evidence is incomplete. In security operations, this can lead to false confidence, premature escalation, or unsafe remediation claims.

Sentinel Project intentionally keeps the final triage path small, reproducible, and auditable. AI is used where it is strongest for a demo: summarization, explanation, evidence-gap framing, defensive knowledge retrieval, and report assistance.

## Requirements / Scope

The project demonstrates:

- deterministic classification for supported payload and incident scenarios;
- deterministic Risk Level and Decision logic;
- simulated response decisions only;
- advisory AI/RAG context for analysts;
- safe synthetic demo scenarios;
- documentation and screenshots suitable for public GitHub review.

Out of scope:

- production IDS/IPS enforcement;
- real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action;
- exploit code, PoC generation, traffic generation, or offensive automation;
- AI-controlled final verdicts.

## Design Principles

1. Keep security authority deterministic and reviewable.
2. Make AI value visible without granting AI unsafe authority.
3. Keep demo scenarios defensive and synthetic.
4. Separate active event facts from historical or advisory context.
5. Require human review before any operational use outside the demo.

## Why Rule-Based Detection Remains Authoritative

The Rule-Based Detector provides reproducible behavior for the supported demo scenarios. Its outputs can be tested, reviewed, and explained through rule IDs and matched evidence. This makes the authority path suitable for a controlled educational demo.

LLM output is intentionally excluded from final attack classification because generative models can hallucinate, overgeneralize, or infer facts that are not present in the input.

## Why AI Is Advisory Only

AI/RAG components help the analyst understand and investigate the deterministic result. They may explain what happened, identify missing evidence, propose review steps, answer defensive questions, or compare approved cases. They must not change the current Risk Level, Decision, live detection facts, graph facts, knowledge corpus, or operational state.

This advisory-only design preserves the safety boundary while still demonstrating practical AI-assisted workflow value.

## Why BLOCK / MONITOR / ALLOW Are Simulated

BLOCK / MONITOR / ALLOW labels communicate a possible triage decision inside the project. They are simulated decisions only. The project does not perform real blocking, monitoring deployment, account action, cloud policy change, SIEM action, SOAR playbook execution, or remediation.

The labels are useful for showing how a blue-team triage workflow can be structured, but they are not proof of real enforcement.

## System Architecture

~~~text
User input / demo scenario
  -> Streamlit analyst console or CLI
  -> Rule-Based Detector
  -> Attack / incident classification
  -> Deterministic Risk Level
  -> Simulated Decision
  -> Advisory context
     -> AI Analyst Brief
     -> Evidence Gap Analyzer
     -> Knowledge Q&A / RAG
     -> Approved Similar Cases
     -> Relationship Graph
  -> Human-reviewed Case Draft / Markdown Export
~~~

The authority path ends at deterministic classification, Risk Level, and simulated Decision. Advisory layers can explain, compare, and document, but they cannot override the authority path.

## Module Design

| Module area | Responsibility | Safety boundary |
|---|---|---|
| Rule-Based Detector | Classifies supported payload and incident patterns. | Detection authority. |
| Risk / Decision policy | Computes deterministic Risk Level and simulated Decision. | Final demo verdict path. |
| Controller / orchestration | Routes explicit commands and deterministic skill flows. | Does not use LLM routing as authority. |
| AI advisory | Builds AI Analyst Brief and Evidence Gap summaries. | Advisory only; no LLM authority. |
| RAG / Knowledge Q&A | Retrieves approved defensive knowledge context. | Advisory only; no exploit guidance. |
| Approved Similar Cases | Loads curated approved seed cases for comparison. | Historical cases do not prove current compromise. |
| Relationship Graph | Displays read-only relationship context. | Explanatory only; not graph-based detection. |
| Case Draft / Export | Produces reviewable report material. | Human review required. |

## Streamlit Analyst Console

The Streamlit console is the primary demo surface. It provides scenario loading, mode selection, active context display, deterministic output, AI advisory panels, case intelligence, graph context, and report export.

For launch and troubleshooting details, use [docs/USER_OPERATION_GUIDE.md](docs/USER_OPERATION_GUIDE.md). For a step-by-step demo path, use [docs/UI_WALKTHROUGH.md](docs/UI_WALKTHROUGH.md).

## Demonstration Scenarios

| Scenario | Input type | Expected classification | Risk Level | Simulated Decision | Demonstrates |
|---|---|---|---|---|---|
| Command Injection demo | Payload text | Command Injection | HIGH | BLOCK | Deterministic payload detection, rule evidence, AI advisory panels, evidence gaps. |
| Authentication incident demo | Authentication log path or synthetic log | Possible Account Compromise | HIGH | MONITOR | Suspicious login sequence review without claiming confirmed compromise. |
| HTTP/2 Resource Exhaustion safe synthetic demo | Synthetic incident summary | HTTP/2 Resource Exhaustion Suspicion | MEDIUM | MONITOR | Defensive DoS/resource-exhaustion triage without traffic generation. |
| Optional Full AI-assisted mode | User-selected mode | Depends on input | Deterministic policy remains authoritative | Simulated only | Optional AI/RAG explanation while preserving boundaries. |

## Testing and Validation

Last recorded v2.8 release-gate validation summary:

- pytest: 1168 passed
- ruff: passed
- mypy: passed
- gitleaks: passed with .gitleaksignore false-positive handling
- screenshot language refresh: completed

Validation covers deterministic behavior, safety-boundary regressions, UI helper behavior, RAG control, language-aware output, documentation links, and release-gate checks. It does not claim production IDS/IPS effectiveness.

Supporting materials:

- [Test report](docs/TEST_REPORT.md)
- [v2.8 release gate](docs/v2.8_release_gate.md)
- [Screenshot gallery](docs/screenshots/README.md)

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated decisions only.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph provide advisory context only.
- Historical approved cases do not prove current compromise or successful execution.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit code, PoC generation, traffic generation, or offensive automation is provided.
- Human review is required.

## Limitations and Non-Goals

Sentinel Project is not a production IDS/IPS, not a real blocking engine, not an exploit generator, not a red-team tool, and not an autonomous incident-response system. It does not replace SIEM, SOAR, EDR, vulnerability management, or incident response approval.

The demo supports a bounded set of scenarios. Its purpose is to demonstrate architecture, workflow, and safety boundaries, not broad threat coverage.

## Future Work

Future work should preserve the deterministic authority boundary while improving analyst usefulness:

- additional defensive synthetic scenarios;
- richer analyst timeline and event replay;
- read-only graph and approved-case memory improvements;
- report export polish;
- packaging and release polish for public review.

## Conclusion

Sentinel Project demonstrates a practical pattern for AI-assisted security triage: deterministic detection and policy remain authoritative, while AI/RAG components provide advisory context for human analysts. This design makes AI useful in the workflow without making it the final judge or an autonomous enforcement mechanism.
