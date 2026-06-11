# User Operation Guide

## Purpose

This guide explains how to run the Sentinel Project Streamlit analyst console and how to interpret each major panel. The console is the primary demo UI for reviewers, professors, and first-time users.

## UI Entry Point

```text
ui/streamlit_app.py
```

Launch command:

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

The UI is a local demo console. It does not perform real firewall, WAF, EDR, account, cloud, SIEM, or SOAR actions.

## Recommended Professor Demo Flow

1. Start the Streamlit console.
2. Select Fast deterministic mode.
3. Load the Command Injection demo.
4. Click Run input.
5. Point out attack type, Risk Level, simulated Decision, and rule ID.
6. Open AI Analyst Brief and explain that it is advisory context only.
7. Open Evidence Gap Analyzer and show confirmed facts vs missing evidence.
8. Use Knowledge Q&A / RAG for a defensive question such as HTTP/2 DoS or CVE context.
9. Review Approved Similar Cases and Relationship Graph.
10. Review Case Draft and Markdown Export.
11. Load the HTTP/2 Resource Exhaustion safe demo and point out that no traffic is generated.

## Major Panels and Tabs

### Input and Scenario Loader

The input panel controls language, analysis mode, and demo scenarios. Scenario cards are safe presets for review. Loading a scenario only fills the input area or context; it does not execute real traffic or enforcement.

### Deterministic Result

After Run input, the console displays the active context, attack classification, Risk Level, simulated Decision, and rule or evidence summary. This is the authority path.

### AI Analyst Brief

AI Analyst Brief summarizes what happened, why it matters, the deterministic verdict, advisory summary, evidence gap summary, recommended next steps, and unsafe assumptions. It is advisory only and does not override Risk Level or Decision.

### Evidence Gap Analyzer

Evidence Gap Analyzer separates confirmed facts from missing evidence. It helps reviewers avoid unsafe conclusions such as assuming command execution, account compromise, or successful exploitation from a single rule match.

### Knowledge Q&A / RAG

Knowledge Q&A / RAG answers defensive security questions from approved knowledge context. It is useful for HTTP/2 Resource Exhaustion, CVE vs CVSS terminology, mitigation concepts, and analyst triage framing. It does not provide exploit steps, PoC instructions, or traffic generation guidance.

### Approved Similar Cases

Approved Similar Cases retrieves curated seed cases for comparison. Similarity reasons and differences are deterministic. Historical cases are advisory references only and do not prove the current event.

### Relationship Graph

Relationship Graph presents event, rule, risk, decision, and approved-case context. It is a visual investigation aid, not graph-based detection authority.

### Case Draft / Export

Case Draft and Markdown Export prepare report material for human review. Drafts and exports are not operational actions and are not automatically promoted to live knowledge.

## Common Demo Checks

| Check | Expected result |
|---|---|
| Command Injection demo | Command Injection, HIGH, simulated BLOCK. |
| Authentication incident demo | Possible Account Compromise, HIGH, simulated MONITOR, with no claim of proven compromise. |
| HTTP/2 Resource Exhaustion safe demo | HTTP/2 Resource Exhaustion Suspicion, MEDIUM, simulated MONITOR, with no traffic generation. |
| AI Analyst Brief | Advisory wording and no final AI verdict. |
| Evidence Gap Analyzer | Missing evidence and unsafe assumptions remain visible. |
| Similar Cases / Graph | Context appears only after relevant current context exists. |

## Troubleshooting

- If Streamlit does not start, confirm that the virtual environment is active and Streamlit is installed.
- If Knowledge Q&A / RAG is unavailable, confirm that local RAG dependencies and indexes are available in your environment.
- If screenshot paths do not render on GitHub, confirm that files still exist under `docs/screenshots/`.
- If a result looks stale, clear context and run the scenario again.
- If local LLM support is unavailable, use Fast deterministic mode for the core demo.

## Safety Reminder

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit / PoC / traffic generation is provided.
- Human review is required.

## Related Documentation

- [UI walkthrough](UI_WALKTHROUGH.md)
- [Screenshot gallery](screenshots/README.md)
- [Test report](TEST_REPORT.md)
- [v2.8 release gate](v2.8_release_gate.md)
