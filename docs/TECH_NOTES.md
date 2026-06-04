# Technical Notes

This document summarizes the main technical ideas behind the project. It is intended for project review, future maintenance, and study notes.

The project is defensive and academic. Final detection and decision logic remains deterministic. LLM and RAG features are used for explanation and advisory context, not as final authority.

## Rule-Based Detection

Rule-based detection uses explicit signatures or patterns to identify known suspicious inputs. Because the rules are written directly and evaluated predictably, this approach is deterministic and easier to test than probabilistic detection.

In this project, `modules/detector.py` supports rule-based detection for:

- XSS
- SQL Injection
- Path Traversal
- Command Injection

This is suitable for known payload patterns, such as common XSS tags, SQL Injection fragments, path traversal strings, and command injection operators. The main weakness is that rule-based detection may miss novel, heavily obfuscated, or previously unseen attack patterns.

## Detection-as-Code

Detection-as-Code means storing detection rules as structured files instead of hard-coding all signatures in Python. In v1.4, this project uses YAML rules under `detections/blue_team/`.

YAML rules are easier to review, update, test, and attach metadata to. This is still deterministic rule-based detection, not ML detection.

Project usage includes:

- `detections/blue_team/`
- `modules/detection_rules.py`
- `modules/rule_loader.py`
- `DetectionRule`

Rule metadata includes:

- `id`
- `title`
- `attack_type`
- `severity`
- `confidence`
- `patterns`
- MITRE techniques
- references

Hard-coded signatures remain as a conservative fallback so the detector keeps known behavior even if external rule loading is unavailable.

Example YAML rule:

```yaml
id: XSS-001
title: Basic XSS Script Indicators
attack_type: XSS
severity: MEDIUM
confidence: 0.8
patterns:
  - "<script>"
  - "alert("
match_mode: substring
case_sensitive: false
enabled: true
```

## ControllerAgent and Tool Registry

v1.5 adds typed agent infrastructure without making the system autonomous. `ToolSpec` defines each tool contract, including input model, output model, safety level, RAG/LLM flags, and allowed input kinds. `ToolRegistry` stores the allowed tools, while the Skill Catalog defines exactly six v1.5 wrapper skills:

- `payload_triage`
- `raw_log_translate`
- `log_file_ingest`
- `rag_security_qa`
- `report_followup`
- `incident_json_export`

Skill wrappers expose existing local capabilities as typed local tools. `ControllerAgent` validates input, calls the registered handler, validates output, and returns a `ControllerOutput`.

Dispatch is deterministic by explicit route or tool name. This is agent infrastructure, not autonomous LLM routing. Auto Route, Smart Router, and LLM-driven tool selection are deferred.

## YAML and Schema Validation

YAML is a human-readable data format. This project uses PyYAML to read YAML rule files, then uses Pydantic to validate that each rule has the required fields and valid values.

Schema validation prevents broken or incomplete rule files from silently entering the detector. For example:

- invalid severity values are rejected
- `confidence` must be between `0.0` and `1.0`
- `patterns` must not be empty
- disabled rules are ignored

This helps keep detection behavior predictable and testable.

Simplified Pydantic-style example, not the full production class:

```python
class DetectionRule(BaseModel):
    id: str
    attack_type: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: float
    patterns: list[str]
```

## Evidence and Incident Model

v1.3 introduced incident-style evidence handling. Evidence items use stable `EV-ID` references, findings use stable `F-ID` references, and incidents group evidence and findings into structured reportable objects.

Project models include:

- `EvidenceItem`
- `EvidenceBundle`
- `Finding`
- `Incident`
- `GenerationMetadata`

This matters because report follow-up can answer questions like "EV-003 是什麼意思？" and JSON Incident Report export becomes possible. Stable evidence references also help prevent ungrounded explanations because generated text can be checked against known evidence IDs.

Compact example:

```text
EV-003: success_after_failures
F-001: possible_account_compromise
Risk Level: HIGH
Decision: MONITOR
```

## Time-Window and Sequence Correlation

Single events may not be enough to determine suspicious behavior. Multiple related events within a time window can create stronger evidence.

