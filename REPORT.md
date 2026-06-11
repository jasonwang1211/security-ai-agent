# Sentinel Project Report

## Abstract

Sentinel Project is an AI-assisted blue-team security triage prototype. It uses deterministic rule-based detection and deterministic Risk Level / Decision logic as the security authority, then presents AI/RAG features as analyst advisory context through a Streamlit SOC analyst console.

The project demonstrates a safe pattern for adding AI to security workflows: AI can summarize, explain, compare, and document, but it does not make the final detection decision, does not change risk, and does not perform real enforcement.

## Problem Statement

Security analysts often need to quickly classify suspicious inputs, assess risk, identify missing evidence, and document the case. AI and RAG can help with explanation and knowledge retrieval, but they become risky if they are allowed to determine whether an attack is real, change severity, or trigger response actions.

The project addresses that tension by separating:

- deterministic detection and policy authority;
- advisory AI/RAG explanation and investigation support;
- human-reviewed reporting and operational judgment.

## Design Goals

1. Make the demo understandable to professors, reviewers, and first-time GitHub visitors.
2. Keep attack detection rule-based and reproducible.
3. Keep Risk Level and Decision deterministic.
4. Show a realistic SOC analyst console rather than a backend-only proof of concept.
5. Use AI/RAG only as advisory context.
6. Preserve safe demo boundaries: no exploit, no traffic generation, and no real enforcement.

## System Architecture

```text
User input / demo scenario
  -> Streamlit analyst console or CLI
  -> Rule-Based Detector
  -> Attack classification
  -> Deterministic Risk Level
  -> Simulated Decision
  -> Advisory layers
     -> AI Analyst Brief
     -> Evidence Gap Analyzer
     -> Knowledge Q&A / RAG
     -> Approved Similar Cases
     -> Relationship Graph
  -> Human-reviewed Case Draft / Markdown Export
```

The authority path is intentionally small and deterministic. Advisory layers can explain the result, surface missing evidence, retrieve defensive knowledge, and compare cases, but they cannot override the current event's Risk Level or Decision.

## Streamlit Analyst Console

The main demo UI is the Streamlit analyst console:

```text
ui/streamlit_app.py
```

Launch command:

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

### Panels and Tabs

| Area | Purpose |
|---|---|
| Input / scenario loader | Select language, analysis mode, and safe demo scenario. |
| Deterministic result | Show attack type, Risk Level, simulated Decision, rule ID, and active context. |
| AI Analyst Brief | Summarize what happened, why it matters, the deterministic verdict, and next steps. |
| Evidence Gap Analyzer | Separate confirmed facts from missing evidence and unsafe assumptions. |
| Knowledge Q&A / RAG | Answer defensive knowledge questions with advisory framing. |
| Approved Similar Cases | Compare the current event with approved seed cases. |
| Relationship Graph | Display event, rule, risk, decision, and case context. |
| Case Draft / Markdown Export | Prepare reviewable report material for a human analyst. |

### Demo Workflow

1. Start the Streamlit console.
2. Select Fast deterministic mode.
3. Load Command Injection or HTTP/2 Resource Exhaustion safe demo.
4. Click Run input.
5. Review attack type, Risk Level, and simulated Decision.
6. Review AI Analyst Brief and Evidence Gap Analyzer.
7. Review Knowledge Q&A / RAG, Similar Cases, Relationship Graph, Case Draft, and Markdown Export.

### Screenshot Evidence

- [Console home](docs/screenshots/01_console_home.png): scenario launcher and main UI surface.
- [AI Analyst Brief](docs/screenshots/03_ai_analyst_brief.png): advisory summary and deterministic boundary.
- [Evidence Gap Analyzer](docs/screenshots/04_evidence_gap_analyzer.png): missing evidence and unsafe assumptions.
- [HTTP/2 safe demo](docs/screenshots/09_http2_resource_exhaustion_demo.png): safe synthetic Resource Exhaustion scenario.

## Core Modules

