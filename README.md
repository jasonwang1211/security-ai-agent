# Sentinel Project - AI-Assisted Blue-Team Security Triage

Sentinel Project is a defensive security triage prototype. It shows how a blue-team analyst can turn suspicious input or incident evidence into a reproducible attack classification, deterministic risk level, simulated decision, advisory AI/RAG context, and reviewable report output.

## Why This Project Exists

Many AI security demos blur an important boundary: they make AI appear to decide whether something is an attack and what action should be taken. Sentinel Project intentionally avoids that pattern.

The project keeps detection and decision-making deterministic, then uses AI/RAG-style features only to help analysts explain, compare, investigate, and document the case. AI is an advisory layer, not the final authority.

## System Flow

```text
User input
-> Rule-Based Detector
-> Attack classification
-> Risk Level
-> Decision
-> AI / RAG advisory context
-> Report output
```

The authority path and advisory path are separated. Rule-based detection and deterministic policy own the verdict. AI Analyst Brief, Evidence Gap Analyzer, Knowledge Q&A / RAG, Approved Similar Cases, and Relationship Graph provide analyst context only.

## Core Design Principles

- Detection is rule-based, not AI-generated.
- Risk Level and Decision are produced by deterministic logic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions.
- RAG, LLM, AI Analyst Brief, and Evidence Gap Analyzer provide advisory context only.
- Historical cases, RAG answers, and graph context do not prove current compromise or successful execution.

## Demo Highlights

- Fast deterministic mode for reproducible rule-based triage.
- Optional Full AI-assisted mode for local AI/RAG explanation paths.
- Lazy RAG startup so fast startup does not eagerly load Chroma, embeddings, Torch, or other heavy dependencies.
- Language-aware output policy for advisory panels and RAG prompt context.
- AI Analyst Brief for analyst-facing event summaries and next steps.
- Evidence Gap Analyzer for missing evidence, unsafe assumptions, and review tasks.
- Knowledge Q&A / RAG for defensive security knowledge questions.
- Approved Similar Cases for curated historical comparison.
- Relationship Graph for event, rule, risk, decision, and case context.
- Case Draft and Markdown Export for human-reviewed reporting.
- Safe synthetic HTTP/2 Resource Exhaustion scenario with no traffic generation.

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated.
- RAG, LLM, AI Analyst Brief, and Evidence Gap provide advisory context only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, proof-of-concept, or traffic generation is provided.
- Human review is required.

## Quick Start

Use a normal PowerShell workflow and replace the repository URL with your own remote.

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

If Knowledge Q&A / RAG is unavailable after rebuilding the environment, confirm that the local knowledge index has been created and follow the project documentation for rebuilding it.

## Documentation

- [User Operation Guide](docs/USER_OPERATION_GUIDE.md)
- [Test Report](docs/TEST_REPORT.md)
- [Code Review Audit](docs/CODE_REVIEW_AUDIT.md)
- [v2.8 Release Gate](docs/v2.8_release_gate.md)
- [Screenshot Gallery](docs/screenshots/README.md)

## Validation

Current validation summary:

- pytest: `1168 passed`
- ruff: passed
- mypy: passed
- gitleaks: passed with `.gitleaksignore` false-positive handling
- screenshot refresh: completed

These checks validate the demo behavior and safety boundaries. They do not claim production IDS/IPS effectiveness.

## Limitations

- This is not a production IDS or IPS.
- It does not actually block attacks.
- It is not a red-team attack tool.
- It does not generate attack traffic.
- It does not provide exploit or proof-of-concept steps.
- AI is not the final decision-maker.
- RAG, LLM output, similar cases, and graph context cannot override the deterministic detector or decision policy.

## Roadmap / Future Work

- Clearer separation between public documentation, historical release notes, and local demo materials.
- Richer analyst timeline and event replay support.
- More defensive synthetic incident scenarios.
- Deeper read-only graph and approved-case memory integration.
- Report export polish for review and presentation workflows.
