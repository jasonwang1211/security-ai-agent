# Architecture Debt and Consolidation Plan

Current milestone: `v1.1.5-unified-triage-rag-routing`

## Current Status

The project has reached a stable demo milestone with:

- Unified `Security Triage Report`
- Payload triage
- Raw auth log triage
- Log file ingestion and aggregation
- `RAGQueryPlanner`-based knowledge QA

This document records the current architecture debt before consolidation work begins. The project is intentionally moving from a working prototype toward a cleaner, easier-to-maintain architecture.

## Current Architecture Debt

### A. SecurityAgent Naming

`SecurityAgent` currently works as an orchestrator / workflow controller. It coordinates detection, scoring, decisioning, response simulation, LLM assist, and report generation.

It is not yet a true tool-calling agent.

Future direction: introduce a Main Controller Agent with a tool registry, where detection, triage, log handling, RAG QA, and reporting can be exposed as explicit tools.

### B. Thin Modules

The following modules are small policy components:

- `risk_scorer.py`
- `decision_engine.py`
- `defense_simulator.py`

They currently provide useful separation, but may be too thin as standalone modules.

Future direction: consolidate them into `triage_policy.py` to keep risk, decision, and simulated defense policy in one coherent place.

### C. LLM Overlap

`llm_threat_judge.py` and `llm_analyzer.py` have overlapping responsibilities around LLM-assisted security interpretation.

Future direction: merge them into `llm_assist.py` with separate methods for:

- Alert explanation
- Suspicious behavior judging

### D. Skill Layer

Current skills are CLI handlers / wrappers. They are useful because they keep `app.py` clean and make each CLI mode easier to understand.

They should not be described as independent agents.

Future direction: convert these handlers into controller tools that can later be registered with a Main Controller Agent.

### E. Responder Size

`responder.py` owns unified report formatting and response playbooks. This makes the report output consistent, but the file is currently large.

Future direction: keep report formatting in `responder.py`, but move static playbook data into structured constants or knowledge files.

### F. RAG Routing

`RAGQueryPlanner` currently supports preferred source selection. This is useful for the current small knowledge base.

Future direction: move toward metadata-driven retrieval with markdown frontmatter and Chroma metadata filtering.

### G. Startup Cost

App startup still initializes heavy RAG, embedding, Chroma, and local LLM resources.

Future direction: lazy initialization so each heavy component loads only when its CLI mode or controller tool needs it.

## Consolidation Roadmap

### Phase 1: Triage Policy Consolidation

- Consolidate `risk_scorer.py`, `decision_engine.py`, and `defense_simulator.py` into `triage_policy.py`.

### Phase 2: LLM Assist Consolidation

- Merge `LLMThreatJudge` and `LLMSecurityAnalyzer` into `LLMAssist`.

### Phase 3: Skill Handler Preparation

- Prepare current skill handlers for a future tool registry.

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

