# Sentinel Project Report

## Abstract

Sentinel Project is an AI-assisted blue-team security triage prototype. It separates deterministic security decisions from advisory AI/RAG components inside a SOC-style workflow, so supported scenarios can be reviewed, tested, and explained without giving AI final authority.

The system uses a Rule-Based Detector and deterministic policy logic to classify supported security inputs, assign Risk Level, and produce simulated BLOCK / MONITOR / ALLOW decisions. AI/RAG features such as AI Analyst Brief, Evidence Gap Analyzer, Knowledge Q&A, Similar Cases, and Relationship Graph provide analyst context only. They do not override the current event's Risk Level or Decision.

## Problem Statement

Security triage requires speed, consistency, and clear evidence. AI tools can help summarize findings and surface context, but they become unsafe if they are treated as final detection authority or allowed to trigger real operational action.

The project addresses this problem by separating deterministic security authority from AI advisory support. The analyst-facing UI makes that boundary visible during review: the verdict path stays deterministic, while AI/RAG panels explain context and gaps.

## Motivation

Many AI security demos blur the line between explanation and authority. A model may produce fluent text that sounds confident even when evidence is incomplete. In security operations, this can lead to false confidence, premature escalation, or unsafe remediation claims.

Sentinel Project intentionally keeps the final triage path small, reproducible, and auditable. AI is used where it is strongest for a demo: summarization, explanation, evidence-gap framing, defensive knowledge retrieval, and report assistance.

## Requirements / Scope

The current prototype includes:

- deterministic classification for supported payload and incident scenarios;
- deterministic Risk Level and Decision logic;
- simulated response decisions only;
- advisory AI/RAG context for analysts;
- safe synthetic demo scenarios;
- documentation and screenshots suitable for public GitHub review.

Out of scope:

- production IDS/IPS enforcement;
- real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action;
- exploit code, PoC generation, traffic generation, or offensive automation;
- AI-controlled final verdicts.

## Design Principles

1. Keep security authority deterministic and reviewable.
2. Use AI for summaries, retrieval context, and evidence framing without granting unsafe authority.
3. Keep demo scenarios defensive and synthetic.
4. Separate active event facts from historical or advisory context.
5. Require human review before any operational use outside the demo.

## Why Rule-Based Detection Remains Authoritative

The Rule-Based Detector provides reproducible behavior for the supported demo scenarios. Its outputs can be tested, reviewed, and explained through rule IDs and matched evidence. This makes the authority path suitable for a controlled educational demo.

LLM output is intentionally excluded from final attack classification because generative models can hallucinate, overgeneralize, or infer facts that are not present in the input.

## Why AI Is Advisory Only

AI/RAG components help the analyst understand and investigate the deterministic result. They may explain what happened, identify missing evidence, propose review steps, answer defensive questions, or compare approved cases. They must not change the current Risk Level, Decision, live detection facts, graph facts, knowledge corpus, or operational state.

This advisory-only design preserves the safety boundary while still demonstrating practical AI-assisted workflow value.

## Why BLOCK / MONITOR / ALLOW Are Simulated

BLOCK / MONITOR / ALLOW labels communicate a possible triage decision inside the project. They are simulated decisions only. The project does not perform real blocking, monitoring deployment, account action, cloud policy change, SIEM action, SOAR playbook execution, or remediation.

The labels are useful for showing how a blue-team triage workflow can be structured, but they are not proof of real enforcement.

## System Architecture

~~~text
User input / demo scenario
  -> Streamlit analyst console or CLI
  -> Rule-Based Detector
  -> Attack / incident classification
  -> Deterministic Risk Level
  -> Simulated Decision
  -> Advisory context
     -> Evidence-Grounded AI Brief (cited, structured, deterministic fallback)
     -> AI Analyst Brief
     -> Evidence Gap Analyzer
     -> Knowledge Q&A / RAG
     -> Approved Similar Cases
     -> Relationship Graph
  -> Human-reviewed Case Draft / Markdown Export
~~~

The authority path ends at deterministic classification, Risk Level, and simulated Decision. Advisory layers can explain, compare, and document, but they cannot override the authority path.

## Core Modules

