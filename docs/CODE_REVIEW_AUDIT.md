# v2.8-D Code Review Audit

## Purpose

This audit records the current architecture health after the v2.7 AI advisory release and v2.8 lazy RAG startup work. It is a review document only; it does not change runtime behavior.

## Overall Assessment

The project has a clear safety architecture: deterministic detection, deterministic Risk Level / Decision, and advisory AI/RAG/UI layers. The most important engineering strength is that authority boundaries are represented in code, UI copy, tests, and documentation.

The main maintenance pressure is UI/documentation growth. Streamlit panels, HTML snippets, i18n labels, and report-section helpers now carry a lot of presentation logic. The next cleanup should reduce duplication without touching detector, risk, decision, or safety-sensitive retrieval behavior.

The v2.8-D Fix Pass adds a lightweight `modules/output_language.py` policy so UI language selection can influence advisory output and RAG prompt style without adding a controller Skill or initializing heavy RAG dependencies.

## Architecture Map

| Area | Representative files | Review note |
|---|---|---|
| CLI entry | `app.py` | Should remain lightweight and avoid eager RAG imports. |
| Streamlit console | `ui/streamlit_app.py` | Main integration surface; useful but becoming large. |
| UI helpers | `modules/ui/*` | Good direction: keeps parsing/rendering testable without importing Streamlit. |
| Controller/orchestrator | `modules/controller/*` | Deterministic routing and ToolPolicy boundaries should remain narrow. |
| Detection | `modules/detector.py`, rule loader/rules | Authority path; do not casually refactor. |
| Risk/decision | triage policy and responder modules | Authority path; must stay deterministic. |
| RAG / Knowledge Q&A | `modules/rag_qa.py`, `modules/lazy_rag.py`, RAG helpers | Advisory only; lazy loading improved startup discipline. |
| AI advisory | `modules/ai_advisory/*`, UI panels | Deterministic advisory summaries; no final verdict authority. |
| Output language policy | `modules/output_language.py` | Pure language profile helper; must stay free of UI, RAG, model, and vector imports. |
| Similar cases | approved seed retrieval modules | Read-only, approved seed corpus only. |
| Graph | `modules/graph/*` | Explanatory graph context, not graph-based detection. |
| Case draft/export | case draft and report export helpers | Human review boundary must remain visible. |

## Redundancy Suspects

The following areas are candidates for careful future cleanup:

- Streamlit tab rendering and repeated card/list HTML blocks.
- Repeated safety-boundary wording across UI panels and docs.
- i18n dictionary growth without grouping by feature.
- Test builders for active event/auth incident UI state.
- Similar card layouts across AI Analyst Brief, Evidence Gap, Similar Cases, and Case Draft views.
- Report/export/draft formatting helpers that share section labels and boundary text.

These are presentation and maintainability concerns, not correctness failures.

## Performance Suspects

The likely startup-cost sources are heavy ML/vector dependencies and their transitive imports:

- Chroma/vector store initialization.
- Embedding model loading.
- `sentence_transformers` / `torch` / NumPy / SciPy / ONNX Runtime chains.
- LangChain/Ollama client setup.
- Streamlit reruns touching modules that should stay lightweight.

v2.8-C already mitigates the highest-risk path by lazy-loading RAG initialization through `LazyRAGQA` and startup import regression tests.

## Already Improved

v2.8-C introduced lazy RAG startup discipline:

- Fast deterministic analysis no longer initializes RAG/LLM components.
- `app.py` and the UI can keep startup light.
- RAG is initialized only when Knowledge Q&A needs it.
- Lazy startup tests protect against accidental eager imports.

v2.8-D Fix Pass adds:

- Language-aware AI Analyst Brief and Evidence Gap output.
- Language-aware RAG prompt instructions and safety boundary wording.
- LazyRAGQA forwarding for optional language kwargs.
- Short HTTP/2 scenario card preview while preserving the full synthetic input for the main textarea.

## Safety-Sensitive Areas To Avoid During Casual Refactors

Avoid broad edits in these areas unless the change is explicitly scoped and well-tested:

- Rule-based detector and detection rule loading.
- Risk scoring and deterministic decision logic.
- RAG answer safety framing and CVE/CVSS terminology normalization.
- ToolPolicy and controller approval boundaries.
- Similar-case approved seed loading and no-override output boundary.
- Graph provenance helpers and graph explanation contracts.
- Case draft approval gate and promotion/draft writer behavior.
- Resource Exhaustion safe-demo wording that prevents traffic-generation or exploit framing.
- Output language helper purity; language switching must not initialize RAG, Chroma, embeddings, Torch, sentence-transformers, or ChatOllama.

## Recommended Refactor Plan

### P0: Preserve Startup Discipline

Keep import-weight tests close to the lazy RAG boundary. Any future feature that imports RAG, embeddings, LangChain, Ollama, or Chroma should prove it does not load those dependencies on the fast deterministic startup path.

### P1: UI Helper Deduplication

Extract small pure helpers for repeated card/list rendering data preparation. Keep Streamlit calls in `ui/streamlit_app.py`, but move parsing and section assembly into `modules/ui/*` where tests can cover them without importing Streamlit.

### P2: i18n Organization

Group translation keys by panel or feature. Add regression tests for mojibake markers and required bilingual labels when new UI panels are added.

### P3: Documentation Synchronization

Keep release notes, user guide, screenshot index, test report, and smoke checklist aligned after each feature batch. This matters because the project is demo-heavy and professor-facing.

## Professor-Facing Explanation

The codebase is intentionally conservative. It demonstrates modern AI-assisted analyst workflows, but every risky action is either simulated, read-only, or gated by human review. The AI layer is useful because it improves explanation and triage quality; it is safe because deterministic code still owns detection, Risk Level, and Decision.

## Audit Conclusion

The architecture is suitable for the current demo and review stage. The next engineering improvements should be lightweight refactors around UI duplication and import discipline, not changes to detection authority or safety policy.
