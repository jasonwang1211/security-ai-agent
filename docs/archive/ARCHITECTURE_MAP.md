# Architecture Ownership Map

## 1. Purpose

This map documents current ownership boundaries for the v1.9 Architecture Cleanup and Orchestration Contracts work.

It is a planning document only. It does not move files, change import paths, create packages, wire runtime automation, or implement Tool Permission, Workflow Plan, Graph RAG, Knowledge Capture, Smart Router runtime, or ControllerAgent auto-execution.

Core safety boundaries remain unchanged:

- deterministic detector and policy own final security decisions
- LLM/RAG are advisory and explanation-only
- RAG is not a detection source
- BLOCK, MONITOR, and ALLOW are simulated decisions
- no real firewall, WAF, SIEM, SOAR, cloud, or endpoint action is performed

## 2. How to Read This Map

Runtime status labels:

- `active runtime`: used by current CLI or primary analysis flow
- `helper`: local helper used by an active path or protected helper path
- `staged`: implemented foundation or preview infrastructure not used as the default runtime
- `eval`: evaluation or regression infrastructure
- `docs`: documentation and release material

Movement guidance labels:

- `no`: keep as-is for now
- `defer`: revisit after ADRs and contract tests
- `possible later`: potential package migration target, but not in Phase 9A-1

## 3. Owner Cluster Table

| Owner cluster | Files | Responsibility | Runtime status | Should move later? |
|---|---|---|---|---|
| `runtime_cli` | `app.py`, `modules/agent.py`, `modules/mode_handlers.py`, `modules/responder.py` | CLI entrypoint, numbered mode handling, SecurityAgent flow, user-facing report formatting | active runtime | defer |
| `detector_rules` | `modules/detection_rules.py`, `modules/rule_loader.py`, `modules/detector.py`, `detections/blue_team/*` | YAML-backed rule schema, rule loading, deterministic detector adapter | active runtime | no |
| `risk_decision` | `modules/triage_policy.py`, risk/decision/defense models in `modules/types.py` | Risk scoring, decision policy, simulated defense action mapping | active runtime | no |
| `incident_evidence` | `modules/types.py`, `modules/evidence_correlator.py`, `modules/incident_exporter.py` | Evidence, finding, incident models, correlation, JSON incident export | active runtime / helper | defer |
| `log_pipeline` | `modules/log_pipeline.py`, `modules/log_ingestion_runner.py` | Log parsing, event normalization, aggregation, ingestion runner | active runtime / helper | defer |
| `rag_runtime` | `modules/rag_qa.py`, `modules/rag_query_planner.py`, `knowledge/*` | Active general security knowledge Q&A runtime and current knowledge lookup path | active runtime | defer |
| `rag_helpers` | `modules/rag_types.py`, `modules/rag_metadata.py`, `modules/rag_intent.py`, `modules/rag_retrieval_planner.py`, `modules/rag_source_assembly.py`, `modules/rag_explainers.py` | RAG v2 helper types, metadata, intent, retrieval planning, source citation, report/rule explainers | helper / staged | possible later |
| `report_followup` | `modules/report_followup.py` | Report-aware follow-up, EV/F-ID question handling, protected report/rule explanation helpers | active runtime / helper | defer |
| `controller_tools` | `modules/controller_agent.py`, `modules/controller_types.py`, `modules/tool_registry.py`, `modules/skill_catalog.py`, `modules/skill_wrappers.py` | Typed controller infrastructure, ToolSpec, ToolRegistry, skill catalog, local skill wrappers | staged | possible later |
| `router` | `modules/smart_router.py` | Rule-based route classification and preview text | staged | possible later |
| `guardrails` | `modules/llm_guardrails.py`, `modules/answer_guardrails.py` | LLM advisory validation and deterministic answer safety checks | helper | possible later |
| `eval` | `modules/eval_cases.py`, `modules/eval_runner.py`, `eval_cases/*` | Eval dataset loading, validation, and deterministic eval smoke summaries | eval | possible later |
| `analyst_ux` | `modules/analyst_suggestions.py` | Deterministic analyst follow-up suggestions | helper | possible later |
| `docs_release` | `README.md`, `REPORT.md`, `docs/ROADMAP.md`, `docs/TECH_NOTES.md`, `ARCHITECTURE_DEBT.md`, `demo_outputs.md` | Project entrypoint docs, demo walkthrough, roadmap, technical notes, architecture debt, demo excerpts | docs | no |

## 4. Runtime vs Staged Boundary

The active CLI runtime is the numbered mode flow through `app.py`, `modules/agent.py`, and `modules/mode_handlers.py`.

The active deterministic security path is rule loading, rule-based detection, triage policy, simulated defense decision mapping, report formatting, and incident/evidence helpers where used by the current flow.

`RAGQA` remains the active general knowledge Q&A runtime. RAG v2 modules are helper or staged infrastructure for source-cited report/rule explanation behavior and should not be described as replacing `RAGQA`.

ControllerAgent and ToolRegistry are typed controller infrastructure. They must not be described as autonomous orchestration, LLM-based tool selection, or runtime auto-execution.

Smart Router is rule-based route classification and preview infrastructure. It does not execute selected routes and is not the default CLI auto-route.

Eval modules and eval datasets are regression infrastructure, not production runtime.

## 5. Known Parallel Paths

`RAGQA` vs RAG v2 helpers:
`RAGQA` is the active general knowledge runtime. RAG v2 helpers provide typed, source-cited helper infrastructure and protected report/rule explanation support.

`followup_handler` vs `report_followup`:
`modules/followup_handler.py` owns point/context follow-up in the existing agent flow. `modules/report_followup.py` owns report-aware EV/F-ID questions and protected report/rule explanation helpers.

`ControllerAgent` vs Smart Router:
`ControllerAgent` is a deterministic typed dispatcher by explicit route or tool name. Smart Router classifies input and provides preview information. Neither path should become LLM-driven or auto-executing in Phase 9A-1.

Eval runner vs production runtime:
`modules/eval_runner.py`, `modules/eval_cases.py`, and `eval_cases/*` are evaluation and regression assets. They should not be imported by active runtime code unless separately scoped.

## 6. Migration Guidance

Do not move files in Phase 9A-1.

Do not change import paths, introduce packages, or create sub-packages in this phase.

Use this map before any future package migration. Potential future package destinations may include:

- `modules/rag/`
- `modules/controller/`
- `modules/eval/`
- `modules/guardrails/`
- `modules/ux/`

These package names are future planning placeholders only. They are not implemented, and no current import path should assume they exist.

Flat modules are acceptable until ownership is clear, ADRs exist, and focused contract tests protect behavior.

## 7. Risk Notes

Moving imports can create a large diff and broad regression risk.

Staged helpers can be mistaken for active runtime if documentation is vague.

Package migration before ADRs and contract tests can create duplicate architecture instead of cleanup.

The ownership map must not imply that Tool Permission Model, Workflow Plan Model, Graph RAG, Knowledge Capture, Smart Router runtime, ControllerAgent auto-execution, or real enforcement has been implemented.

## 8. Follow-up Actions

- ADR Foundation
- Tool Permission Contract
- Workflow Plan Contract
- Testing Strategy Documentation
- Optional Package Migration Plan after ADRs and contract tests