| Module area | Responsibility | Safety boundary |
|---|---|---|
| Rule-Based Detector | Classifies supported payload and incident patterns. | Detection authority. |
| Risk / Decision policy | Computes deterministic Risk Level and simulated Decision. | Final demo verdict path. |
| Controller / orchestration | Routes explicit commands and deterministic skill flows. | Does not use LLM routing as authority. |
| AI advisory | Builds AI Analyst Brief and Evidence Gap summaries. | Advisory only; no LLM authority. |
| Evidence-Grounded AI Brief | Builds a cited, structured brief over deterministic evidence, gaps, and optional similar-case / graph context, with a deterministic fallback and guardrail. | Advisory only; copies the official verdict and never overrides it. |
| RAG / Knowledge Q&A | Retrieves approved defensive knowledge context. | Advisory only; no exploit guidance. |
| Approved Similar Cases | Loads curated approved seed cases for comparison. | Historical cases do not prove current compromise. |
| Relationship Graph | Displays read-only relationship context. | Explanatory only; not graph-based detection. |
| Case Draft / Export | Produces reviewable report material. | Human review required. |

## Streamlit Analyst Console

The Streamlit console is the primary demo surface. It provides scenario loading, mode selection, active context display, deterministic output, AI advisory panels, case intelligence, graph context, and report export.

For launch and troubleshooting details, use [docs/USER_OPERATION_GUIDE.md](docs/USER_OPERATION_GUIDE.md). For a step-by-step demo path, use [docs/UI_WALKTHROUGH.md](docs/UI_WALKTHROUGH.md).

## Demonstration Scenarios

| Scenario | Input type | Expected classification | Risk Level | Simulated Decision | Demonstrates |
|---|---|---|---|---|---|
| Command Injection demo | Payload text | Command Injection | HIGH | BLOCK | Deterministic payload detection, rule evidence, AI advisory panels, evidence gaps. |
| Authentication incident demo | Authentication log path or synthetic log | Possible Account Compromise | HIGH | MONITOR | Suspicious login sequence review without claiming confirmed compromise. |
| HTTP/2 Resource Exhaustion safe synthetic demo | Synthetic incident summary | HTTP/2 Resource Exhaustion Suspicion | MEDIUM | MONITOR | Defensive DoS/resource-exhaustion triage without traffic generation. |
| Optional Full AI-assisted mode | User-selected mode | Depends on input | Deterministic policy remains authoritative | Simulated only | Optional AI/RAG explanation while preserving boundaries. |

## Testing and Validation

Latest v3.1 branch validation rerun for this documentation patch:

- pytest: 1268 passed
- ruff: passed
- mypy: passed, no issues found in 180 source files
- git diff --check: passed
- Disallowed wording scan for vendor/trailer text: no matches

The test suite verifies bounded demo behavior, contract stability, fallback behavior, and safety-boundary regressions. It does not measure real-world detection accuracy, live SOC effectiveness, production traffic coverage, or real enforcement effectiveness.

### Validation Matrix