In v1.3 Scenario A, the project detects repeated authentication failures followed by a successful login. This can produce a `possible_account_compromise` finding with `HIGH / MONITOR`.

This means the behavior is suspicious but not a confirmed compromise. Analyst review is still required before making operational conclusions.

Project module:

- `modules/evidence_correlator.py`

## LLM Guardrails

LLMs can hallucinate, so this project does not allow LLM output to make final decisions. `LLMAssist` is advisory only, and `LLMGuardrails` validates advisory output before it is trusted as context.

Guardrail checks include:

- evidence reference validation
- no downgrade of deterministic verdict
- no unilateral `BLOCK` authority
- allowed attack type validation
- confidence sanity checks
- fallback to deterministic result if unsafe

Project modules:

- `modules/llm_assist.py`
- `modules/llm_guardrails.py`

Why not let the LLM decide?

Because final security decisions must be reproducible, testable, and bounded by deterministic policy.

Pseudo-rule:

```text
If LLMAssist cites EV-999 but EV-999 does not exist in the EvidenceBundle,
LLMGuardrails rejects the advisory result and falls back to deterministic output.
```

## RAG and Report-aware Follow-up

RAG is used for explanation and security knowledge, not primary detection. Report-aware follow-up explains existing reports, evidence IDs, risk levels, and decisions. It must not re-judge the final verdict.

Project modules and knowledge paths include:

- `modules/rag_query_planner.py`
- `modules/rag_qa.py`
- `modules/report_followup.py`
- `knowledge/blue_team/report_explainer/`

Example follow-up questions:

- "EV-003 是什麼意思？"
- "為什麼是 MONITOR？"
- "我接下來要查什麼？"

## RAG v2 Foundation

v1.6 introduces metadata-aware and source-cited helper infrastructure for RAG v2. It does not replace the current `RAGQA` runtime and does not make RAG a detection source.

Key pieces:

- Frontmatter metadata makes knowledge docs easier to filter and cite.
- Exact ID extraction / lookup handles EV-ID, F-ID, INC-ID, rule ID, and MITRE technique ID references better than pure vector search.
- The metadata-aware retrieval planner selects candidate sources without running vector retrieval.
- `AnswerWithSources` carries answer text, `SourceCitation` entries, exact IDs, answer-support confidence, and limitations.
- Report Explainer v2 and Rule Explainer v2 are deterministic helper paths.

Safety boundary:

RAG v2 remains explanation-only. It cannot override final verdicts, risk levels, decisions, or deterministic policy-controlled output. `BLOCK`, `MONITOR`, and `ALLOW` remain simulated.

## v1.7 Reliability Foundation

v1.7 adds deterministic reliability infrastructure before any user-facing router activation.

- `eval_cases/` contains small regression datasets, not a statistical benchmark.
- AnswerGuardrails are deterministic safety checks for unsafe answer claims.
- The Evaluation Runner performs deterministic smoke checks over bundled cases.
- Smart Router is rule-based route selection only.
- Smart Router is not wired into the CLI yet and does not execute tools.
- There is no LLM routing and no LLM final verdict override.

The detailed v1.7 design lives in `docs/v1.7-spec.md`; these notes only summarize the technical role of the new foundation.

## v1.8 Protected Runtime Wiring and Analyst UX

v1.8 adds narrow protected helper paths without replacing the existing runtime.

- Protected report/rule helpers wrap source-cited helper output with AnswerGuardrails.
- Unsafe helper output returns conservative fallback wording with limitations.
- Smart Router preview calls the route decision helper only and does not execute tools.
- Analyst follow-up suggestions are deterministic templates.
- There is no LLM routing, tool execution, RAGQA replacement, or final verdict override.

The detailed v1.8 design lives in `docs/v1.8-spec.md`; these notes only summarize the technical role of the implemented helper layer.

## v1.9 Architecture Cleanup and Orchestration Contracts

v1.9 adds architecture cleanup documents and schema-only orchestration contracts. It is not a runtime automation milestone.

