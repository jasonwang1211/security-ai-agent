# Roadmap

## Current Baseline: v2.9.0 (internal stable milestone)

Sentinel Project currently includes a Streamlit analyst console, deterministic detection authority, advisory AI/RAG context, the v2.9 Evidence-Grounded AI Brief (advisory-only, deterministic fallback, with structured Similar Cases / Graph context), bilingual public documentation, and English / Traditional Chinese screenshot sets.

## Short-Term Polish

- Documentation architecture and public navigation cleanup.
- GitHub release packaging and release-note polish.
- Repository About, topics, and public-facing metadata.
- Public review and demo readiness checks.
- Continued screenshot and documentation consistency checks.

## v2.9: Evidence-Grounded AI Brief (completed, merged, tagged v2.9.0)

Merged into `main` and tagged `v2.9.0` as an internal stable milestone (no GitHub
Release). Release-gate evidence: `docs/v2.9_release_gate.md`; release notes:
`docs/v2.9_release_notes.md`.

Completed:

- M1 — Evidence-Grounded AI Brief MVP (deterministic bundle + structured brief with deterministic fallback; advisory-only; existing panels preserved).
- M2 — Guardrail hardening before any live LLM (synonym-aware blocked language, defensive-negation allowance, official-verdict immutability).
- M3/M4 — Structured Similar Cases / Graph context wired into the brief and Markdown export (`case-*` / `graph-*` citations), advisory-only and without re-triggering retrieval or parsing display text.
- RC1/RC2 — Release gate, release notes, and Evidence-Grounded AI Brief panel screenshots.

## v3.0: Final Polish (in progress)

Presentation and documentation polish on top of v2.9.0; no new major features. See
`docs/v3.0_final_polish_plan.md`.

- README / REPORT / docs sync to the v2.9 baseline (done).
- Final demo path confirmation in the UI walkthrough.
- v3.0 full-window screenshots (deferred until UI/docs freeze; see the plan + screenshot gallery TODO).
- Live-provider presentation remains manual-smoke gated. The public showcase defaults to provider-disabled fallback, while optional provider contracts and RAG / Knowledge Q&A have separate runtime-readiness requirements.


## v3.2: Full AI-Assisted Showcase UI Wiring (development branch)

The `v3.2-full-ai-assisted-showcase` branch wires the v3.1 backend contracts into the existing AI Analyst tab without changing detector authority or adding live-provider requirements. The public path remains deterministic fallback by default; screenshots and README showcase refresh are deferred until the UI is manually reviewed.

Completed in this branch:

- Full AI-Assisted Advisory Result panel over the current EvidenceGroundingBundle.
- Event-Aware Q&A panel over the active deterministic context.
- State clearing for stale Event-aware Q&A output when the active analysis changes.
- Focused tests for advisory boundaries, fallback behavior, optional RAG / Similar Cases / Graph context, and lazy startup.

## Long-Term Ideas

- Analyst Timeline / Event Replay for clearer investigation storytelling.
- More defensive synthetic scenarios.
- Improved report export formatting.
- Approved case review workflow.
- Read-only graph / case memory improvements.
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