| Module area | Responsibility | Safety note |
|---|---|---|
| Rule-Based Detector | Classifies supported payload and incident patterns. | Detection authority. |
| Risk / Decision policy | Computes deterministic Risk Level and simulated Decision. | Final demo verdict path. |
| Controller / orchestration | Routes explicit commands and deterministic skill flows. | Does not use LLM routing for authority. |
| AI advisory | Builds AI Analyst Brief and Evidence Gap summaries. | Advisory only. |
| RAG / Knowledge Q&A | Retrieves approved defensive knowledge context. | Advisory only, no exploit content. |
| Approved Similar Cases | Loads curated seed cases for comparison. | Historical cases do not prove current compromise. |
| Relationship Graph | Displays read-only investigation context. | Not graph-based detection. |
| Case Draft / Export | Creates reviewable report material. | Human review required. |

## Demo Scenarios

| Scenario | Input type | Expected classification | Risk Level | Simulated Decision | Demonstrates |
|---|---|---|---|---|---|
| Command Injection demo | Payload text | Command Injection | HIGH | BLOCK | Rule-based payload detection, deterministic policy, advisory AI panels. |
| Authentication incident demo | Authentication log path or synthetic log | Possible Account Compromise | HIGH | MONITOR | Suspicious sequence review without claiming confirmed compromise. |
| HTTP/2 Resource Exhaustion safe synthetic demo | Synthetic incident summary | HTTP/2 Resource Exhaustion Suspicion | MEDIUM | MONITOR | Safe resource-exhaustion triage without traffic generation. |
| Optional Full AI-assisted mode | User-selected mode | Depends on input | Deterministic policy remains authoritative | Simulated only | Optional AI/RAG explanation while preserving boundaries. |

## Safety Boundary

All public documentation and UI behavior must preserve this boundary:

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit / PoC / traffic generation is provided.
- Human review is required.

## Testing and Validation

Current validation summary:

- pytest: `1168 passed`
- ruff: passed
- mypy: passed
- gitleaks: passed with `.gitleaksignore` false-positive handling
- screenshot refresh: completed

Validation focuses on deterministic behavior, safety boundaries, UI helper behavior, RAG control, language-aware output, and documentation link integrity. It does not claim production IDS/IPS effectiveness.

## What the Screenshots Prove

| Screenshot | Evidence |
|---|---|
| [01_console_home.png](docs/screenshots/01_console_home.png) | The Streamlit console is the main demo UI, with four scenario cards and visible safety framing. |
| [03_ai_analyst_brief.png](docs/screenshots/03_ai_analyst_brief.png) | AI Analyst Brief appears as advisory context and keeps deterministic boundaries visible. |
| [04_evidence_gap_analyzer.png](docs/screenshots/04_evidence_gap_analyzer.png) | Evidence Gap separates confirmed facts from missing evidence and unsafe assumptions. |
| [05_knowledge_qa_rag.png](docs/screenshots/05_knowledge_qa_rag.png) | Knowledge Q&A / RAG is presented as defensive advisory context. |
| [09_http2_resource_exhaustion_demo.png](docs/screenshots/09_http2_resource_exhaustion_demo.png) | HTTP/2 Resource Exhaustion is represented as a safe synthetic incident summary, not traffic generation. |

## Limitations

- The project is not a production IDS/IPS.
- It is not an autonomous response or enforcement system.
- It does not replace SIEM, SOAR, EDR, endpoint telemetry, vulnerability management, or incident response approval.
- RAG answer quality depends on approved knowledge content.
- Similar Cases are a curated demo corpus, not a production case database.
- AI does not have final decision authority.

## Future Work

- Add additional defensive synthetic scenarios.
- Improve analyst timeline and event replay workflows.
- Expand read-only graph and approved-case memory context.
- Improve report export formatting for presentations and reviews.
- Continue documentation polish and link hygiene.

## Conclusion

Sentinel Project demonstrates a practical and safety-conscious way to add AI/RAG support to SOC triage. Deterministic detection and policy remain the authority path, while advisory layers improve explanation, investigation, comparison, and reporting.

The result is a demo-ready security project that can be inspected from GitHub, operated through Streamlit, and reviewed without confusing AI advisory output for final security authority.