- `docs/v1.9-spec.md` is the detailed design source of truth.
- `docs/ARCHITECTURE_MAP.md` documents ownership boundaries.
- `docs/adr/` records the core architecture decisions.
- `modules/controller/tool_policy.py` defines a schema-only Tool Permission Contract.
- `modules/controller/workflow_types.py` defines a schema-only Workflow Plan Contract.
- `docs/TESTING_STRATEGY.md` documents the testing source of truth.
- `docs/PACKAGE_MIGRATION_PLAN.md` documents future package migration planning.
- RAG helper modules now live under `modules/rag/` with flat compatibility shims.
- Controller/orchestration modules now live under `modules/controller/` with flat compatibility shims.
- The manual LLM/RAG smoke checklist is documented as manual-only, not CI, and not executed.

Technical boundary:

- Tool Policy does not enforce runtime behavior.
- Workflow Plan does not execute tools.
- ControllerAgent does not auto-execute.
- Smart Router is not the default CLI auto-route.
- There is no LLM tool selection.
- At the v1.9 contract stage there was no Graph RAG, Knowledge Capture, or Agent Skill Orchestration runtime implementation; v2.4 later adds deterministic read/analysis skill orchestration only.
- `RAGQA` remains the active general knowledge QA runtime.
- LLM/RAG output does not decide attacks or override Risk Level / Decision.
- `BLOCK`, `MONITOR`, and `ALLOW` remain simulated decisions.
- No real firewall, WAF, SIEM, SOAR, cloud, or endpoint enforcement is performed.

## v2.0 Knowledge Graph Foundation

v2.0 adds a deterministic in-memory graph foundation. The graph organizes evidence and context; it is not a detector, policy engine, RAG runtime, or tool execution system.

Core graph types:

- `GraphNodeKind` and `GraphEdgeKind` define the allowed vocabulary.
- `GraphSourceRef` records where a node or edge came from.
- `GraphNode`, `GraphEdge`, and `GraphSnapshot` provide the Pydantic data contract.

The deterministic builder in `modules/graph/builder.py` creates `GraphSnapshot` objects from structured `Incident` data and explicitly provided `DetectionRule` objects. It does not load YAML, read files, inspect free text, guess relationships, call LLMs, call Chroma/Ollama/vector systems, execute tools, or change Risk Level / Decision. Every edge includes source/reason metadata.

The lookup helpers in `modules/graph/lookup.py` are read-only and edge-driven:

- `get_node`
- `get_neighbors`
- `get_edges_for_node`
- `find_nodes_by_kind`
- `get_related_findings`
- `get_related_rules`
- `get_incident_context`

`get_incident_context` returns a small deterministic lookup summary only. It does not assemble prompts, source-cited answers, vector context, RAG context, LLM messages, or analyst recommendations.

The export helpers in `modules/graph/exporter.py` serialize in-memory snapshots with `graph_snapshot_to_dict` and `graph_snapshot_to_json`. They do not add save/load helpers or file persistence.

v2.0 intentionally keeps Graph RAG retrieval, Knowledge Capture, LLM graph extraction, Neo4j, vector search, runtime agent orchestration, tool execution, and KnowledgeDoc graph seed deferred. The 2A-3 decision keeps explicit `DetectionRule` seed inside the builder and defers KnowledgeDoc graph seed until a metadata audit.

## v2.1 Graph-Backed Explanation MVP

`modules/graph/explainers.py` owns the first visible graph-backed explanation helper. Its public API is `explain_graph_reference(snapshot, reference_id) -> AnswerWithSources`.

The helper supports exact references only:

- `EV-*` follows explicit `SUPPORTED_BY` edges to findings.
- `F-*` follows explicit `SUPPORTED_BY`, `MAPS_TO_RULE`, and `RELATED_TO_ATTACK` edges.
- rule IDs such as `CMD-001` or `DETECTION_RULE:CMD-001` follow explicit `MAPS_TO_RULE` and `DETECTS` edges.
- `INC-*` summarizes explicit incident graph context.

