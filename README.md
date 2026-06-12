# Sentinel Project - AI-Assisted Blue-Team Security Triage

Sentinel Project is a defensive security triage prototype with a Streamlit SOC analyst console. It combines deterministic rule-based detection, deterministic Risk Level / Decision logic, simulated response decisions, and advisory AI/RAG context into a reviewable blue-team workflow.

The main demo is not a backend API. It is an analyst-facing console that lets reviewers load safe scenarios, run deterministic analysis, inspect AI advisory panels, compare approved cases, view graph context, and export human-reviewed reports.

## Screenshot Showcase

### Streamlit Analyst Console

![Streamlit analyst console home](docs/screenshots/en/01_console_home.png)

The console home shows the primary demo surface: language and mode controls, scenario launcher cards, input area, active context, and safety messaging.

### AI Analyst Brief

![AI Analyst Brief panel](docs/screenshots/en/03_ai_analyst_brief.png)

The AI Analyst Brief summarizes the current event in analyst language while keeping the deterministic verdict separate from advisory explanation.

### Evidence Gap Analyzer

![Evidence Gap Analyzer panel](docs/screenshots/en/04_evidence_gap_analyzer.png)

The Evidence Gap Analyzer highlights confirmed facts, missing evidence, review tasks, and unsafe assumptions. It does not override Risk Level or Decision.

### HTTP/2 Resource Exhaustion Safe Demo

![HTTP/2 Resource Exhaustion safe synthetic demo](docs/screenshots/en/09_http2_resource_exhaustion_demo.png)

The HTTP/2 scenario is a safe synthetic incident summary. It demonstrates defensive triage without exploit steps, proof-of-concept material, or traffic generation.

## Why This Project Matters

Many AI security demos blur an important line: they make AI appear to decide whether an event is an attack and what action should be taken. That is unsafe for a blue-team workflow because advisory text can be mistaken for a final verdict.

Sentinel Project intentionally separates deterministic authority from AI advisory support:

- The Rule-Based Detector and deterministic policy own classification, Risk Level, and Decision.
- AI Analyst Brief, Evidence Gap Analyzer, Knowledge Q&A / RAG, Similar Cases, and Relationship Graph explain and enrich the investigation.
- Human review remains required before any operational action outside the demo.

## What It Does

| Capability | What it demonstrates | Authority level |
|---|---|---|
| Rule-Based Detector | Identifies supported payload and incident patterns with reproducible rules. | Detection authority |
| Deterministic Risk / Decision | Produces Risk Level and simulated BLOCK / MONITOR / ALLOW decisions. | Decision authority |
| Streamlit Analyst Console | Provides the main interactive SOC analyst demo UI. | Presentation layer |
| AI Analyst Brief | Summarizes what happened, why it matters, verdict context, next steps, and unsafe assumptions. | Advisory only |
| Evidence Gap Analyzer | Lists confirmed facts, missing evidence, recommended checks, and unsafe assumptions. | Advisory only |
| Knowledge Q&A / RAG | Answers defensive security questions from approved knowledge context. | Advisory only |
| Approved Similar Cases | Compares current context with curated approved seed cases. | Advisory only |
| Relationship Graph | Displays event, rule, risk, decision, and case context as graph-oriented analyst context. | Advisory only |
| Case Draft / Markdown Export | Produces human-reviewed draft and export material for reporting. | Human review required |
| HTTP/2 Resource Exhaustion safe synthetic demo | Demonstrates DoS/resource-exhaustion triage without traffic generation. | Safe demo only |

## Streamlit Analyst Console

UI entry point:

```text
ui/streamlit_app.py
```

Launch command:

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

Recommended demo flow:

1. Select Fast deterministic mode.
2. Load the Command Injection demo or HTTP/2 Resource Exhaustion safe demo.
3. Click Run input.
4. Review attack type, Risk Level, and simulated Decision.
5. Review AI Analyst Brief and Evidence Gap Analyzer.
6. Review Knowledge Q&A / RAG, Approved Similar Cases, and Relationship Graph.
7. Review Case Draft and Markdown Export.

The UI does not perform real defensive actions. It does not block, monitor, disable accounts, update cloud policy, deploy SIEM/SOAR actions, or generate attack traffic.

## Architecture

