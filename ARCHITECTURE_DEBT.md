# Architecture Debt and Consolidation Plan

Current milestone: `v1.1.5-unified-triage-rag-routing`

## Current Status

The project has reached a stable demo milestone with:

- Unified `Security Triage Report`
- Payload triage
- Raw auth log triage
- Log file ingestion and aggregation
- `RAGQueryPlanner`-based knowledge QA

This document records the current architecture debt and consolidation progress. The project is intentionally moving from a working prototype toward a cleaner, easier-to-maintain architecture.

## Completed Consolidation

- Triage policy completed: `risk_scorer.py`, `decision_engine.py`, and `defense_simulator.py` were consolidated into `modules/triage_policy.py`.
- LLM assist completed: `llm_threat_judge.py` and `llm_analyzer.py` were consolidated into `modules/llm_assist.py`.
- CLI mode handler consolidation completed: `modules/skills/*` was consolidated into `modules/mode_handlers.py`.
- Log pipeline consolidation completed: `log_parser.py`, `event_normalizer.py`, `event_aggregator.py`, `event_to_agent_input.py`, and `log_input_adapter.py` were consolidated into `modules/log_pipeline.py`.

## Current Architecture Debt

### A. ControllerAgent / Tool Registry

`SecurityAgent` currently works as an orchestrator / workflow controller. It coordinates detection, scoring, decisioning, response simulation, LLM assist, and report generation.

It is not yet a true tool-calling agent.

Future direction: introduce a Main Controller Agent with a tool registry, where detection, triage, log handling, RAG QA, and reporting can be exposed as explicit tools.

### B. Responder Size

`responder.py` owns unified report formatting and response playbooks. This makes the report output consistent, but the file is currently large.

Future direction: keep report formatting in `responder.py`, but move static playbook data into structured constants or knowledge files.

### C. RAG Routing

`RAGQueryPlanner` currently supports preferred source selection. This is useful for the current small knowledge base.

Future direction: move toward metadata-driven retrieval with markdown frontmatter and Chroma metadata filtering.

### D. Startup Cost

App startup still initializes heavy RAG, embedding, and Chroma resources.

Future direction: broader lazy initialization so each heavy component loads only when its CLI mode or controller tool needs it.

### E. Schemas / Common Types

Most pipeline contracts are still plain dictionaries. This is flexible for the prototype, but it makes cross-module contracts easy to drift.

Future direction: introduce lightweight shared schemas or common types for detector results, normalized events, triage policy results, LLM assist results, and report inputs.

## Consolidation Roadmap

### Phase 1: Triage Policy Consolidation

- Completed: `risk_scorer.py`, `decision_engine.py`, and `defense_simulator.py` were consolidated into `modules/triage_policy.py`.

### Phase 2: LLM Assist Consolidation

- Completed: `LLMThreatJudge` and `LLMSecurityAnalyzer` were consolidated into `modules/llm_assist.py`.

### Phase 3: Skill Handler Preparation

- Completed: CLI skill handlers were consolidated into `modules/mode_handlers.py`.

### Phase 3B: Log Pipeline Consolidation

- Completed: log parser, normalizer, aggregator, event-to-agent adapter, and raw log input adapter were consolidated into `modules/log_pipeline.py`.

### Phase 4: Responder Playbook Refactor

- Keep unified report formatting in `responder.py`.
- Move static response playbooks into structured constants or knowledge files.

### Phase 5: Lazy Initialization

- Defer RAG, embedding, Chroma, and local LLM initialization until needed.

### Phase 6: ControllerAgent / Tool Registry

- Introduce a future `ControllerAgent` and explicit tool registry for routing analysis, RAG QA, log ingestion, and reporting workflows.

## Non-Goals

- Do not build a 10-agent architecture now.
- Do not build a Red / Blue simulation lab now.
- Do not support every log format now.
- Do not connect to a real firewall, WAF, or EDR.