Graph provenance reuses the existing RAG v2 answer contract. `SourceCitation.metadata` carries real graph node, edge, and `GraphSourceRef` provenance already present in the `GraphSnapshot`; no `AnswerWithSources` or `SourceCitation` schema expansion was needed. Outward-facing rule IDs are normalized to stable IDs such as `CMD-001`, while citation metadata keeps the real graph node and edge IDs.

`explain_graph_followup_protected(...)` in `modules/report_followup.py` calls the graph explainer and then runs the result through existing `AnswerGuardrails`. Known evidence, finding, and rule IDs are derived from the supplied `GraphSnapshot`, so protected graph answers stay bounded by actual graph contents.

Missing references return insufficient context without fabricated graph citations. Existing but disconnected graph nodes may be cited as existing nodes while the answer states that no explicit relationship was found.

Safety boundary:

This is graph-backed explanation, not Graph RAG retrieval. It does not call LLMs, Chroma/Ollama/vector systems, execute tools, write knowledge, replace `RAGQA`, change Risk Level / Decision, or perform real enforcement. `BLOCK`, `MONITOR`, and `ALLOW` remain simulated decisions, and deterministic detector / risk / decision remain final authority.

## v2.2 Curated RAG Graph Seed Foundation

v2.2 released as `v2.2.0`.

Batch 2.2-A promotes reviewed curated Traditional Chinese knowledge into the live report-explainer corpus while keeping the runtime contract narrow:

- 9 reviewed Traditional Chinese report-explainer KB documents were promoted into live `knowledge/blue_team/report_explainer/`.
- Live report-explainer coverage expanded from 11 to 20 documents.
- The typed RAG metadata model now supports only the v2.2-consumed fields: `title`, `review_status`, `finding_types`, `evidence_types`, `decision_labels`, and `tags`.
- Promoted documents use `schema_version: v2.2-live1` and `review_status: approved_for_runtime_promotion`.
- Five authentication documents remain retrieval/explanation context only and do not define graph-seed edges.
- Four verified rule explainers retain reviewed attack/rule metadata: XSS / `XSS-001` / `MEDIUM` / simulated `MONITOR`; SQL Injection / `SQLI-001` / `HIGH` / simulated `BLOCK`; Path Traversal / `PATH-001` / `HIGH` / simulated `BLOCK`; Command Injection / `CMD-001` / `HIGH` / simulated `BLOCK`.
- Resolved references were added before live promotion.

`modules/graph/knowledge_doc_seed.py` defines the v2.2 seed helper. Its public API is:

```python
build_knowledge_doc_seed(
    metadata_items: Sequence[KnowledgeDocMetadata],
    detection_rules: Sequence[DetectionRule],
) -> GraphSnapshot
```

The helper accepts already parsed metadata items and explicitly supplied `DetectionRule` objects. It does not load Markdown, parse YAML files, inspect prose, parse `graph_links`, call RAG, call LLMs, run vector search, ingest knowledge, or modify `modules/graph/builder.py`.

Graph-seed candidates require `review_status == "approved_for_runtime_promotion"`. Retrieval-only documents with empty `attack_types` and `rule_ids` produce empty seed output. Edges are emitted only when supplied detection rules confirm both the rule ID and the corresponding attack type.

The v2.2 seed vocabulary is deliberately small:

- `KNOWLEDGE_DOC -> ATTACK_TYPE` through `RELATED_TO_ATTACK`
- `KNOWLEDGE_DOC -> DETECTION_RULE` through `MAPS_TO_RULE`

Edge provenance comes from `frontmatter.attack_types` and `frontmatter.rule_ids`.

`combine_hybrid_explanation_protected(...)` in `modules/report_followup.py` combines already-built graph context and already-built curated knowledge context. It preserves both graph provenance and curated KB citations, then applies existing deterministic guardrails. It is assembly-only: it does not perform automatic retrieval, vector-to-graph expansion, intent classification, RAG calls, LLM calls, detector changes, Risk Level changes, or Decision changes.

Demonstrated coverage:

