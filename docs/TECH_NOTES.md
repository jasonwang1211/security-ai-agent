# Technical Notes

Current baseline: v2.8 demo-ready.

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

The current public validation summary is maintained in `docs/TEST_REPORT.md` and the v2.8 release gate evidence is maintained in `docs/v2.8_release_gate.md`.