| Test category | Representative behavior verified | Safety / architecture boundary verified | Example modules or tests | Limitation / what this does not prove |
|---|---|---|---|---|
| Deterministic detection and triage policy | Supported payload/log/scenario inputs map to rule-based classification, deterministic Risk Level, and simulated Decision such as HIGH -> BLOCK, MEDIUM -> MONITOR, LOW -> ALLOW. | Rule-Based Detector remains detection authority; Risk Level / Decision remain deterministic. | `tests/test_detector.py`, `tests/test_detection_rules.py`, `tests/test_fast_analysis.py`, `tests/test_scenario_a_integration.py`, `tests/test_http2_resource_exhaustion_demo.py` | Does not prove production IDS/IPS accuracy or broad real-world attack coverage. |
| Evidence bundle and Evidence-Grounded AI Brief | EvidenceGroundingBundle preserves official verdict, rule IDs, evidence IDs, citation IDs, evidence gaps, and unsafe assumptions; brief output remains advisory. | Official Risk Level / Decision are copied from deterministic context and not regenerated by AI. | `modules/ai_advisory/evidence_bundle.py`, `modules/ai_advisory/grounded_brief.py`, `tests/test_ai_advisory_evidence_bundle.py`, `tests/test_ai_advisory_grounded_brief.py` | Does not prove that every possible analyst narrative is complete or sufficient for a real incident. |
| AI guardrails and safety boundary | Verdict tampering, Similar Cases-as-proof, Graph-as-detection-source, enforcement language, exploit / PoC / traffic generation / load testing are refused, blocked, or forced to fallback. | AI/RAG/Similar Cases/Graph remain advisory-only; no real enforcement or offensive automation is authorized. | `tests/test_ai_advisory_grounded_brief.py`, `tests/test_llm_guardrails.py`, `tests/test_answer_guardrails.py`, `tests/test_responder_llm_advisory_boundary.py` | Pattern-based guardrails reduce known unsafe phrasing but are not a complete security policy engine. |
| v3.1 Full AI-assisted foundation | Prompt contract, disabled default provider, fake test-injection provider, optional local/openai-compatible provider contracts, invalid JSON, missing citations, unsafe output, provider failure, and provider exceptions degrade safely. | CI requires no live LLM, API key, Ollama, Chroma, embeddings, or network access; provider output cannot overwrite official Risk / Decision. | `modules/ai_advisory/prompt_contract.py`, `modules/ai_advisory/llm_provider.py`, `modules/ai_advisory/full_ai_assisted.py`, `tests/test_ai_advisory_prompt_contract.py`, `tests/test_ai_advisory_llm_provider.py`, `tests/test_ai_advisory_full_ai_assisted.py` | Does not prove a live provider is available, configured, high quality, or safe without separate manual smoke testing. |
| Event-aware Q&A backend | Questions about the current incident use deterministic verdict, rule IDs, evidence IDs, evidence gaps, optional RAG context, Similar Cases, and Graph context; unsafe questions are refused before provider calls. | Similar Cases cannot prove compromise; Graph is not a detection source; real enforcement and verdict override requests are refused. | `modules/ai_advisory/event_qa.py`, `tests/test_ai_advisory_event_qa.py` | Does not provide a full conversational UI or guarantee answer quality from a live provider. |
| Similar Cases and Relationship Graph | Approved Similar Cases are loaded read-only and scored deterministically; Graph context is read-only explanatory context. | Historical cases do not prove current compromise; Graph context does not become detection authority. | `tests/test_approved_case_retrieval.py`, `tests/test_ai_advisory_similar_case_graph.py`, `tests/test_graph_builder.py`, `tests/test_graph_explainers.py`, `tests/test_ui_relationship_graph_view.py` | Does not prove a production-scale case memory or graph analytics system. |
| RAG / Knowledge Q&A controls | RAG routing, controlled retrieval, source assembly, answer safety framing, no-answer paths, and lazy startup expectations are covered. | RAG is optional and advisory; retrieval output does not modify official verdict or perform enforcement. | `tests/test_rag_qa_controlled_runtime.py`, `tests/test_rag_intent.py`, `tests/test_rag_controlled_retrieval.py`, `tests/test_rag_source_assembly.py`, `tests/test_lazy_rag_startup.py` | Does not prove live embedding quality, production index freshness, or full knowledge-base coverage. |
| UI helper / Streamlit smoke behavior | UI helper parsing, panels, layout sections, export view, route/policy view, and AppTest smoke flows including Run -> Find Similar Cases -> case-001 / graph-001 are covered. | UI paths preserve the deterministic/advisory split and avoid stale context regressions. | `tests/test_ui_report_sections.py`, `tests/test_ui_ai_advisory_view.py`, `tests/test_ui_evidence_grounded_brief_view.py`, `tests/test_ui_report_export_view.py`, `tests/test_ui_demo_scenarios.py` | Does not prove browser compatibility, production deployment readiness, or every manual demo path. |
| Documentation / release-gate consistency | Public docs, screenshot references, release-gate notes, validation wording, and safety-boundary language are kept consistent. | Review materials repeat the same authority boundary and limitations as the runtime architecture. | `docs/TEST_REPORT.md`, `docs/v2.9_release_gate.md`, `docs/screenshots/README.md`, documentation link checks where present | Does not replace human review of public-facing claims. |

Supporting materials:

- [Test report](docs/TEST_REPORT.md)
- [v2.9 release gate](docs/v2.9_release_gate.md) and [v2.9 release notes](docs/v2.9_release_notes.md)
- [Screenshot gallery](docs/screenshots/README.md)

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated decisions only.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph provide advisory context only.
- Historical approved cases do not prove current compromise or successful execution.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit code, PoC generation, traffic generation, or offensive automation is provided.
- Human review is required.

## Limitations and Non-Goals

Sentinel Project is not a production IDS/IPS, not a real blocking engine, not an exploit generator, not a red-team tool, and not an autonomous incident-response system. It does not replace SIEM, SOAR, EDR, vulnerability management, or incident response approval.

The demo supports a bounded set of scenarios. Its purpose is to demonstrate architecture, workflow, and safety boundaries, not broad threat coverage.

## Future Work

Future work should preserve the deterministic authority boundary while improving analyst usefulness:

- additional defensive synthetic scenarios;
- richer analyst timeline and event replay;
- read-only graph and approved-case memory improvements;
- report export polish;
- packaging and release polish for public review.

## Conclusion

Sentinel Project implements a practical pattern for AI-assisted security triage: deterministic detection and policy remain authoritative, while AI/RAG components provide advisory context for human analysts. The result is a reviewable workflow where AI reduces analyst reading effort without becoming the final judge or an autonomous enforcement mechanism.