- Scenario A authentication hybrid explanation combines graph context for `EV-003` supporting `F-001` with curated authentication KB context. The generic KB answer has no fixed `EV-003` or `F-001` bindings, and `Decision` remains simulated `MONITOR`.
- Command Injection hybrid explanation uses the approved KnowledgeDoc seed to connect the command-injection explainer to `ATTACK_TYPE:Command Injection` and `DETECTION_RULE:CMD-001`. Graph provenance and curated KB citations coexist, and `Decision` remains simulated `BLOCK`.

Safety boundary:

Deterministic detector / risk / decision remain final authority. Graph and curated RAG context provide explanation/support only. `ALLOW`, `MONITOR`, and `BLOCK` remain simulated decisions. v2.2 does not implement automatic Graph RAG retrieval, vector-to-graph expansion, Knowledge Capture, LLM graph extraction, `RAGQA` replacement, CLI auto-route, real enforcement, or real monitoring deployment. Existing legacy KB documents remain supported, and full corpus schema migration is deferred.

## v2.3 Controlled Retrieval and Structured Follow-Up

v2.3 released as `v2.3.0`.

Mode 3 runtime:

- `RAGQA.answer_question(...)` first attempts controlled approved-source selection for reviewed targets including SQL Injection, `CMD-001`, and `success_after_failures`.
- If controlled selection has no match, the existing vector fallback remains available.
- Returned Mode 3 answers use the protected return path with Traditional Chinese safety boundary text, internal metadata-label suppression, canonical visible RAG / LLM terminology, and deterministic final-authority wording.
- RAG and LLM remain explanation-only and cannot override deterministic `Risk Level` or `Decision`.

Mode 1 event follow-up:

- Payload analysis stores an in-memory `ActiveEventContext` with facts from the current payload-analysis flow only.
- Mode 4 can answer current-event questions about classification reasoning, matched rule/signature evidence, simulated Decision boundary, uncertainty about successful exploitation, and defensive investigation or remediation guidance.
- Manual smoke verified `test; rm -rf /tmp/test` as Command Injection with `HIGH / BLOCK`, command-injection signatures, and simulation notice. Follow-up confirmed that simulated `BLOCK` is not real enforcement and that a rule match does not prove successful command execution.

Mode 2 authentication incident follow-up:

- Qualifying authentication logs use deterministic correlation to create structured `Incident`, `Evidence`, and `Finding` values.
- Scenario A stores `ActiveAuthIncidentContext` and builds an explicit in-memory `GraphSnapshot` from the current incident.
- Mode 2 visible output includes the structured incident summary with `INC-20260501-001`, `Possible Account Compromise`, `HIGH`, simulated `MONITOR`, `EV-003`, and `F-001`.
- Mode 4 can explain `EV-003`, the explicit `EV-003` / `F-001` support relationship, simulated `MONITOR`, compromise uncertainty, and investigation next steps.
- New non-qualifying Mode 2 log analysis clears stale structured context.

Safety boundary:

v2.3 uses graph-grounded follow-up only for the current structured authentication incident. It is not Similar-Case Graph RAG, not automatic historical-case retrieval, and not LLM-generated graph reasoning. It does not implement direct-input Auto Router, Agent Skill Orchestration, LLM-assisted skill selection, Knowledge Capture, event write-back, automatic vector-to-graph expansion, the deferred Mode 3 KnowledgeDoc graph-expansion WIP, real firewall/WAF/EDR/account action, or RAG/LLM override of deterministic `Risk Level` or `Decision`.

## v2.4 Deterministic Agent Skill Orchestration Runtime

v2.4 release gate passed; ready to tag. The current released baseline remains tag `v2.3.0` until the v2.4 tag, merge, and push are completed.

Runtime ownership:

- Direct user input is now the primary CLI path.
- The `menu` command preserves the legacy four-mode interface as a debug/demo fallback.
- The deterministic skill layer invokes `AnalyzePayloadSkill`, `AnalyzeAuthenticationLogSkill`, `ExplainActiveEventSkill`, `ExplainActiveIncidentSkill`, and `KnowledgeQASkill`.
- Skill selection is deterministic and rule-based; it is not LLM-selected.
- The skill layer wraps existing v2.3 runtime paths rather than redefining detector, incident, graph, or RAG authority.

