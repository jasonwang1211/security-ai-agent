# Architecture Debt Engineering Journal

Current baseline: `v1.2-documentation-and-test-stabilization`

This document tracks structural debt cleanup as an engineering discipline: reducing module sprawl, consolidating thin wrappers, and preserving deterministic safety boundaries before adding more agentic behavior.

## Current Status

The project has reached a stable consolidated architecture with:

- Unified `Security Triage Report`
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- Raw auth log translation
- Log file ingestion and brute-force candidate aggregation
- `RAGQueryPlanner`-based knowledge QA
- Pydantic boundary models for future controller and tool work

## Consolidation Outcomes

| Area | Before | After | Outcome |
|---|---|---|---|
| Triage policy | `risk_scorer.py`, `decision_engine.py`, `defense_simulator.py` | `triage_policy.py` | Consolidated risk scoring, decision mapping, and simulated defense policy |
| LLM assist | `llm_threat_judge.py`, `llm_analyzer.py` | `llm_assist.py` | Unified advisory LLM behavior and fallback handling |
| CLI mode wrappers | `modules/skills/*` | `mode_handlers.py` | Consolidated thin CLI wrappers |
| Log ingestion | parser / normalizer / aggregator / adapter modules | `log_pipeline.py` | Consolidated parse -> normalize -> aggregate -> adapt flow |
| Boundary contracts | ad-hoc dictionaries | `modules/types.py` | Added Pydantic boundary models for future controller/tool work |
| Testing foundation | limited smoke coverage | golden + log pipeline + boundary tests | Current quality gate: `30 passed`, ruff, mypy |

## Current Quality Gate

- `python -m pytest` -> `30 passed`
- `python -m ruff check .`
- `python -m mypy app.py modules tests`
- CI runs the same quality gate

## Remaining Engineering Notes

### ControllerAgent / Tool Registry

`SecurityAgent` currently works as an orchestrator / workflow controller. It coordinates detection, scoring, decisioning, response simulation, LLM assist, and report generation.

It is not yet a true tool-calling agent. Future controller work should preserve deterministic policy boundaries and use typed tool input/output contracts.

### Responder Size

`responder.py` owns unified report formatting and response playbooks. This keeps output consistent, but the file remains large.

Future cleanup can keep report formatting in `responder.py` while moving static playbook data into structured constants or knowledge files.

### RAG Routing

`RAGQueryPlanner` supports preferred source selection for the current small knowledge base.

Future retrieval work can move toward metadata-driven retrieval with markdown frontmatter and Chroma metadata filtering.

### Startup Cost

App startup may still initialize heavy RAG, embedding, and Chroma resources.

Future work should continue moving heavy components toward lazy initialization.

## Out of Scope for Consolidation

- Building a large multi-agent architecture immediately
- Building a Red / Blue simulation lab during consolidation
- Supporting every real-world log format during consolidation
- Connecting to real firewall, WAF, EDR, SIEM, SOAR, or cloud policy actions

For planned future work after consolidation, see [docs/ROADMAP.md](docs/ROADMAP.md).
