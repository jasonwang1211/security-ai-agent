# Architecture Debt Engineering Journal

Current baseline: `v1.5-controller-agent` branch, based on tag `v1.4.0` on `main`

This document tracks structural debt cleanup as an engineering discipline: reducing module sprawl, consolidating thin wrappers, and preserving deterministic safety boundaries before adding more agentic behavior.

## Current Status

The project has reached a stable consolidated architecture with:

- Unified `Security Triage Report`
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- Raw auth log translation
- Log file ingestion and brute-force candidate aggregation
- `RAGQueryPlanner`-based knowledge QA
- Pydantic boundary models for future controller and tool work
- Evidence / Finding / Incident schemas and JSON Incident Report export
- Time-window authentication sequence correlation for Scenario A
- Advisory LLMAssist guardrails and report-aware follow-up
- YAML-based Detection-as-Code Lite rules with schema validation and metadata
- Isolated v1.5 ControllerAgent and Tool Registry infrastructure

## Consolidation Outcomes

| Area | Before | After | Outcome |
|---|---|---|---|
| Triage policy | `risk_scorer.py`, `decision_engine.py`, `defense_simulator.py` | `triage_policy.py` | Consolidated risk scoring, decision mapping, and simulated defense policy |
| LLM assist | `llm_threat_judge.py`, `llm_analyzer.py` | `llm_assist.py` | Unified advisory LLM behavior and fallback handling |
| CLI mode wrappers | `modules/skills/*` | `mode_handlers.py` | Consolidated thin CLI wrappers |
| Log ingestion | parser / normalizer / aggregator / adapter modules | `log_pipeline.py` | Consolidated parse -> normalize -> aggregate -> adapt flow |
| Boundary contracts | ad-hoc dictionaries | `modules/types.py` | Added Pydantic boundary models for future controller/tool work |
| Testing foundation | limited smoke coverage | golden + log pipeline + boundary + incident + detection-rule + controller tests | Current quality gate: `240 passed`, ruff, mypy |

## v1.3 Phase Outcomes

- Evidence / Finding / Incident schemas
- LLM Safety Layer Foundation
- Time-window auth sequence correlation
- JSON Incident Report export
- Minimal report-aware follow-up helper
- Evidence-grounded LLMAssist
- Scenario A integration test
- 11 `report_explainer` KB docs

Engineering note: v1.3 intentionally increased module count because the new modules represent separate responsibilities:

- `evidence_correlator.py`
- `incident_exporter.py`
- `llm_guardrails.py`
- `report_followup.py`

## v1.4 Phase Outcomes

- Detection rules moved into YAML files.
- Added `DetectionRule` schema and `RuleLoader`.
- Detector adapter now uses YAML rules as the primary path.
- Rule metadata exposed in detector results.
- Hard-coded signatures retained as conservative fallback during migration.
- Quality gate updated to `141 passed`.

Metrics note:

- Test count: `102 passed` -> `141 passed`
- New modules: `detection_rules.py`, `rule_loader.py`
- New rule directory: `detections/blue_team/`
- YAML rule files: 4
- Supported YAML attack types: XSS, SQL Injection, Path Traversal, Command Injection
- Hard-coded signatures retained as conservative fallback

New modules:

- `detection_rules.py`
- `rule_loader.py`

New rule folder:

- `detections/blue_team/`

## v1.5 Phase Outcomes

- Added typed ControllerAgent infrastructure while keeping existing CLI modes unchanged.
- Added deterministic dispatch by explicit route/tool name.
- Added six v1.5 wrapper skill contracts and thin wrappers.
- Verified `ToolRegistry`, Skill Catalog, Skill Wrappers, and `ControllerAgent` together through integration-style tests.
- Deferred Smart Router, Auto Route, LLM-driven routing, Rule Explainer, and Investigation Planner.

New modules:

- `controller_types.py`
- `tool_registry.py`
- `skill_catalog.py`
- `skill_wrappers.py`
- `controller_agent.py`

New tests:

- `test_controller_types.py`
- `test_tool_registry.py`
- `test_skill_catalog.py`
- `test_skill_wrappers.py`
- `test_controller_agent.py`
- `test_controller_agent_integration.py`

Quality gate:

- Previous v1.4 gate: `141 passed`
- Current v1.5 gate: `240 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed

Architecture note:

v1.5 intentionally keeps `ControllerAgent` isolated from CLI runtime. Existing CLI modes remain unchanged, and Smart Router is deferred.

## Current Quality Gate

- `python -m pytest` -> `240 passed`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed
- CI runs the same quality gate

## Remaining Engineering Notes

### ControllerAgent / Tool Registry

`ControllerAgent` now exists as an isolated deterministic dispatcher for typed tools. It is not wired into the CLI runtime yet. Future controller work should preserve deterministic policy boundaries and avoid LLM-driven routing until the planned Smart Router milestone.

### Follow-up Module Boundary

`followup_handler.py` and `report_followup.py` should be reviewed before or during v1.5 Tool Registry work. The goal is to decide whether point-based follow-up and report-aware EV/F-ID follow-up should remain separate tools or be unified behind one `ToolSpec`.

### Responder Size

`responder.py` owns unified report formatting and response playbooks. This keeps output consistent, but the file remains large.

Future cleanup can keep report formatting in `responder.py` while moving static playbook data into structured constants or knowledge files. Planned sequencing should follow [docs/ROADMAP.md](docs/ROADMAP.md).

### RAG Routing

`RAGQueryPlanner` supports preferred source selection for the current small knowledge base.

Future retrieval work can move toward metadata-driven retrieval with markdown frontmatter and Chroma metadata filtering. Planned sequencing should follow [docs/ROADMAP.md](docs/ROADMAP.md).

### Startup Cost

App startup may still initialize heavy RAG, embedding, and Chroma resources.

Future work should continue moving heavy components toward lazy initialization. Planned sequencing should follow [docs/ROADMAP.md](docs/ROADMAP.md).

## Out of Scope for Consolidation

- Building a large multi-agent architecture immediately
- Building a Red / Blue simulation lab during consolidation
- Supporting every real-world log format during consolidation
- Connecting to real firewall, WAF, EDR, SIEM, SOAR, or cloud policy actions

For planned future work after consolidation, see [docs/ROADMAP.md](docs/ROADMAP.md).
