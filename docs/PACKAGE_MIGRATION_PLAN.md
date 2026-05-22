# Package Migration Plan

## 1. Purpose

This document is part of the v1.9 Architecture Cleanup and Orchestration Contracts work.

Its purpose is to plan whether the current flat `modules/` structure should eventually be migrated into sub-packages. It does not perform that migration.

Phase 9A-6 is documentation-only:

- no files are moved
- no import paths are changed
- no packages or sub-packages are created
- no tests are modified
- no runtime behavior is changed

## 2. Current Problem

`modules/` is currently a flat structure.

That flat layout has been workable, but ownership is becoming harder to scan as the project adds RAG helpers, ControllerAgent infrastructure, eval support, guardrails, analyst UX helpers, and orchestration contracts.

Directly moving files now would create a large import diff and could hide behavior changes. A package migration should therefore be planned before it is implemented.

The immediate problem is not that flat modules are broken. The problem is that future cleanup should avoid mixing file moves, import rewrites, runtime wiring, and feature work in the same phase.

## 3. Current Ownership Basis

Future package migration should start from the owner clusters already documented in the architecture map:

- `runtime_cli`
- `detector_rules`
- `risk_decision`
- `incident_evidence`
- `log_pipeline`
- `rag_runtime`
- `rag_helpers`
- `report_followup`
- `controller_tools`
- `router`
- `guardrails`
- `eval`
- `analyst_ux`
- `docs_release`

These owner clusters are planning input only. They do not mean that package migration has happened.

## 4. Candidate Future Packages

The following package names are candidate future destinations only. They are not created in Phase 9A-6, and no current import path should assume they exist.

### `modules/rag/`

Potential owner for:

- active RAGQA runtime
- RAG v2 helper types and metadata
- retrieval planning
- source citation and source assembly
- report and rule explainers

Active `RAGQA` should not be moved early. Helper-only files are safer candidates for an earlier migration phase.

### `modules/controller/`

Potential owner for:

- `ControllerAgent`
- `ToolSpec`
- `ToolRegistry`
- `SkillCatalog`
- skill wrappers

This package should remain deterministic orchestration infrastructure. Migration must not turn ControllerAgent into LLM-based tool selection or runtime auto-execution.

### `modules/eval/`

Potential owner for:

- eval case models
- eval runner

Eval files are likely lower-risk migration candidates because they are regression infrastructure, not production runtime.

### `modules/guardrails/`

Potential owner for:

- `AnswerGuardrails`
- LLM guardrails
- answer safety checks

Guardrails should remain advisory and deterministic safety checks. Migration must not make LLM output a final detection source.

### `modules/ux/`

Potential owner for:

- analyst suggestions
- Smart Router preview, if later decided
- protected explanation UX helpers, if later separated

Smart Router must remain preview-only unless a later phase explicitly wires a guarded runtime path.

### `modules/pipeline/` or `modules/log_pipeline/`

Potential owner for:

- log parser
- event normalizer
- event aggregator
- log ingestion runner

The package name should be chosen only when ownership is stable enough to avoid another rename.

### `modules/core/` or `modules/security_core/`

Potential owner for:

- detector
- risk scorer
- decision engine
- defense simulator
- incident and evidence models, if appropriate

This is the highest-risk candidate area because it includes active security behavior. It should not be moved early.

## 5. Migration Principles

Package migration should follow these principles:

- migrate only after tests are green
- migrate one package at a time
- preserve behavior during migration
- do not add runtime wiring during migration
- preserve public imports or add compatibility shims if needed
- avoid mixing migration with feature work
- run the full quality gate after every package move
- do not move files just for aesthetics
- move only when ownership is stable

Migration should not change the security model:

- deterministic detector and policy keep final authority
- RAG/LLM remains advisory and explanation-only
- RAG/LLM is not a detection source
- LLM output must not override Risk Level or Decision
- BLOCK, MONITOR, and ALLOW remain simulated decisions
- no real firewall, WAF, SIEM, SOAR, cloud, or endpoint enforcement is added

## 6. Suggested Migration Order

### Phase M1 - Eval Package

Move eval-related files only, if low risk:

- eval case models
- eval runner

This should be the first candidate because eval infrastructure is not production runtime.

### Phase M2 - RAG Helper Package

Move RAG helper-only files:

- RAG types
- metadata helpers
- intent helpers
- retrieval planner
- source assembly
- explainers

Do not move active `RAGQA` in this phase.

### Phase M3 - Controller Package

Move controller and tool infrastructure:

- controller types
- ControllerAgent
- ToolRegistry
- SkillCatalog
- skill wrappers

This phase should preserve deterministic dispatch and must not add auto-execution.

### Phase M4 - Guardrails Package

Move guardrail helpers:

- answer guardrails
- LLM guardrails
- safety checks

This phase should preserve advisory-only behavior.

### Phase M5 - Active Runtime Review

Consider active runtime files only after helper moves are stable.

Candidates may include runtime CLI helpers, active RAGQA, detector/risk/decision core, log pipeline, and incident/evidence models. These should be split into smaller phases if approved.

### Phase M6 - Docs Sync And Compatibility Cleanup

Update docs after actual migration phases.

Remove compatibility shims only when imports are stable, tests are green, and the public import surface is no longer needed.

## 7. Files Not Recommended To Move Early

Do not move these early:

- `app.py`
- active `RAGQA` runtime
- detector, risk, and decision core
- CLI mode handlers
- anything imported by app startup
- anything with Chroma, Ollama, embedding, LLM, or ChatOllama side effects

Reasons:

- runtime import risk
- startup behavior risk
- large diff risk
- increased chance of circular imports
- higher chance of hiding behavior changes inside mechanical moves

## 8. Test Strategy For Migration

For any future package migration phase, run:

- focused tests for the moved owner cluster
- full `python -m pytest`
- `python -m ruff check .`
- `python -m mypy app.py modules tests`
- relevant import guard tests
- `git diff --check`

Manual app smoke may be useful after a migration phase is complete, but it is not part of this planning phase.

Do not run normal CI against local LLM, Chroma, Ollama, embedding, or Torch startup paths.

## 9. Risks

Package migration risks include:

- import path breakage
- circular imports
- stale docs
- duplicated compatibility shims
- moving staged helpers in a way that makes them look runtime-active
- large diffs hiding behavior changes
- mixing feature work with file moves

The highest-risk areas are active CLI startup, active RAGQA runtime, detector/risk/decision core, and any module with local LLM or vector-store side effects.

## 10. Non-Goals

Phase 9A-6 does not include:

- file moves
- import changes
- package or sub-package creation
- code changes
- test changes
- runtime changes
- workflow execution
- Graph RAG implementation
- Knowledge Capture implementation
- ControllerAgent auto-execution
- Smart Router runtime wiring
- detector, risk, or decision behavior changes

## 11. Follow-up Actions

- Phase 9A-7: docs sync and release gate
- future v1.9.x or v2.0 package migration phase, if needed
- future Graph RAG planning only after ownership is stable
- future Knowledge Capture planning only after ownership is stable
