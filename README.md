# AI-Assisted Blue-Team Security Triage Prototype

[![CI](https://github.com/jasonwang1211/security-ai-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/jasonwang1211/security-ai-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A hybrid blue-team security triage prototype: deterministic rule-based detection as the safety floor, with LLM and RAG layers used only for explanation and context. The LLM can suggest, but it never overrides the final system verdict. Local-first, defensive-only, and designed for academic SOC-style analysis.

[English](#english) | [繁體中文](#繁體中文)

## English

This project helps analysts review suspicious payloads, translate individual raw log lines, ingest and aggregate log files, ask RAG-based security knowledge questions, and read results through a unified `Security Triage Report`.

The system is a defensive academic prototype. It does not attack real targets or control real security infrastructure.

For detailed evaluation notes and CLI excerpts, see:

- [Demo & Evaluation Report](REPORT.md)
- [Demo Outputs](demo_outputs.md)

### The Problem

SOC-style triage has two common failure modes:

- Pure rule-based detection is stable, but misses contextual or behavior-based signals.
- Pure LLM-based detection is flexible, but can hallucinate and should not be trusted with blocking decisions.

This project explores a hybrid path: deterministic detection and policy produce the final verdict, while LLM and RAG layers explain, contextualize, and support analyst review.

### Key Features

| Layer | Component | Role |
|---|---|---|
| Detection | Rule-Based Detector + YAML Rules | Deterministic XSS, SQL Injection, Path Traversal, and Command Injection detection using YAML-based Detection-as-Code rules. |
| Triage | TriagePolicy | Risk scoring and simulated `BLOCK` / `MONITOR` / `ALLOW` decisions. |
| Pipeline | Log Pipeline | Parses, normalizes, aggregates, and adapts log inputs. |
| Knowledge | RAGQueryPlanner + RAG QA | Local defensive knowledge retrieval and explanation. |
| Assist | LLMAssist | Advisory reasoning only; it never overrides the final verdict. |
| Controller | ControllerAgent + Tool Registry | Typed v1.5 agent infrastructure for deterministic dispatch by explicit route or tool name. |
| Graph | Graph-Backed Explanation + KnowledgeDoc Seed Helpers | Deterministic `modules/graph/*` helper infrastructure for in-memory evidence/context structure, protected exact-reference explanations, and reviewed KnowledgeDoc seed candidates; not automatic Graph RAG retrieval. |
| Output | Security Triage Report | Unified report format across payload and log flows. |
| Incident | Evidence / Incident Capability | Stable EV-ID / F-ID evidence handling, sequence correlation, JSON Incident export, and report-aware follow-up. |

### Non-Goals

This prototype deliberately does not:

- Attack real systems or external targets.
- Execute real firewall, WAF, EDR, SIEM, SOAR, or cloud policy actions.
- Let LLM output override deterministic rule-based or policy decisions.
- Treat RAG retrieval as a primary detection layer.
- Replace production security monitoring systems.

`BLOCK`, `MONITOR`, and `ALLOW` are simulated training decisions only.

### Current Flow

```text
User Input
-> CLI Mode Handler
-> SecurityAgent
-> Rule-Based Detection / Log Pipeline / RAGQueryPlanner
-> TriagePolicy
-> LLMAssist
-> Unified Security Triage Report
```

Role separation:

- Rule-Based Detector, Log Pipeline, and TriagePolicy are deterministic.
- RAGQueryPlanner and RAG QA support knowledge retrieval and explanation.
- LLMAssist is advisory only.
- Unified Security Triage Report is the final output format.

### System Architecture

![English architecture diagram](docs/architecture_en.png)

Core modules:

- `app.py`: interactive CLI entry point
- `modules/mode_handlers.py`: CLI mode orchestration
- `modules/agent.py`: `SecurityAgent` coordination layer
- `modules/detector.py`: rule-based payload detection
- `modules/triage_policy.py`: risk, decision, and simulated defense policy
- `modules/llm_assist.py`: optional LLM-assisted explanation and suspicious behavior advice
- `modules/log_pipeline.py`: raw log parsing, normalization, aggregation, adaptation, and translation
- `modules/rag_query_planner.py`: RAG query planning and source preference selection
- `modules/rag_qa.py`: local knowledge retrieval and answer generation
- `modules/types.py`: Pydantic boundary types
- `modules/graph/types.py`: graph type contracts for in-memory snapshots
- `modules/graph/builder.py`: deterministic GraphSnapshot builder from structured inputs
- `modules/graph/lookup.py`: read-only graph lookup helpers
- `modules/graph/exporter.py`: JSON-ready graph snapshot export helpers
- `modules/graph/explainers.py`: protected exact-reference graph-backed explanation helper using explicit graph provenance
- `modules/graph/knowledge_doc_seed.py`: reviewed KnowledgeDoc metadata seed helper for narrow graph candidates from explicit `attack_types` / `rule_ids`

### v1.3 Evidence and Incident Capability

v1.3 moves the prototype from single-event triage toward incident-style evidence handling:

- Evidence / Finding / Incident Pydantic schemas
- Stable EV-ID and F-ID references
- Time-window authentication sequence correlation
- `possible_account_compromise` finding
- JSON Incident Report export
- Report-aware follow-up helper
- Evidence-grounded LLMAssist with guardrails
- Scenario A mixed auth log integration test
- 11 `report_explainer` KB docs

Boundaries:

- `possible_account_compromise` is suspicious, not confirmed compromise.
- v1.3 uses `HIGH / MONITOR`, not automatic `BLOCK`.
- LLMAssist remains advisory only.
- Final verdict remains deterministic and policy-controlled.
- No real enforcement actions are performed.

### v1.4 Detection-as-Code Lite

v1.4 moves payload signatures into deterministic YAML detection rules while preserving existing detector behavior:

- YAML-based detection rules under `detections/blue_team/`
- `DetectionRule` Pydantic schema
- YAML rule loader with schema validation
- Detector adapter using YAML as the primary detection path
- XSS / SQL Injection / Path Traversal / Command Injection migrated to YAML
- Rule metadata exposed: rule IDs, source paths, severity, confidence, MITRE techniques, and references
- Hard-coded signatures remain as a conservative fallback
- v1.4 test gate: `141 passed`

Boundaries:

- Detection remains deterministic and rule-based.
- This is not ML anomaly detection.
- Rules are not generated by LLMs.
- No real firewall, WAF, EDR, SIEM, SOAR, or cloud enforcement is performed.
- YAML metadata does not override `TriagePolicy`.

### v1.5 ControllerAgent and Tool Registry

v1.5 adds typed agent infrastructure without changing the current CLI behavior:

- `ToolRegistry` stores typed `ToolSpec` entries.
- `ControllerAgent` dispatches deterministically by explicit route or tool name.
- Six wrapper skills are defined: `payload_triage`, `raw_log_translate`, `log_file_ingest`, `rag_security_qa`, `report_followup`, and `incident_json_export`.
- Tool inputs and outputs are validated with Pydantic boundary models.
- Controller integration tests verify the registry, skill catalog, wrappers, and dispatcher together.
- No Auto Route mode, Smart Router, or LLM-driven tool selection is included in v1.5.
- Final verdicts remain deterministic and policy-controlled.
- Current test gate: `240 passed`.

Boundaries:

- v1.5 does not wire `ControllerAgent` into `app.py` or the CLI menu.
- Existing CLI modes remain unchanged.
- Controller unit and integration tests do not initialize real RAG, Chroma, embeddings, Ollama, ChatOllama, Torch, or `SecurityAgent`.

### v1.6 RAG v2 Foundation

v1.6 adds source-cited RAG v2 helper infrastructure while keeping the existing `RAGQA` runtime and CLI behavior unchanged:

- RAG v2 boundary types: `AnswerWithSources`, `SourceCitation`, `RAGRetrievalPlan`, and `ExtractedIds`.
- Frontmatter metadata support for the 11 `report_explainer` knowledge docs.
- Rule-based RAG intent classification.
- Exact ID extraction and lookup helpers for EV-ID, F-ID, INC-ID, rule IDs, and MITRE technique IDs.
- Metadata-aware retrieval planning without running vector retrieval.
- Source assembly from metadata candidates into `SourceCitation` and `AnswerWithSources`.
- Deterministic Report Explainer v2 and Rule Explainer v2 helpers.
- v1.6 quality gate: `366 passed`.

Boundaries:

- v1.6 helpers are not wired into the existing `modules/rag_qa.py` runtime yet.
- No Chroma, Ollama, embeddings, Torch, or LLM generation is introduced in these helper paths.
- RAG remains explanation-only and does not override deterministic verdicts, risk levels, or simulated decisions.

### v1.7 Answer Safety / Evaluation / Smart Router Foundation

v1.7 adds reliability infrastructure before user-facing router activation:

- Evaluation case foundation under `eval_cases/`.
- Deterministic `AnswerGuardrails` foundation, not an LLM classifier.
- Deterministic Evaluation Runner foundation.
- Rule-based Smart Router foundation.
- CI Gitleaks secret scanning.
- Reusable log ingestion runner moved into `modules/`.
- v1.7 quality gate: `445 passed`.

Boundaries:

- Smart Router is not wired into the CLI yet.
- Smart Router is rule-based, not LLM-based.
- RAG/LLM remain advisory and explanation-only.
- Final verdicts remain deterministic and policy-controlled.

### v1.8 Protected Runtime Wiring and Analyst UX

v1.8 adds the first narrow protected integration helpers while preserving existing CLI behavior:

- Protected report/rule explanation helpers through `report_followup.py`.
- AnswerGuardrails-protected fallback behavior for unsafe helper output.
- Smart Router preview mode that shows a route decision without executing tools.
- Deterministic analyst follow-up suggestions.
- v1.8 quality gate: `487 passed`.

Boundaries:

- `RAGQA` remains the active general knowledge QA runtime.
- Smart Router preview is not the default CLI path and does not execute tools.
- No LLM routing, final verdict override, or real firewall/WAF/SIEM/SOAR enforcement is introduced.

Traditional Chinese summary:

- v1.8 新增受保護的報告/規則說明 helper、AnswerGuardrails 安全 fallback、Smart Router preview，以及 deterministic 分析師追問建議。
- `RAGQA` 仍是一般知識問答 runtime；Smart Router preview 不會執行工具，也不是預設 CLI 路徑。
- 沒有 LLM routing、沒有 AI 覆蓋最終判定、沒有真實防火牆/WAF/SIEM/SOAR 執行。

### v1.9 Architecture Cleanup and Orchestration Contracts

v1.9 is an architecture and contract milestone, not a runtime feature release:

- Architecture ownership map for runtime, helper, staged, eval, and docs boundaries.
- ADR foundation for ControllerAgent, follow-up boundaries, RAGQA/RAG helper coexistence, Tool Permission Model, and Workflow Plan Model.
- Schema-only Tool Permission Contract in `modules/controller/tool_policy.py`.
- Schema-only Workflow Plan Contract in `modules/controller/workflow_types.py`.
- Testing Strategy documentation for unit, eval, import guard, release gate, and manual LLM/RAG smoke checks.
- Controlled RAG helper migration into `modules/rag/` with flat compatibility shims.
- Controlled controller/orchestration migration into `modules/controller/` with flat compatibility shims.
- Manual LLM/RAG smoke checklist documented as manual-only, not CI, and not executed.
- Historical v2.1 release-gate result: `600 passed`.

Boundaries:

- v1.9 does not implement Graph RAG or Knowledge Capture.
- v1.9 does not add LLM tool selection, runtime auto-execution, or Smart Router default CLI auto-route.
- v1.9 does not replace `RAGQA`.
- AI does not decide attacks or override Risk Level / Decision.
- `BLOCK`, `MONITOR`, and `ALLOW` remain simulated decisions.
- No real firewall, WAF, SIEM, SOAR, cloud, or endpoint enforcement is introduced.

### v2.0 Knowledge Graph Foundation

v2.0 adds a deterministic in-memory Knowledge Graph foundation. The graph is evidence/context structure, not detection authority:

- Typed graph contracts in `modules/graph/types.py`: `GraphNodeKind`, `GraphEdgeKind`, `GraphSourceRef`, `GraphNode`, `GraphEdge`, and `GraphSnapshot`.
- Snapshot builder in `modules/graph/builder.py` through `build_graph_snapshot(...)`.
- Read-only graph lookup helpers in `modules/graph/lookup.py`.
- JSON-ready export helpers in `modules/graph/exporter.py`.

Boundaries:

- The builder uses structured `Incident` objects and explicitly provided `DetectionRule` objects only.
- No YAML loading, file loading, free-text extraction, guessed relationships, Graph RAG retrieval, Knowledge Capture, LLM graph extraction, Neo4j, vector search, Chroma/Ollama/LLM calls, runtime orchestration, or tool execution is included.
- Graph lookup does not change Risk Level / Decision, replace the Rule-Based Detector, replace `RAGQA`, write knowledge, call LLMs, or execute tools.
- Deterministic detector / risk / decision remain final authority, and `BLOCK`, `MONITOR`, and `ALLOW` remain simulated decisions.

### v2.1 Graph-Backed Explanation MVP

v2.1 adds a protected exact-reference explanation helper over the v2.0 in-memory graph foundation:

- `modules/graph/explainers.py` adds `explain_graph_reference(snapshot, reference_id) -> AnswerWithSources`.
- Exact EV-ID, F-ID, rule ID, and INC-ID references can be explained from explicit graph nodes and edges with existing `SourceCitation` provenance.
- `modules/report_followup.py` adds `explain_graph_followup_protected(...)`, which routes graph answers through existing `AnswerGuardrails`.
- Scenario A focused coverage shows `EV-003` explicitly supporting `F-001` while `Decision` remains simulated `MONITOR`.

Boundaries:

- v2.1 is graph-backed explanation, not Graph RAG retrieval.
- It is a protected helper and tested integration capability, not CLI auto-routing or a new `app.py` mode.
- It does not implement Knowledge Capture, LLM graph extraction, vector search, runtime orchestration, tool execution, `RAGQA` replacement, Risk Level / Decision override, or real enforcement.

### v2.2 Curated RAG Graph Seed Foundation

v2.2 released as `v2.2.0`.

v2.2 promotes reviewed curated Traditional Chinese report-explainer content and adds narrow protected graph/knowledge assembly helpers:

- Promoted 9 reviewed Traditional Chinese report-explainer KB documents into live `knowledge/blue_team/report_explainer/`.
- Expanded live report-explainer coverage from 11 to 20 documents.
- Added minimal typed RAG metadata support for `title`, `review_status`, `finding_types`, `evidence_types`, `decision_labels`, and `tags`.
- Promoted documents use `schema_version: v2.2-live1` and `review_status: approved_for_runtime_promotion`.
- Five authentication documents remain retrieval/explanation context only and do not define graph-seed edges.
- Four verified rule explainers retain reviewed attack/rule metadata: XSS / `XSS-001` / `MEDIUM` / simulated `MONITOR`; SQL Injection / `SQLI-001` / `HIGH` / simulated `BLOCK`; Path Traversal / `PATH-001` / `HIGH` / simulated `BLOCK`; Command Injection / `CMD-001` / `HIGH` / simulated `BLOCK`.
- Resolved references were added before live promotion.
- `build_knowledge_doc_seed(...)` accepts parsed `KnowledgeDocMetadata` plus explicitly supplied `DetectionRule` objects.
- Seed candidates must be approved for runtime promotion and are cross-validated against supplied detection rules.
- The seed helper creates only `KNOWLEDGE_DOC -> ATTACK_TYPE` through `RELATED_TO_ATTACK` and `KNOWLEDGE_DOC -> DETECTION_RULE` through `MAPS_TO_RULE`.
- `combine_hybrid_explanation_protected(...)` combines already-built graph context and already-built curated knowledge context, preserves citations, and then applies existing deterministic guardrails.

Boundaries:

- Deterministic detector / risk / decision remain final authority.
- Graph and curated RAG context provide explanation/support only.
- `ALLOW`, `MONITOR`, and `BLOCK` remain simulated decisions.
- v2.2 implements protected hybrid explanation/context assembly using explicit graph context plus curated knowledge source context.
- v2.2 does not implement automatic Graph RAG retrieval, vector-to-graph expansion, Knowledge Capture, LLM graph extraction, `RAGQA` replacement, CLI auto-route, or real enforcement.
- Existing legacy KB documents remain supported; full corpus schema migration is deferred.

### v2.3 Controlled Retrieval and Structured Follow-Up

v2.3 released as `v2.3.0`.

v2.3 documents the committed and manually verified runtime scope on the feature branch:

- Mode 3 knowledge Q&A now tries controlled approved-source selection before the existing vector fallback for reviewed targets including SQL Injection, `CMD-001`, and `success_after_failures`.
- Mode 3 answers use the protected return path with Traditional Chinese safety boundary text, internal metadata-label suppression, canonical visible RAG / LLM terminology, and deterministic final-authority wording.
- Mode 1 payload analysis retains an in-memory `ActiveEventContext` containing only facts produced by the current payload-analysis flow.
- Mode 4 can answer current payload-event follow-ups about classification reasoning, matched rule/signature evidence, simulated Decision boundaries, exploitation uncertainty, and defensive investigation or remediation guidance.
- Mode 2 qualifying authentication logs create structured `Incident`, `Evidence`, and `Finding` values through existing deterministic correlation.
- Scenario A stores `ActiveAuthIncidentContext`, builds an explicit in-memory `GraphSnapshot` from the current incident, and shows a structured summary with `INC-20260501-001`, `EV-003`, `F-001`, `HIGH`, and simulated `MONITOR`.
- Mode 4 can explain `EV-003`, the explicit `EV-003` / `F-001` support relationship, why `MONITOR` was selected, why the sequence does not confirm account compromise, and defensive investigation next steps.
- Non-qualifying Mode 2 log analysis clears stale structured context so follow-up cannot accidentally use an older incident.

Boundaries:

- v2.3 includes graph-grounded follow-up for the current structured authentication incident only.
- The graph facts come from explicit current-event `GraphSnapshot` relationships, not LLM-generated graph reasoning.
- v2.3 does not implement direct-input Auto Router, Agent Skill Orchestration, LLM-assisted skill selection, Similar-Case Graph RAG, approved historical-case retrieval, Knowledge Capture or event write-back, automatic vector-to-graph expansion, the deferred Mode 3 KnowledgeDoc graph-expansion WIP, real firewall/WAF/EDR/account action, or RAG/LLM override of deterministic `Risk Level` or `Decision`.

### v2.4 Deterministic Agent Skill Orchestration Runtime

v2.4 release gate passed; ready to tag. The current released baseline remains tag `v2.3.0` until the v2.4 tag, merge, and push are completed.

Direct-input Agent runtime:

- Direct user input is now the primary CLI interaction path.
- Users can enter a suspicious payload, authentication log path, active-context follow-up question, or general security knowledge question without selecting Mode 1 / 2 / 3 / 4 first.
- Typing `menu` preserves the legacy four-mode interface as a debug/demo fallback.

Deterministic skill orchestration:

- The runtime deterministically routes to `AnalyzePayloadSkill`, `AnalyzeAuthenticationLogSkill`, `ExplainActiveEventSkill`, `ExplainActiveIncidentSkill`, or `KnowledgeQASkill`.
- Skill selection is deterministic and not LLM-selected.
- The skill layer wraps already-working v2.3 runtime capabilities; it does not redefine detector, incident, graph, or RAG authority.
- `ToolPolicy` permits approved read/analysis flows and keeps future write-capable behavior blocked or approval-required.

Active-context behavior:

- Payload analysis can retain `ActiveEventContext`; qualifying authentication log analysis can retain `ActiveAuthIncidentContext`.
- Structured current-event/current-incident follow-up takes precedence when applicable.
- General knowledge Q&A may run while an active context exists and does not overwrite that structured context.
- v2.4 reuses v2.3 event-grounded payload follow-up, graph-grounded current authentication incident follow-up, and protected controlled knowledge Q&A.

Focused implementation validation already completed:

- Pytest: `110 passed in 1.64s`
- Ruff: passed
- Mypy: passed across 108 source files
- `git diff --check`: passed
- Mojibake scan over v2.4-A touched files: no known corrupted fragments found

Manual runtime smoke was also completed for direct payload input, direct authentication log input, active-context follow-up, protected SQL Injection knowledge Q&A, and `menu` legacy fallback.

Boundaries:

- v2.4 does not implement or release LLM-assisted skill selection, `RetrieveSimilarCaseSkill`, executable `DraftCaseCaptureSkill`, Similar-Case Graph RAG, historical-case retrieval, Knowledge Capture or event write-back, automatic live ingestion, real firewall/WAF/EDR/account enforcement, real monitoring deployment, or RAG/LLM override of deterministic `Risk Level` or `Decision`.
- Any future write-capable capture skill must require explicit approval and human review before live ingestion.
### CLI Modes

```text
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

### Testing And Quality Checks

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Run tests, lint, and gradual typing checks:

```powershell
python -m pytest
python -m ruff check .
python -m mypy app.py modules tests
```

Last full release-gate test result: `693 passed in 14.72s` for v2.4.

v2.4 full release gate passed: `python -m pytest` -> `693 passed in 14.72s`, Ruff passed, Mypy passed across 108 source files, `git diff --check` passed, and Gitleaks (`gitleaks detect --source . --verbose --redact`) passed with no leaks found across 171 commits scanned. The local gate used a fresh writable pytest basetemp directory: `C:\Users\jason\Desktop\sentinel_pytest_runs\v2_4_gate_02389f227c3b468c9aca3b7b774e7190`.

Historical v2.3 full release gate remains recorded separately: `670 passed in 8.23s`, Ruff passed, Mypy passed across 106 source files, `git diff --check` passed, and Gitleaks found no leaks across 167 commits scanned.

Historical v2.2 full release gate remains recorded separately: `628 passed`, Ruff passed, Mypy passed across 99 source files, `git diff --check` passed, and Gitleaks found no leaks across 160 commits scanned.

v2.2 focused validation remains recorded separately: Batch 2.2-A `67 passed`, Ruff passed, Mypy passed, and `git diff --check` passed; Batch 2.2-B `96 passed`, Ruff passed, Mypy passed, and `git diff --check` passed.

The test suite includes expanded golden smoke tests, direct consolidated log pipeline tests, Pydantic boundary model tests, incident/export/follow-up/guardrail tests, Scenario A integration coverage for a mixed authentication log, and deterministic v2.4 skill orchestration coverage. Deterministic tests do not start the full app or initialize RAGQA, Chroma, embeddings, Torch, Ollama, ChatOllama, or local LLM clients. GitHub Actions CI runs the same quality gate.

### Local Model Prerequisites

Ollama should be installed and running locally before using the CLI.

Required local models:

- `qwen2.5:7b`
- `gemma4:e4b`

Exact model names can be changed in `config.py`.

### How To Run

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ingest_knowledge.py
python app.py
```

### Current Status

Current release baseline: tag `v2.3.0`.

Current phase: v2.4 release gate passed; ready to tag.

目前 release baseline：tag `v2.3.0`。
目前里程碑：v2.4 release gate 已通過；準備 tag。

Completed:

- Unified `Security Triage Report`
- Raw log translation and brute-force candidate aggregation
- Rule-based detection for XSS, SQL Injection, Path Traversal, and Command Injection
- `RAGQueryPlanner`
- Pydantic boundary types for gradual controller and tool registry work
- v1.3 Evidence and Incident Capability, including stable EV-ID/F-ID contracts, `possible_account_compromise` correlation, JSON Incident Report export, report-aware follow-up, LLMAssist guardrails, Scenario A integration coverage, and 11 `report_explainer` KB docs
- v1.4 Detection-as-Code Lite, including YAML rules, schema validation, detector adapter, rule metadata, and hard-coded fallback
- v1.5 ControllerAgent and Tool Registry infrastructure, including typed tool specs, deterministic dispatch, six wrapper skills, and integration tests
- v1.6 RAG v2 Foundation, including source-cited helper types, metadata parsing, intent classification, exact ID extraction, metadata-aware planning, source assembly, and deterministic report/rule explainers
- v1.7 Answer Safety / Evaluation / Smart Router Foundation, including eval cases, deterministic answer guardrails, eval runner, isolated rule-based Smart Router, CI Gitleaks, and reusable log ingestion runner cleanup
- v1.8 Protected Runtime Wiring and Analyst UX, including protected report/rule explanation helpers, guarded fallback behavior, Smart Router preview mode, and deterministic analyst suggestions
- v1.9 Architecture Cleanup and Orchestration Contracts, including architecture ownership map, ADR foundation, Tool Permission Contract, Workflow Plan Contract, Testing Strategy, controlled RAG/controller package migrations with flat compatibility shims, and manual LLM/RAG smoke checklist documentation
- v2.0 Knowledge Graph Foundation, including typed graph contracts, snapshot builder, read-only graph query helpers, JSON-ready snapshot export, and the 2A-3 decision to defer KnowledgeDoc graph seeding until a metadata audit
- v2.1 Graph-Backed Explanation MVP, including exact EV-ID, F-ID, rule ID, and INC-ID graph explanations from explicit graph edges with existing `SourceCitation` provenance and `AnswerGuardrails` protection
- v2.2 Curated RAG Graph Seed Foundation, including 9 promoted reviewed Traditional Chinese report-explainer KB documents, 20 live report-explainer docs, minimal typed metadata support, reviewed KnowledgeDoc graph seed candidates, and protected hybrid graph/knowledge explanation assembly
- v2.3 Controlled Retrieval and Structured Follow-Up, including protected controlled Mode 3 retrieval, Mode 1 active payload-event follow-up, and Mode 2 current-incident graph-grounded authentication follow-up
- v2.4 Deterministic Agent Skill Orchestration Runtime, including direct-input primary CLI path, deterministic read/analysis skill routing, active-context preservation, protected knowledge Q&A reuse, and legacy menu fallback
- Expanded golden smoke tests, direct log pipeline tests, focused boundary model tests, `pytest`, `ruff`, lenient `mypy`, and GitHub Actions CI

### Further Reading

- [Technical Notes](docs/TECH_NOTES.md) — Engineering deep-dive covering Detection-as-Code, Evidence/Incident modeling, LLM guardrails, MITRE metadata, and testing strategy.
- [Roadmap](docs/ROADMAP.md) — Version plan and future milestones.
- [Architecture Debt Journal](ARCHITECTURE_DEBT.md) — Engineering consolidation notes.
- [Demo & Evaluation Report](REPORT.md) — Demo walkthrough and verification.

### Roadmap

**✅ v1.3 — Evidence and Incident Capability** (Completed)

See [docs/ROADMAP.md](docs/ROADMAP.md) for delivered items.

**✅ v1.4 — Detection-as-Code Lite** (Completed)

- YAML-based detection rules
- `DetectionRule` schema and YAML rule loader
- Detector adapter using YAML as the primary detection path
- Severity, confidence, references, and MITRE technique metadata
- XSS / SQL Injection / Path Traversal / Command Injection migrated to YAML
- Hard-coded signatures retained as conservative fallback

**✅ v1.5 — ControllerAgent and Tool Registry** (Completed on `v1.5-controller-agent`)

- Typed `ToolSpec` contracts and `ToolRegistry`
- Deterministic `ControllerAgent` dispatch by explicit route/tool name
- Six wrapper skills
- No Auto Route, Smart Router, or LLM-driven tool selection

**✅ v1.6 — RAG v2 Foundation** (Released as `v1.6.0`)

- Source-cited RAG v2 helper infrastructure
- Metadata/frontmatter for 11 `report_explainer` docs
- Exact ID extraction / lookup
- Metadata-aware retrieval planning
- Source citations and `AnswerWithSources`
- Deterministic Report Explainer v2 and Rule Explainer v2 helpers
- Not wired into the existing `RAGQA` runtime

**v1.7 - Answer Safety, Evaluation, and Smart Router Foundation** (Completed foundation)

- v1.7 foundation: evaluation datasets, deterministic AnswerGuardrails, Evaluation Runner, and isolated rule-based Smart Router
- Smart Router is not CLI-wired yet, and no LLM-based routing is introduced

**v1.8 - Protected Runtime Wiring and Analyst UX** (Release-ready foundation)

- Protected report/rule explanation helpers, guarded fallback behavior, Smart Router preview, and deterministic analyst suggestions
- Existing CLI modes and `RAGQA` remain unchanged
- Smart Router preview does not execute tools and is not the default CLI route
- No LLM routing, verdict override, or real enforcement

**v1.9 - Architecture Cleanup and Orchestration Contracts** (Release-ready documentation and contract milestone)

- Architecture ownership map, ADR foundation, Tool Permission Contract, Workflow Plan Contract, Testing Strategy, and Package Migration Plan
- Controlled RAG helper and controller/orchestration package migrations with flat compatibility shims
- Manual LLM/RAG smoke checklist documented as manual-only, not CI, and not executed
- Contract/schema-only; no runtime auto-execution, LLM tool selection, Graph RAG, Knowledge Capture, RAGQA replacement, AI verdict override, or real enforcement

**v2.0 - Knowledge Graph Foundation** (Released as `v2.0.0`)

- Typed graph contracts, snapshot builder, read-only graph query helpers, and JSON-ready snapshot export
- No `rule_graph.py` for now; explicit `DetectionRule` seed remains inside the builder
- KnowledgeDoc graph seed is deferred until a metadata audit
- Graph RAG retrieval, Knowledge Capture, LLM graph extraction, Neo4j, vector search, runtime orchestration, tool execution, and `RAGQA` replacement remain deferred

**v2.1 - Graph-Backed Explanation MVP** (Release gate passed previously)

- `modules/graph/explainers.py` adds `explain_graph_reference(snapshot, reference_id) -> AnswerWithSources`
- Exact EV-ID, F-ID, rule ID, and INC-ID references can be explained from explicit graph nodes and edges with protected citations
- `modules/report_followup.py` adds `explain_graph_followup_protected(...)`, which routes graph answers through existing `AnswerGuardrails`
- Rule IDs such as `CMD-001` and `DETECTION_RULE:CMD-001` normalize outward-facing `rule_ids` to stable IDs while citations retain graph provenance
- This is a protected helper and tested integration capability, not CLI auto-routing, an `app.py` mode, Graph RAG retrieval, Knowledge Capture, `RAGQA` replacement, decision override, or real enforcement

**v2.2 - Curated RAG Graph Seed Foundation** (Released as `v2.2.0`)

- 9 reviewed Traditional Chinese report-explainer KB documents promoted into live `knowledge/blue_team/report_explainer/`
- Live report-explainer coverage expanded from 11 to 20 documents
- Minimal typed metadata support for `title`, `review_status`, `finding_types`, `evidence_types`, `decision_labels`, and `tags`
- Reviewed KnowledgeDoc graph seed helper for explicit `attack_types` / `rule_ids` cross-validated against supplied `DetectionRule` objects
- Protected hybrid explanation helper that combines already-built graph context and curated knowledge context, then applies existing guardrails
- Scenario A authentication hybrid context keeps `Decision` simulated `MONITOR`; Command Injection hybrid context keeps `Decision` simulated `BLOCK`
- Boundary: no automatic Graph RAG retrieval, vector-to-graph expansion, Knowledge Capture, LLM graph extraction, `RAGQA` replacement, CLI auto-route, Risk Level / Decision override, or real enforcement

**v2.3 - Controlled Retrieval and Structured Follow-Up** (Released as `v2.3.0`)

- Mode 3 protected controlled retrieval for reviewed knowledge targets before vector fallback
- Mode 1 `ActiveEventContext` follow-up for the latest payload/event analysis
- Mode 2 `ActiveAuthIncidentContext` and current-incident `GraphSnapshot` follow-up for Scenario A authentication correlation
- Manual smoke verified Command Injection `HIGH / BLOCK` remains simulated and does not prove command execution
- Manual smoke verified Scenario A `INC-20260501-001`, `EV-003`, `F-001`, `HIGH / MONITOR` with explicit graph facts and no confirmed-compromise claim
- Boundary: no Auto Router, Skill Orchestration, LLM-assisted skill selection, Similar-Case Graph RAG, Knowledge Capture, event write-back, real enforcement, real monitoring deployment, or Risk Level / Decision override

For the full plan, see [docs/ROADMAP.md](docs/ROADMAP.md).

## 繁體中文

這是一個混合式藍隊安全分流原型：以「可重現的規則式偵測」作為安全地板，LLM 與 RAG 只負責解釋、補充脈絡與輔助分析。LLM 可以提出建議，但不能覆蓋最終系統判定。本專案採本地優先、防禦導向設計，適合學術展示與 SOC-style 分析流程。

### 專案簡介

本專案協助分析可疑 payload、轉換單筆原始日誌、匯入並聚合日誌檔案、回答以 RAG 為基礎的資安知識問題，並以統一 Security Triage Report 呈現結果。

這是一個防禦導向的學術原型，不會攻擊真實目標，也不會控制真實安全基礎設施。

詳細評估紀錄與 CLI 範例可參考：

- [Demo & Evaluation Report](REPORT.md)
- [Demo Outputs](demo_outputs.md)

### 問題背景

SOC-style 事件分流常見兩個問題：

- 純規則式偵測穩定，但容易漏掉需要上下文判讀的行為型訊號。
- 純 LLM 偵測彈性高，但可能幻覺，不適合直接決定封鎖或放行。

本專案採混合式設計：由 deterministic detection 與 policy 產生最終判定，LLM 與 RAG 只負責解釋、脈絡補充與輔助分析。

### 主要功能

| 層級 | 元件 | 說明 |
|---|---|---|
| Detection | Rule-Based Detector + YAML Rules | 以 YAML-based Detection-as-Code 規則進行 XSS、SQL Injection、Path Traversal、Command Injection 的 deterministic 偵測。 |
| Triage | TriagePolicy | 負責風險評估與模擬 `BLOCK` / `MONITOR` / `ALLOW` 決策。 |
| Pipeline | Log Pipeline | 解析、正規化、聚合並轉接日誌輸入。 |
| Knowledge | RAGQueryPlanner + RAG QA | 提供本地防禦知識檢索與解釋。 |
| Assist | LLMAssist | 只提供輔助推理，不覆蓋最終系統判定。 |
| Output | Security Triage Report | 在 payload 與 log flow 中提供統一報告格式。 |

### 非目標

本 prototype 明確不做以下事情：

- 不攻擊真實系統或外部目標。
- 不執行真實 firewall、WAF、EDR、SIEM、SOAR 或 cloud policy 動作。
- 不讓 LLM 輸出覆蓋 deterministic rule-based 或 policy 決策。
- 不把 RAG 檢索當作主要偵測層。
- 不取代正式 production security monitoring system。

`BLOCK`、`MONITOR`、`ALLOW` 都是模擬訓練決策。

### 目前流程

```text
使用者輸入
-> CLI 模式處理器
-> SecurityAgent
-> 規則式偵測 / 日誌管線 / RAGQueryPlanner
-> TriagePolicy
-> LLMAssist
-> 統一 Security Triage Report
```

角色分工：

- Rule-Based Detector、Log Pipeline、TriagePolicy 是 deterministic。
- RAGQueryPlanner 與 RAG QA 負責知識檢索與解釋。
- LLMAssist 只提供 advisory 建議。
- 統一 Security Triage Report 是最終輸出格式。

### 系統架構

![繁體中文架構圖](docs/architecture_zh.png)

主要模組：

- `app.py`：互動式 CLI 入口
- `modules/mode_handlers.py`：CLI 模式協調
- `modules/agent.py`：`SecurityAgent` 協調層
- `modules/detector.py`：規則式 payload 偵測
- `modules/triage_policy.py`：風險、決策與模擬防禦策略
- `modules/llm_assist.py`：選用的 LLM 輔助解釋與可疑行為建議
- `modules/log_pipeline.py`：原始日誌解析、正規化、聚合、轉接與轉譯
- `modules/rag_query_planner.py`：RAG 查詢規劃與偏好來源選擇
- `modules/rag_qa.py`：本地知識檢索與回答生成
- `modules/types.py`：Pydantic boundary types

### CLI 模式

```text
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
```

### 測試與品質檢查

```powershell
python -m pytest
python -m ruff check .
python -m mypy app.py modules tests
```

最近一次完整 release gate 測試結果為 v2.4：`693 passed in 14.72s`，Ruff、Mypy（108 source files）、`git diff --check` 與 Gitleaks（no leaks found；171 commits scanned）均通過。v2.4 release gate 已通過；準備 tag；目前 release baseline 仍為 `v2.3.0`。

測試使用 dummy RAG 與 LLMAssist 物件，不會啟動完整 CLI，也不會初始化 RAGQA、Chroma、embeddings、Torch、Ollama、ChatOllama 或本地 LLM client。GitHub Actions CI 會執行同一組品質檢查。

### 目前狀態

Current release baseline: tag `v2.3.0`.

Current phase: v2.4 release gate passed; ready to tag.

目前 release baseline：tag `v2.3.0`。
目前里程碑：v2.4 release gate 已通過；準備 tag。

已完成：

- 統一 Security Triage Report
- 原始日誌轉譯與 brute-force candidate 聚合
- XSS、SQL Injection、Path Traversal、Command Injection 的規則式偵測
- `RAGQueryPlanner`
- Pydantic boundary types 基礎
- v1.4 Detection-as-Code Lite：YAML detection rules、`DetectionRule` schema、YAML rule loader、detector adapter、rule metadata，並保留 hard-coded fallback
- v1.5 ControllerAgent / Tool Registry infrastructure：typed `ToolSpec`、deterministic dispatch、six wrapper skills 與 integration tests
- v1.6 RAG v2 Foundation：source-cited helper types、frontmatter metadata、intent classification、exact ID lookup、metadata-aware planning、source assembly、Report Explainer v2 / Rule Explainer v2
- v1.7 Answer Safety / Evaluation / Smart Router Foundation
- v1.8 Protected Runtime Wiring and Analyst UX
- v1.9 Architecture Cleanup and Orchestration Contracts：完成 ownership map、ADR foundation、Tool Permission / Workflow Plan contracts、受控的 RAG/controller migration 與 flat compatibility shims，並新增 manual smoke checklist 文件
- v2.0 知識圖譜基礎：新增圖譜型別契約、決定性圖譜建構器、唯讀查詢輔助函式、可序列化為 JSON 的匯出輔助函式；2A-3 決策為 KnowledgeDoc 圖譜種子延後到 metadata 盤點後再處理
- v2.1 Graph-Backed Explanation MVP：新增 `modules/graph/explainers.py`，可針對 EV-ID、F-ID、rule ID 與 INC-ID 從明確圖譜節點與邊產生受保護、帶 citation 的解釋
- v2.2 Curated RAG Graph Seed Foundation：已將 9 篇 reviewed Traditional Chinese report-explainer KB 文件提升到 live corpus，使 live report-explainer 從 11 篇擴充到 20 篇；新增最小 typed metadata、reviewed KnowledgeDoc graph seed helper，以及 protected hybrid graph/knowledge explanation assembly
- v2.3 Controlled Retrieval and Structured Follow-Up：Mode 3 受保護 controlled retrieval、Mode 1 active payload-event follow-up，以及 Mode 2 current-incident GraphSnapshot authentication follow-up 已完成實作；已發布為 `v2.3.0`
- 圖譜是證據與脈絡結構，不作為偵測權威或最終判定來源；graph lookup 不會改變 Risk Level / Decision、不會取代規則式偵測器或 `RAGQA`、不會呼叫 LLM、自動寫入知識或執行工具
- 邊界：仍是 deterministic rule-based detection，不是 ML detection，也不是 LLM-generated rules；YAML metadata 不會覆蓋 `TriagePolicy`
- expanded golden smoke tests、direct log pipeline tests、boundary model tests、`pytest`、`ruff`、寬鬆 `mypy` 與 GitHub Actions CI

### 延伸閱讀

- [Technical Notes](docs/TECH_NOTES.md)：整理 Detection-as-Code、Evidence/Incident model、LLM guardrails、MITRE metadata 與測試策略。
- [Roadmap](docs/ROADMAP.md)：版本規劃與後續里程碑。
- [Architecture Debt Journal](ARCHITECTURE_DEBT.md)：架構整理與技術債紀錄。
- [Demo & Evaluation Report](REPORT.md)：Demo 流程與驗證紀錄。

### Roadmap / 後續規劃

**✅ v1.3 — Evidence and Incident Capability / 證據與事件能力**（已完成）

已交付項目請見 [docs/ROADMAP.md](docs/ROADMAP.md)。

**✅ v1.4 — Detection-as-Code Lite / YAML 規則式偵測**（已完成）

- YAML-based detection rules / YAML 偵測規則
- `DetectionRule` schema and YAML rule loader / `DetectionRule` schema 與 YAML rule loader
- Detector adapter using YAML as primary path / detector adapter 以 YAML 作為主要偵測路徑
- Severity, confidence, references, and MITRE technique metadata / 嚴重度、信心值、參考資料與 MITRE 技術 metadata
- XSS / SQL Injection / Path Traversal / Command Injection signatures migrated to YAML / 已將 XSS、SQL Injection、Path Traversal、Command Injection signatures 移至 YAML
- Hard-coded signatures remain as fallback / hard-coded signatures 保留作為保守 fallback

**✅ v1.5 — ControllerAgent and Tool Registry / ControllerAgent 與 Tool Registry**（已完成）

- Typed `ToolSpec` contracts and `ToolRegistry`
- Deterministic `ControllerAgent` dispatch by explicit route/tool name
- Six wrapper skills
- No Auto Route, Smart Router, or LLM-driven tool selection

**✅ v1.6 — RAG v2 Foundation / RAG v2 基礎**（已完成）

- 11 份 `report_explainer` docs 的 frontmatter metadata
- EV-ID / F-ID / INC-ID / rule ID / MITRE technique ID extraction 與 lookup helpers
- metadata-aware retrieval planner
- SourceCitation / AnswerWithSources source assembly
- deterministic Report Explainer v2 與 Rule Explainer v2 helpers
- 尚未接入既有 `RAGQA` runtime；沒有新增 Chroma / Ollama / LLM generation

完整規劃請見 [docs/ROADMAP.md](docs/ROADMAP.md)。

**v1.7 - Answer Safety, Evaluation, and Smart Router Foundation / 答案安全、評估與 Smart Router 基礎**（foundation 已完成）

- small regression eval cases / 小型回歸評估案例
- deterministic AnswerGuardrails / deterministic 答案安全檢查
- deterministic Evaluation Runner / deterministic 評估執行器
- isolated rule-based Smart Router / 隔離的 rule-based Smart Router
- 尚未接入 CLI；沒有 LLM-based routing；final verdict 仍由 deterministic policy 控制

**v1.8 - Protected Runtime Wiring and Analyst UX / 受保護 runtime wiring 與分析師 UX**（release-ready foundation）

- protected report/rule explanation helpers / 受保護的報告與規則說明 helper
- AnswerGuardrails fallback / deterministic 安全 fallback
- Smart Router preview only / Smart Router 只預覽、不執行工具
- deterministic analyst suggestions / deterministic 分析師追問建議
- `RAGQA` remains active; no LLM routing, verdict override, or real enforcement

**v1.9 - Architecture Cleanup and Orchestration Contracts**（已完成）

- Architecture ownership map、ADR foundation、Tool Permission / Workflow Plan contracts
- Controlled RAG/helper 與 controller/orchestration package migrations，並保留 flat compatibility shims
- Manual LLM/RAG smoke checklist documented as manual-only
- Boundary: no runtime auto-execution, LLM tool selection, Graph RAG, Knowledge Capture, RAGQA replacement, AI verdict override, or real enforcement

**v2.0 - 知識圖譜基礎**（已發布為 `v2.0.0`）

- 圖譜型別契約：`GraphNodeKind`、`GraphEdgeKind`、`GraphSourceRef`、`GraphNode`、`GraphEdge`、`GraphSnapshot`
- 決定性圖譜建構器：`build_graph_snapshot(...)`
- 唯讀查詢輔助函式，以及可序列化為 JSON 的匯出輔助函式
- 2A-3 決策：KnowledgeDoc 圖譜種子延後到 metadata 盤點後再處理
- 邊界：圖譜是證據與脈絡結構，不作為偵測權威或最終判定來源；graph lookup 不會改變 Risk Level / Decision、不會取代規則式偵測器或 `RAGQA`、不會呼叫 LLM、自動寫入知識或執行工具

**v2.1 - Graph-Backed Explanation MVP**（release gate 已於前一里程碑通過）

- `explain_graph_reference(snapshot, reference_id)` 可用明確圖譜邊解釋 EV-ID、F-ID、rule ID 與 INC-ID
- `explain_graph_followup_protected(...)` 會將圖譜解釋交給既有 `AnswerGuardrails` 保護
- `SourceCitation.metadata` 重用真實圖譜節點、邊與 source provenance；沒有擴充 RAG schema
- Scenario A 展示 `EV-003` 明確支援 `F-001`，且 incident `Decision` 仍為 `MONITOR`
- 這不是 Graph RAG retrieval，也不是 CLI auto-routing、`app.py` 新模式、Knowledge Capture、`RAGQA` replacement、Risk Level / Decision override、tool execution 或 real enforcement

**v2.2 - Curated RAG Graph Seed Foundation**（已發布為 `v2.2.0`）

- 9 篇 reviewed Traditional Chinese report-explainer KB 文件已提升到 live `knowledge/blue_team/report_explainer/`
- live report-explainer coverage 從 11 篇擴充到 20 篇
- 新增 `title`、`review_status`、`finding_types`、`evidence_types`、`decision_labels`、`tags` 的最小 typed metadata 支援
- `build_knowledge_doc_seed(...)` 只接收 parsed `KnowledgeDocMetadata` 與明確提供的 `DetectionRule` objects，並只從 reviewed `attack_types` / `rule_ids` 產生候選圖譜邊
- `combine_hybrid_explanation_protected(...)` 只組合已建立的 graph context 與 curated knowledge context，保留 citations，並套用既有 deterministic guardrails
- `BLOCK`、`MONITOR`、`ALLOW` 仍是 simulated decisions；graph 與 curated RAG context 只提供 explanation/support，不會覆蓋 Risk Level 或 Decision