Context behavior:

- Payload analysis can retain `ActiveEventContext` for current-event follow-up.
- Qualifying authentication log analysis can retain `ActiveAuthIncidentContext` and current-incident `GraphSnapshot` facts for graph-grounded follow-up.
- Structured current-event/current-incident follow-up takes precedence when applicable.
- General knowledge Q&A can run while structured context exists and does not overwrite that context.

Policy boundary:

- `ToolPolicy` permits approved read/analysis flows and keeps future write-capable behavior blocked or approval-required.
- v2.4 does not implement or release LLM-assisted skill selection, `RetrieveSimilarCaseSkill`, executable `DraftCaseCaptureSkill`, Similar-Case Graph RAG, historical-case retrieval, Knowledge Capture or event write-back, automatic live ingestion, real firewall/WAF/EDR/account enforcement, real monitoring deployment, or RAG/LLM override of deterministic `Risk Level` or `Decision`.
- Any future write-capable capture skill must require explicit approval and human review before live ingestion.

Focused validation:

- Pytest: `110 passed in 1.64s`
- Ruff: passed
- Mypy: passed across 108 source files
- `git diff --check`: passed
- Mojibake scan over v2.4-A touched files: no known corrupted fragments found
- Manual runtime smoke passed for direct payload input, direct authentication log input, active follow-up, protected SQL Injection knowledge Q&A, and legacy `menu` fallback.
## Testing Strategy

The project uses several testing layers:

- Unit tests: test individual models and functions
- Golden tests: protect known payload behavior from regression
- Integration tests: verify an end-to-end scenario such as Scenario A
- Lint and type checks: `ruff` and `mypy`

Last full quality gate:

- `python -m pytest` -> `693 passed in 14.72s` for v2.4
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed, `108 source files`
- `git diff --check` -> passed
- Gitleaks -> passed, no leaks found across 171 commits scanned using `gitleaks detect --source . --verbose --redact`

The full v2.4 release gate used a fresh writable pytest basetemp directory for local Windows temp-directory safety: `C:\Users\jason\Desktop\sentinel_pytest_runs\v2_4_gate_02389f227c3b468c9aca3b7b774e7190`.

Historical v2.3 full release gate remains recorded separately: `670 passed in 8.23s`, Ruff passed, Mypy passed across 106 source files, `git diff --check` passed, and Gitleaks found no leaks across 167 commits scanned.

Focused v2.2 validation already completed:

- Batch 2.2-A focused validation: `67 passed`, Ruff passed, Mypy passed, `git diff --check` passed
- Batch 2.2-B focused validation: `96 passed`, Ruff passed, Mypy passed, `git diff --check` passed

Deterministic tests do not require Ollama, Chroma, embeddings, Torch, ChatOllama, or app startup.

Compact examples:

```text
Golden payload test:
known XSS / SQLi / Path Traversal / Command Injection payloads should keep their expected behavior.

Scenario A integration test:
mixed auth log -> Incident -> EV-ID follow-up -> LLMAssist guardrails.
```

## MITRE ATT&CK Metadata

MITRE ATT&CK provides standard technique IDs. This project uses MITRE technique IDs as metadata in YAML rules so local rules can connect to broader security terminology.

Examples include:

- `T1059` for command/scripting-related behavior
- `T1190` for exploit public-facing application style references
- `T1083` for file/directory discovery style references

Mappings in this prototype are lightweight educational metadata, not a complete ATT&CK evaluation.

## What This Project Is Not

This project is:

- not a production SIEM
- not a SOAR system
- not a WAF
- not an offensive tool
- not an ML anomaly detector
- not an LLM-based final decision engine

It is a defensive, local-first academic prototype.

## Study Checklist

- YAML syntax
- PyYAML `safe_load`
- Pydantic validators
- rule-based detection
- Detection-as-Code
- false positive / false negative
- MITRE ATT&CK basics
- LLM hallucination and guardrails
- RAG basics
- unit / golden / integration testing
