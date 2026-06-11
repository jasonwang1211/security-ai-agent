# Testing Strategy

## 1. Purpose

This document records the v1.9 testing strategy for Architecture Cleanup and Orchestration Contracts.

Its purpose is to organize test categories, ownership, release gates, manual LLM/RAG smoke checks, and deferred test debt. It does not change test behavior, move test files, add helpers, update pytest configuration, or introduce new CI jobs.

The core safety model remains unchanged:

- deterministic detector and policy output own final security decisions
- RAG/LLM output is advisory and explanation-only
- RAG/LLM is not a detection source
- LLM output must not override Risk Level or Decision
- BLOCK, MONITOR, and ALLOW remain simulated decisions
- no real firewall, WAF, SIEM, SOAR, cloud, or endpoint action is performed

## 2. Test Categories

| Category | Purpose | Examples |
|---|---|---|
| Unit tests | Validate pure functions, Pydantic models, enum contracts, and deterministic helpers. | Rule models, incident types, RAG helper types, tool policy, workflow types. |
| Integration-style unit tests | Exercise local deterministic flows without external services. | Detection flow, log ingestion flow, controller dispatch, report follow-up behavior. |
| Eval dataset tests | Validate that JSONL eval datasets load and keep expected structure. | `eval_cases/*`, `tests/test_eval_cases.py`. |
| Eval runner tests | Validate deterministic eval runner summaries and smoke behavior. | `tests/test_eval_runner.py`. |
| Import guard tests | Prove helper or contract modules do not import heavy runtime dependencies. | Subprocess import guards for `app`, `rag_qa`, Chroma, Ollama, LangChain, Torch, or local LLM clients. |
| Release gate tests | Confirm the repository is ready for release or phase handoff. | `pytest`, `ruff`, `mypy`, `gitleaks`, `git diff --check`. |
| Manual LLM/RAG smoke tests | Manually verify local Ollama, Chroma, Mode 3 RAG QA, and LLM assist behavior. | Not part of normal CI. |

## 3. Current Quality Gate

Expected release gate commands:

```powershell
python -m pytest
python -m ruff check .
python -m mypy app.py modules tests
gitleaks detect --source . --verbose --redact
git diff --check
```

The current expected full pytest result is `525 passed`, or the latest actual count from the current branch if additional tests are added later.

On Windows, a `tmp_path` or pytest temp directory `PermissionError` under the local temp directory can occur in this sandbox. Treat that as a local sandbox/temp permission issue, not an assertion failure. Under elevated execution or normal temp permissions, the tests are expected to pass.

## 4. Test Ownership Map