```text
User input / demo scenario
  -> Rule-Based Detector
  -> Attack classification
  -> Deterministic Risk Level
  -> Simulated Decision
  -> Advisory context
     -> AI Analyst Brief
     -> Evidence Gap Analyzer
     -> Knowledge Q&A / RAG
     -> Approved Similar Cases
     -> Relationship Graph
  -> Human-reviewed Case Draft / Markdown Export
```

| Path | Owns | Must not do |
|---|---|---|
| Authority path | Rule-based detection, attack classification, Risk Level, Decision. | Depend on LLM output for final verdicts. |
| Advisory path | AI/RAG explanation, evidence gaps, similar cases, graph context, draft/export support. | Override current Risk Level or Decision. |
| Human review path | Analyst interpretation, report review, operational decisions outside the demo. | Treat simulated decisions as real enforcement. |

## Demo Scenarios

| Scenario | Input type | Expected classification | Risk Level | Simulated Decision | What it demonstrates | Screenshot |
|---|---|---|---|---|---|---|
| Command Injection demo | Payload text | Command Injection | HIGH | BLOCK | Deterministic payload triage, rule evidence, AI advisory panels, evidence gaps. | [AI Analyst Brief](docs/screenshots/en/03_ai_analyst_brief.png) |
| Authentication incident demo | Authentication log path or synthetic log content | Possible Account Compromise | HIGH | MONITOR | Suspicious login sequence triage without claiming confirmed compromise. | [Console home](docs/screenshots/en/01_console_home.png) |
| HTTP/2 Resource Exhaustion safe synthetic demo | Synthetic incident summary | HTTP/2 Resource Exhaustion Suspicion | MEDIUM | MONITOR | Safe DoS/resource-exhaustion triage with no traffic generation. | [HTTP/2 demo](docs/screenshots/en/09_http2_resource_exhaustion_demo.png) |
| Optional Full AI-assisted mode | User-selected mode | Depends on input | Deterministic policy remains authoritative | Simulated only | Optional AI/RAG explanation path while preserving the safety boundary. | [Full AI-assisted optional](docs/screenshots/en/10_full_ai_assisted_optional.png) |

## Quick Start

Use a normal PowerShell workflow and replace the repository URL with your own remote.

```powershell
git clone <your-repo-url>
cd sentinel_project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

CLI mode remains available for direct command-line use:

```powershell
python app.py
```

## Repository Structure

```text
ui/                         Streamlit analyst console
modules/                    Detector, RAG, advisory, graph, controller helpers
detections/blue_team/       Rule-based detection rules
knowledge/                  Defensive knowledge corpus
data/approved_case_seeds/   Approved similar-case seed data
docs/                       Public documentation
docs/screenshots/           Screenshot gallery
docs/zh-TW/                 Traditional Chinese docs
tests/                      Regression and boundary tests
```

## Documentation Map

### Start here

- [Project report](REPORT.md)
- [User operation guide](docs/USER_OPERATION_GUIDE.md)

### UI / demo walkthrough

- [UI walkthrough](docs/UI_WALKTHROUGH.md)
- [Screenshot gallery](docs/screenshots/README.md)

### Validation

- [Test report](docs/TEST_REPORT.md)
- [v2.8 release gate](docs/v2.8_release_gate.md)

### Architecture / review

- [Technical notes](docs/TECH_NOTES.md)
- [Roadmap](docs/ROADMAP.md)
- [Code review audit](docs/CODE_REVIEW_AUDIT.md)

### Traditional Chinese

- [Traditional Chinese overview](docs/zh-TW/README.zh-TW.md)
- [Traditional Chinese project report](docs/zh-TW/PROJECT_REPORT.zh-TW.md)

## Validation

Current validation summary:

- pytest: `1168 passed`
- ruff: passed
- mypy: passed
- gitleaks: passed with `.gitleaksignore` false-positive handling
- screenshot refresh: completed

These checks validate demo behavior and safety-boundary regressions. They do not claim production IDS/IPS effectiveness.

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit / PoC / traffic generation is provided.
- Human review is required.

## Limitations and Non-Goals

- Not a production IDS/IPS.
- Not a red-team tool.
- Not an exploit generator.
- Not an autonomous response system.
- Not a final AI decision engine.
- Not a replacement for SIEM, SOAR, EDR, vulnerability management, or incident response approval.

## Roadmap

- Keep public documentation, historical release notes, and local demo aids clearly separated.
- Add more defensive synthetic incident scenarios.
- Improve analyst timeline and event replay workflows.
- Expand read-only graph and approved-case memory context while preserving advisory boundaries.
- Polish report export and release packaging for review-ready demos.
