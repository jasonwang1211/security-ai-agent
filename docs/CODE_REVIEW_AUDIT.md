# Code Review Audit

## Purpose

This audit summarizes the current architecture health of Sentinel Project after the v2.8 demo-ready work. It is a review document only; it does not change runtime behavior.

## Overall Assessment

The project has a clear safety architecture: deterministic detection, deterministic Risk Level / Decision, and advisory AI/RAG/UI layers. The most important engineering strength is that authority boundaries are represented in code, UI copy, tests, and documentation.

The main maintenance pressure is documentation and UI surface growth. Streamlit panels, HTML snippets, i18n labels, and report-section helpers now carry a lot of presentation logic. Future cleanup should reduce duplication without touching detector, risk, decision, or safety-sensitive retrieval behavior.

## Architecture Map

| Area | Representative files | Review note |
|---|---|---|
| CLI entry | `app.py` | Should remain lightweight and avoid eager RAG imports. |
| Streamlit console | `ui/streamlit_app.py` | Main integration surface; useful but large. |
| UI helpers | `modules/ui/*` | Keeps parsing/rendering testable without importing Streamlit. |
| Controller/orchestrator | `modules/controller/*` | Deterministic routing and ToolPolicy boundaries should remain narrow. |
| Detection | detector and rule-loading modules | Authority path; do not casually refactor. |
| Risk/decision | triage policy and responder modules | Authority path; must stay deterministic. |
| RAG / Knowledge Q&A | RAG helpers and lazy loader | Advisory only; lazy loading protects startup. |
| AI advisory | `modules/ai_advisory/*`, UI panels | Deterministic advisory summaries; no final verdict authority. |
| Output language policy | `modules/output_language.py` | Pure language profile helper; should stay lightweight. |
| Similar cases | approved seed retrieval modules | Read-only, approved seed corpus only. |
| Graph | `modules/graph/*` | Explanatory graph context, not graph-based detection. |
| Case draft/export | draft and export helpers | Human review boundary must remain visible. |

## Safety Boundary Confirmed

- Rule-Based Detector is the detection authority.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated.
- RAG, LLM, AI Analyst Brief, and Evidence Gap provide advisory context only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, proof-of-concept, or traffic generation is provided.
- Human review is required.

## Maintainability Risks

- Repeated safety-boundary wording across UI panels and docs.
- i18n dictionary growth without feature grouping.
- Streamlit tab rendering and repeated card/list HTML blocks.
- Demo/report documentation accumulating release-history language.
- RAG and graph helper boundaries becoming harder to reason about if future features are added too broadly.

## Recommended Refactor Plan

1. Keep startup import tests close to the Lazy RAG boundary.
2. Extract small pure helpers for repeated UI card/list rendering data preparation.
3. Group translation keys by panel or feature.
4. Keep public docs separated from historical release notes and local presentation materials.
5. Preserve safety-sensitive modules unless a change is explicitly scoped and well-tested.

## Audit Conclusion

The architecture is suitable for the current demo and review stage. Future engineering improvements should focus on documentation structure, UI helper deduplication, and import discipline rather than changing detection authority or safety policy.