| Test file | Owner cluster | Notes |
|---|---|---|
| `tests/test_detector.py` | `detector_rules` | Deterministic detector behavior. |
| `tests/test_detection_rules.py` | `detector_rules` | Rule model and rule matching behavior. |
| `tests/test_rule_loader.py` | `detector_rules` | YAML rule loading behavior. |
| `tests/test_types.py` | `risk_decision` / `incident_evidence` | Shared incident, risk, decision, and simulated defense models. |
| `tests/test_golden_smoke.py` | `risk_decision` | End-to-end deterministic golden smoke expectations. |
| `tests/test_scenario_a_integration.py` | `risk_decision` / `detector_rules` | Local deterministic scenario integration. |
| `tests/test_log_pipeline.py` | `log_pipeline` | Log parser, normalizer, and aggregator behavior. |
| `tests/test_log_ingestion_runner.py` | `log_pipeline` | Log ingestion runner behavior and import safety. |
| `tests/test_incident_types.py` | `incident_evidence` | Incident model behavior. |
| `tests/test_evidence_correlator.py` | `incident_evidence` | Evidence correlation behavior. |
| `tests/test_incident_exporter.py` | `incident_evidence` | Incident export behavior. |
| `tests/test_evidence_grounded_llm_assist.py` | `incident_evidence` / `guardrails` | Evidence-grounded advisory output checks. |
| `tests/test_report_followup.py` | `report_followup` | Report-aware EV/F-ID and protected explanation behavior. |
| `tests/test_rag_types.py` | `rag_helpers` | RAG helper models and types. |
| `tests/test_rag_metadata.py` | `rag_helpers` | Metadata helper behavior and import guard coverage. |
| `tests/test_rag_intent.py` | `rag_helpers` | RAG intent classification helpers. |
| `tests/test_rag_retrieval_planner.py` | `rag_helpers` | Retrieval planning helper behavior. |
| `tests/test_rag_source_assembly.py` | `rag_helpers` | Source assembly and citation helper behavior. |
| `tests/test_rag_explainers.py` | `rag_helpers` | Report and rule explanation helpers. |
| `tests/test_answer_guardrails.py` | `guardrails` | Answer safety checks and import guard coverage. |
| `tests/test_llm_guardrails.py` | `guardrails` | LLM advisory guardrail behavior. |
| `tests/test_eval_cases.py` | `eval` | Eval dataset loading and validation. |
| `tests/test_eval_runner.py` | `eval` | Deterministic eval runner behavior. |
| `tests/test_smart_router.py` | `router` | Smart Router preview and route classification behavior. |
| `tests/test_controller_agent.py` | `controller_tools` | ControllerAgent dispatch contract. |
| `tests/test_controller_agent_integration.py` | `controller_tools` | Local controller integration behavior. |
| `tests/test_controller_types.py` | `controller_tools` | Controller type contracts. |
| `tests/test_skill_catalog.py` | `controller_tools` | Skill catalog behavior. |
| `tests/test_skill_wrappers.py` | `controller_tools` | Skill wrapper behavior and import guard coverage. |
| `tests/test_tool_registry.py` | `controller_tools` | Tool registry behavior. |
| `tests/test_tool_policy.py` | `orchestration_contracts` | Tool Permission Contract schema and policy defaults. |
| `tests/test_workflow_types.py` | `orchestration_contracts` | Workflow Plan Contract schema and preview plan behavior. |
| `tests/test_analyst_suggestions.py` | `analyst_ux` | Deterministic analyst suggestion helpers. |

## 5. Import Guard Strategy

Import guard tests prove that helper, eval, and contract modules can be imported without starting heavy runtime paths.

Preferred pattern:

- run import checks in an isolated subprocess
- assert the target helper imports successfully
- assert forbidden runtime modules are absent from that subprocess

Avoid relying on global `sys.modules` assertions in the shared pytest process unless the test provides explicit isolation. A shared import guard helper may be useful later, but this phase does not implement it.

Forbidden heavy runtime imports for unit-level helper tests commonly include:

- `app`
- `modules.rag_qa`
- Chroma
- Ollama or ChatOllama
- LangChain runtime clients
- Torch
- embedding model startup paths

## 6. Manual LLM/RAG Smoke Strategy

Manual LLM/RAG smoke tests depend on local services and machine state, including Ollama, Chroma, embedding models, and local environment configuration. They should not run in normal CI.

Suggested manual checks:

```powershell
ollama list
docker ps
```

Then run the application manually outside normal CI and verify Mode 3 RAG QA with a basic question such as:

```text
What is SQL Injection?
```

Manual review should confirm:

- the answer does not claim RAG/LLM is a detection source
- the answer does not override detector Risk Level or Decision
- the answer does not claim real blocking or real enforcement occurred
- advisory language remains explanation-only
- any BLOCK, MONITOR, or ALLOW wording remains simulated

## 7. Known Test Debt

Deferred cleanup items:

- create a shared subprocess import guard helper if repeated patterns keep growing
- split `tests/test_report_followup.py` if protected report follow-up coverage becomes too large
- make eval dataset validation and eval runner behavior more explicitly layered
- consider a local-only manual LLM/RAG checklist for machine-specific checks
- if future package migration happens, reorganize tests by owner cluster only after ownership is stable

## 8. Non-Goals

This document does not:

- modify tests
- modify production code
- move test files
- add test helpers
- change pytest configuration
- change `pyproject.toml`
- add CI jobs
- add LLM integration tests to normal CI
- initialize Ollama, Chroma, embeddings, Torch, ChatOllama, or local LLM clients

## 9. Follow-up Actions

- Phase 9A-6: Optional Package Migration Plan
- Future: standalone local-only manual LLM/RAG smoke checklist
- Future: shared subprocess import guard helper
- Future: test layout cleanup after ownership and package boundaries are stable
