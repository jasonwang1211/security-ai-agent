# User Operation Guide

This guide explains how to start Sentinel Project, run the main demo flow, read the output, and understand the safety boundaries.

## 1. Project Overview

Sentinel Project is a defensive SOC triage prototype. It combines Rule-Based Detector output, deterministic Risk Level / Decision logic, AI Analyst Brief, Evidence Gap Analyzer, Knowledge Q&A / RAG, Approved Similar Cases, Relationship Graph, Case Draft, and Markdown Export.

## 2. What The System Does

The system can:

- Analyze suspicious payloads or demo incident inputs.
- Display attack classification, Risk Level, and Decision.
- Provide AI Analyst Brief and Evidence Gap Analyzer output.
- Answer defensive Knowledge Q&A / RAG questions.
- Show Approved Similar Cases and Relationship Graph context.
- Generate human-reviewed Case Draft and Markdown Export content.

## 3. What The System Does Not Do

The system does not:

- Attack real systems.
- Generate exploit or proof-of-concept steps.
- Generate attack traffic.
- Modify firewall, WAF, EDR, account, cloud, SIEM, or SOAR state.
- Allow RAG, LLM output, historical cases, or graph context to override the deterministic verdict.

## 4. Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated.
- RAG, LLM, AI Analyst Brief, and Evidence Gap provide advisory context only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, proof-of-concept, or traffic generation is provided.
- Human review is required.

## 5. Requirements

Recommended environment:

- PowerShell or an equivalent shell.
- Python and a project virtual environment.
- Streamlit.
- pytest, ruff, and mypy for validation.
- A local knowledge index if Knowledge Q&A / RAG is needed.

## 6. Quick Start

```powershell
git clone <your-repo-url>
cd sentinel_project
.\venv\Scripts\Activate.ps1
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

CLI mode:

```powershell
python app.py
```

## 7. Recommended Demo Flow

1. Start the Streamlit console.
2. Select Fast deterministic mode.
3. Load the Command Injection demo.
4. Click Run input.
5. Confirm the deterministic result, such as `Command Injection`, `HIGH`, and simulated `BLOCK`.
6. Review AI Analyst Brief and Evidence Gap Analyzer.
7. Review Knowledge Q&A / RAG.
8. Review Approved Similar Cases and Relationship Graph.
9. Review Case Draft and Markdown Export.
10. Load the safe synthetic HTTP/2 Resource Exhaustion demo and confirm that it is synthetic, advisory, and non-operational.

## 8. Reading The Output

### Risk Level

Risk Level is produced by deterministic policy from the available evidence. It is not an LLM guess.

### Decision

Decision is simulated:

- `BLOCK`: simulated block recommendation.
- `MONITOR`: simulated monitoring or review recommendation.
- `ALLOW`: insufficient deterministic evidence to block or monitor.

### AI Analyst Brief

AI Analyst Brief summarizes the current event, deterministic reasoning, evidence gaps, and next review steps. It is advisory context only.

### Evidence Gap Analyzer

Evidence Gap Analyzer helps avoid overclaiming. For example, a payload rule match does not prove successful execution; telemetry, logs, EDR data, or network evidence may still be needed.

### Knowledge Q&A / RAG

Knowledge Q&A answers defensive security questions. Answers do not override Risk Level or Decision.

### Similar Cases / Graph

Similar cases and graph context support comparison and explanation. They do not prove compromise.

## 9. Screenshot Gallery

See [screenshots/README.md](screenshots/README.md) for the current screenshot gallery.

## 10. Validation Evidence

See:

- [TEST_REPORT.md](TEST_REPORT.md)
- [v2.8_release_gate.md](v2.8_release_gate.md)

## 11. Troubleshooting

- If Streamlit does not start, confirm that the virtual environment is active and Streamlit is installed.
- If Knowledge Q&A cannot answer, confirm that the local knowledge index exists.
- If Full AI-assisted mode is slow, use Fast deterministic mode for the primary demo path.

## 12. Final Reminder

Sentinel Project is an academic/demo prototype. It demonstrates safe triage architecture and AI advisory workflow. It is not a production IDS/IPS or autonomous response platform.
