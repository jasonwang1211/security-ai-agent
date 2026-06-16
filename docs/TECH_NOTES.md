# Technical Notes

Current baseline: v2.9.0 (Evidence-Grounded AI Brief merged into main; internal stable milestone).

These notes summarize the current architecture at a public, implementation-oriented level. Historical implementation plans and older release notes are kept in `docs/archive/`.

## Detection and Decision Authority

Sentinel Project keeps detection authority deterministic. The Rule-Based Detector classifies supported inputs, maps structured evidence to attack categories, and feeds deterministic Risk Level and Decision logic. AI components do not override the current event classification, Risk Level, or Decision.

BLOCK, MONITOR, and ALLOW are simulated decisions for demonstration and analyst workflow purposes. The system does not perform real enforcement.

## Lazy RAG Startup

v2.8 separates fast deterministic startup from heavier retrieval dependencies. Fast deterministic mode should not initialize Chroma, embedding models, LangChain, Ollama, or other heavy RAG/LLM dependencies. Knowledge Q&A and full AI-assisted paths load retrieval support only when those features are used.

## Language-Aware Output Policy

Analyst-facing advisory output follows the selected UI language where supported. The policy is intended for presentation clarity only; it does not alter detection, risk scoring, decisions, or retrieval authority.

## AI Analyst Brief

The AI Analyst Brief provides deterministic advisory context over the current analysis. It summarizes what happened, why it matters, the deterministic verdict, evidence gaps, suggested next review steps, and unsafe assumptions. It is advisory-only and does not use LLM authority for final decisions.

## Evidence-Grounded AI Brief (v2.9)

The Evidence-Grounded AI Brief is the v2.9 evolution of the advisory analyst narrative, merged into `main` and tagged `v2.9.0`. A deterministic `EvidenceGroundingBundle` collects already-computed facts — the rule-based detection and official verdict, current evidence, evidence gaps, and optional RAG / approved similar-case / graph relationship context — with stable citation IDs (`ev-*`, `rule-*`, `gap-*`, `rag-*`, `case-*`, `graph-*`). A structured brief is then generated with a deterministic fallback.

- The official Risk Level and Decision are copied from the bundle and can never be regenerated or overridden by generated content; a guardrail forces a deterministic fallback if generated text changes the verdict, overclaims advisory context, or uses unsafe enforcement / offensive wording.
- Structured Similar Cases and Graph context are consumed as already-computed structured objects (no display-text parsing) and remain advisory only: similar cases are not proof of compromise, and graph context is not a detection source.
- No live LLM client is wired; the brief currently runs as a deterministic fallback, and the guardrail is a pre-LLM safety layer.

## Evidence Gap Analyzer

The Evidence Gap Analyzer lists missing or unconfirmed evidence that an analyst should review before making operational conclusions. It does not prove compromise, successful execution, or exploitation, and it does not override Risk Level or Decision.

## Knowledge Q&A / RAG

Knowledge Q&A provides defensive explanations from approved knowledge context. RAG output is advisory only and must not be treated as detection authority, exploitation proof, or operational enforcement.

## Approved Similar Cases

Approved Similar Cases retrieve manually curated, approved seed cases for comparison. Similarity reasons and differences are deterministic, and historical cases never override the current event's Risk Level or Decision.

## Relationship Graph

The Relationship Graph presents read-only analyst context around current events, approved cases, and related evidence. It is a visualization and investigation aid, not a source of final facts or enforcement action.

## Case Draft / Export

Case Draft and Markdown Export support human review workflows. Drafts and exports are not live knowledge updates, enforcement actions, or final incident records unless a human reviewer explicitly promotes them outside this demo boundary.

## HTTP/2 Resource Exhaustion Safe Synthetic Demo

The HTTP/2 Resource Exhaustion scenario is a safe synthetic incident summary. It is designed for defensive triage demonstration, does not generate network traffic, does not include exploit steps or proof-of-concept instructions, and requires human review.

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level and Decision are deterministic.
- BLOCK, MONITOR, and ALLOW are simulated.
- RAG, LLM, AI Analyst Brief, Evidence Gap Analyzer, Similar Cases, and Graph context are advisory only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, proof-of-concept, or traffic generation is produced.
- Human review is required.

## Validation Summary

The current public validation summary is maintained in `docs/TEST_REPORT.md`, and the latest release-gate evidence is in `docs/v2.9_release_gate.md` (with `docs/v2.8_release_gate.md` kept as the prior v2.8 record).
