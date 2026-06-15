# Roadmap

## Current Baseline: v2.8 Demo-Ready

Sentinel Project currently includes a Streamlit analyst console, deterministic detection authority, advisory AI/RAG context, bilingual public documentation, and English / Traditional Chinese screenshot sets.

## Short-Term Polish

- Documentation architecture and public navigation cleanup.
- GitHub release packaging and release-note polish.
- Repository About, topics, and public-facing metadata.
- Public review and demo readiness checks.
- Continued screenshot and documentation consistency checks.

## v2.9 Branch: Evidence-Grounded AI Brief

Work in progress on the `v2.9-evidence-grounded-ai-brief` branch (not yet merged,
tagged, or released). Release-gate evidence: `docs/v2.9_release_gate.md`.

Completed on the v2.9 branch:

- M1 — Evidence-Grounded AI Brief MVP (deterministic bundle + structured brief with deterministic fallback; advisory-only; existing panels preserved).
- M2 — Guardrail hardening before any live LLM (synonym-aware blocked language, defensive-negation allowance, official-verdict immutability).
- M3/M4 — Structured Similar Cases / Graph context wired into the brief and Markdown export (`case-*` / `graph-*` citations), advisory-only and without re-triggering retrieval or parsing display text.

Remaining for a v2.9 release candidate:

- Optional live LLM client integration (still not wired; deterministic fallback only).
- Release screenshots for the Evidence-Grounded AI Brief panel.
- Release documentation / release-note finalization.

Still-open / longer-term candidate ideas:

- Analyst Timeline / Event Replay for clearer investigation storytelling.
- More defensive synthetic scenarios.
- Improved report export formatting.
- Approved case review workflow.
- Read-only graph / case memory improvements.

## Long-Term Ideas

- More structured evidence schemas.
- Additional scenario packs.
- Optional report PDF export.
- Structured UI state replay for demos and review sessions.
- More mature packaging for public releases.

## Non-Goals

- No production IDS/IPS claim.
- No real enforcement.
- No exploit / PoC / traffic generation.
- No AI final verdict.
- No autonomous firewall, WAF, EDR, account, cloud, SIEM, or SOAR action.

## Safety Boundary

Future work must preserve the current authority split: Rule-Based Detector and deterministic policy own the verdict path; AI/RAG, Similar Cases, and Relationship Graph remain advisory context only.
