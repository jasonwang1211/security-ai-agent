# AI-Assisted Blue-Team Security Triage Prototype

This project is an AI-assisted blue-team security triage prototype. It helps analysts review suspicious payloads, translate individual raw log lines, ingest and aggregate log files, ask RAG-based security knowledge questions, and read the result through a unified `Security Triage Report`.

The system is a defensive academic prototype. It does not attack real targets or control real security infrastructure.

## What It Supports

- Payload / event analysis
- Single raw log translation
- Log file ingestion and aggregation
- RAG-based security knowledge Q&A
- Unified `Security Triage Report` output

For detailed evaluation notes and CLI excerpts, see:

- [Demo & Evaluation Report](REPORT.md)
- [Demo Outputs](demo_outputs.md)

## Current CLI Modes

```text
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

## Key Features

| Feature | Purpose |
|---|---|
| Rule-Based Detector | Detects known payload attacks such as XSS, SQL Injection, and Path Traversal. |
| Consolidated Log Pipeline | `modules/log_pipeline.py` parses, normalizes, aggregates, adapts, and translates log inputs. |
| CLI Mode Handlers | `modules/mode_handlers.py` contains the lightweight CLI mode wrappers used by `app.py`. |
| Raw Log Input Adapter | Translates a single raw log line into an event-oriented triage input. |
| RAGQueryPlanner | Plans security knowledge queries and supports preferred source selection. |
| RAG Knowledge Q&A | Answers defensive security questions using local knowledge and retrieval. |
| LLMAssist | Provides alert explanation and suspicious behavior suggestions while leaving final decisions to the system flow. |
| TriagePolicy | Owns risk scoring, decision mapping, and simulated defense policy. |
| Unified Security Triage Report | Presents triage results in one consistent report format. |
| Simulated Defense Decision | Produces simulated `BLOCK`, `MONITOR`, or `ALLOW` decisions. |

## Current Pipelines

### A. Payload Triage

```text
User Payload
-> Rule-Based Detector
-> TriagePolicy
-> Security Triage Report
```

### B. Single Raw Log Triage

```text
Raw Log Line
-> Log Pipeline
-> Event-to-Agent Input
-> Authentication Failure Triage Report
```

### C. Log File Triage

```text
Log File
-> Log Pipeline
-> SecurityAgent
-> Security Triage Report
```

### D. RAG QA

```text
Security Question
-> RAGQueryPlanner
-> Preferred Source Selection / Chroma Retrieval
-> RAG Answer
```

## Sample Output Summaries

### XSS Payload

```text
Status: ALERT
Attack Type: XSS
Risk Level: MEDIUM
Decision: MONITOR
```

### Single Raw Auth Log

```text
Status: REVIEW
Attack Type: Authentication Failure
Risk Level: LOW
Decision: MONITOR
```

### auth_bruteforce.log

```text
Status: SUSPICIOUS
Attack Type: Brute Force
Risk Level: HIGH or MEDIUM
Decision: MONITOR
```

## Safety Boundaries

- Rule-Based Detector is the primary detection layer for known payload attacks.
- RAG is for explanation and knowledge support only.
- LLM Assist provides suggestions only.
- Final `Decision` belongs to the system decision flow.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions.
- The system does not control real firewalls, WAF, EDR, cloud policies, or production response systems.
- This is a defensive academic prototype.

## Project Structure

```text
sentinel_project/
├── app.py
├── config.py
├── demo_log_ingestion.py
├── demo_outputs.md
├── REPORT.md
├── README.md
├── requirements.txt
├── demo_logs/
│   ├── web_attack.log
│   └── auth_bruteforce.log
├── knowledge/
│   └── blue_team/
│       ├── attack_techniques/
│       ├── detection_rules/
│       ├── response_playbooks/
│       ├── security_controls/
│       ├── anomaly_analysis/
│       └── report_guides/
└── modules/
    ├── agent.py
    ├── mode_handlers.py
    ├── detector.py
    ├── triage_policy.py
    ├── llm_assist.py
    ├── responder.py
    ├── log_pipeline.py
    ├── rag_qa.py
    ├── rag_query_planner.py
    └── followup_handler.py
```

## Local Model Prerequisites

Ollama should be installed and running locally before using the CLI.

Required local models:

- `qwen2.5:7b`
- `gemma4:e4b`

Pull them with:

```bash
ollama pull qwen2.5:7b
ollama pull gemma4:e4b
```

Exact model names can be changed in `config.py`.

## How to Run

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Prepare the local RAG knowledge base:

```bash
python ingest_knowledge.py
```

Run the CLI:

```bash
python app.py
```

## Running Tests

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Run the golden smoke tests:

```powershell
python -m pytest
```

Run lint and gradual typing checks:

```powershell
python -m ruff check .
python -m mypy app.py modules tests
```

Pytest runs the golden smoke tests. Ruff checks style, imports, and common lint issues. Mypy is configured in lenient mode as a gradual typing foundation.

These tests use dummy RAG and LLM Assist objects, so they do not start the full app or initialize Chroma, embeddings, Torch, Ollama, or local LLM clients.

## Model Configuration

| Purpose | Model |
|---|---|
| RAG answer generation | `qwen2.5:7b` |
| Agent / Threat Judge | `gemma4:e4b` |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |

## Current Status

Current working branch:

```text
v1.1.4-event-to-agent-adapter
```

Current milestone:

```text
v1.1.5-unified-triage-rag-routing
```

Completed:

- Unified `Security Triage Report`
- Raw log translation
- `auth_failure` triage
- Brute force candidate triage
- `RAGQueryPlanner`
- Mode 3 dedicated knowledge QA route

## Future Work

Next:

- Smart Input Router / Main Controller Agent
- Lazy Initialization
- JSON incident report export
- More realistic log formats
- Web dashboard
- Hybrid multi-agent architecture
- Red / blue simulation lab
