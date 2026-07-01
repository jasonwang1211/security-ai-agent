# v3.8 Live Provider / RAG Health Audit

## 1. Current Branch / HEAD / Status

- Repository: `C:\Users\jason\Desktop\sentinel_project`
- Branch inspected: `v3.7-post-final-runtime-truth`
- HEAD inspected: `f50e68f docs: record v3.7 manual streamlit smoke result`
- Working tree before this report: clean.
- Remote state from `git branch -vv`: branch tracks `origin/v3.7-post-final-runtime-truth` with no ahead/behind marker, so it appears pushed and aligned with origin. No push was performed during this audit.

Recent commits at audit start:

```text
f50e68f docs: record v3.7 manual streamlit smoke result
98fc2d5 docs: finalize v3.7 runtime and integration notes
b2f8370 docs: summarize v3.7 knowledge capture stack import
f96794c docs: add v3.6 review and UI smoke notes
c5fae43 test: add knowledge capture review UI safety tests
f4fcb32 feat: add knowledge capture review UI prototype
2597d00 docs: add v3.6 knowledge capture review UI plan
9bda780 docs: add knowledge capture demo artifacts and review notes
a7ac8a4 test: harden knowledge capture approval and export safety
adc4757 test: add knowledge capture safety regressions
```

## 2. Current Runtime Architecture Summary

The project is mixed-runtime:

- deterministic detection / official verdict path remains the authority;
- Full AI-Assisted Advisory Result and Event-Aware Q&A can run through provider-disabled deterministic fallback;
- optional provider contracts can call local or OpenAI-compatible providers when explicitly configured;
- RAG / Knowledge Q&A depends on local RAG runtime readiness for true knowledge answers;
- natural/contextual follow-up may enter the RAG follow-up path.

Configured components from `config.py`:

| Setting | Value |
|---|---|
| `MODEL_NAME` | `qwen2.5:7b` |
| `AGENT_MODEL_NAME` | `gemma4:e4b` |
| `CHROMA_PATH` | `./chroma_db` |
| `EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `TOP_K` | `5` |

## 3. Provider-Disabled Fallback Paths

### Full AI-Assisted Advisory Result

Evidence:

- `modules/ai_advisory/llm_provider.py` defines `DEFAULT_PROVIDER_MODE = "disabled"` and reads `SENTINEL_AI_PROVIDER_MODE`.
- `normalize_provider_mode(...)` only accepts `local` and `openai_compatible` from env; `fake` is not enabled from normal env runtime.
- `build_default_provider(...)` returns a disabled provider unless env explicitly requests a supported live provider mode.
- `modules/ai_advisory/full_ai_assisted.py::run_full_ai_assisted(...)` builds the default provider, calls `selected_provider.generate(...)`, and falls back to deterministic grounded brief results for disabled, unavailable, invalid JSON, guardrail-blocked, or provider-exception cases.
- `modules/ui/full_ai_assisted_view.py` renders `provider_mode`, `provider_status`, `llm_status`, and `guardrail_status` chips.

Current visible status exists at panel level, but there is no separate health probe explaining why a provider is disabled/unavailable or whether a model/server is reachable.

### Event-Aware Q&A

Evidence:

- `modules/ai_advisory/event_qa.py::answer_event_aware_question(...)` refuses unsafe questions before provider selection/call.
- Safe questions use `build_default_provider(...)` and can return deterministic fallback under disabled provider mode.
- The UI helper `modules/ui/event_qa_view.py` renders `provider_mode`, `provider_status`, and `llm_status`.

Current visible status is per-answer only. There is no global UI runtime health summary.

## 4. Live Provider Paths

### v3.1 Provider Contracts

- `modules/ai_advisory/llm_provider.py::LocalLLMProvider.generate(...)` lazily imports `langchain_community.chat_models.ChatOllama` inside the call path and invokes it with the configured model name.
- `modules/ai_advisory/llm_provider.py::OpenAICompatibleProvider` uses stdlib HTTP and requires endpoint/model/key configuration.
- `build_default_provider(...)` uses `AGENT_MODEL_NAME` as the default local model via `_default_local_model_name()`, so the local provider path points to `gemma4:e4b` unless env overrides it.

Live provider behavior is optional and should remain manual-smoke gated. v3.8 should not make provider availability a requirement for CI or Streamlit startup.

### Legacy LLMAssist Path

- `modules/llm_assist.py` imports `AGENT_MODEL_NAME` and lazily initializes `ChatOllama(model=AGENT_MODEL_NAME, temperature=0)` in `_initialize_llm()`.
- `LLMAssist.__init__()` sets up prompts/state but does not initialize ChatOllama immediately.
- `LLMAssist` returns fallback metadata such as `llm_status = "FALLBACK"` when it cannot use the local model path.

## 5. RAG / Knowledge Q&A Paths

### Lazy RAG Wrapper

- `modules/lazy_rag.py::LazyRAGQA` defers importing and constructing `RAGQA` until `_get_instance()` is called.
- `app.py` and `ui/streamlit_app.py` construct `LazyRAGQA()` during runtime setup, but that alone should not initialize Chroma, embeddings, or ChatOllama.

### RAGQA Runtime Initialization

- `modules/rag_qa.py::RAGQA.__init__()` records runtime state and sets `_components_initialized = False`.
- `_ensure_initialized()` triggers component initialization only when RAG methods need it.
- `_initialize_components()` imports and constructs:
  - `HuggingFaceEmbeddings(model_name=EMBED_MODEL)`;
  - `ChatOllama(model=MODEL_NAME, temperature=0)`;
  - `Chroma(persist_directory=CHROMA_PATH, embedding_function=self.embeddings)`.
- `RAGQA.is_ready()` currently calls `_ensure_initialized()`, so a naive health check using `is_ready()` would initialize heavy dependencies. v3.8 should avoid using `is_ready()` for default passive health display.
- `RAGQA.handle_natural_followup(...)` and answer-generation paths call `_ensure_initialized()` and can enter live RAG/LLM behavior.

### RAG Query Planner

- `modules/rag_query_planner.py::RAGQueryPlanner` defaults to `MODEL_NAME` and can lazily initialize `ChatOllama(model=self.model_name, temperature=0)` through `_get_llm()`.

## 6. Follow-up / ?? Paths

Follow-up remains mixed:

- `modules/agent.py::_handle_followup(...)` can answer active event / incident follow-up through deterministic event/incident follow-up helpers.
- Natural follow-up and contextual follow-up call `self.rag_qa.handle_natural_followup(...)`, which may initialize RAG and use ChatOllama/Chroma/embeddings.
- `ui/streamlit_app.py::run_followup_question(...)` routes follow-up through the existing orchestrator path and records the response.

v3.8 health UI should make it clear that follow-up can be deterministic or RAG-backed depending on question type and state.

## 7. Current UI Runtime Labels

Current UI exposes several local status chips or messages:

- `modules/ui/full_ai_assisted_view.py` renders `provider_mode`, `provider_status`, `llm_status`, `guardrail_status`, `human_review_required`, and `no_enforcement`.
- `modules/ui/event_qa_view.py` renders `provider_mode`, `provider_status`, `llm_status`, `human_review_required`, and `no_enforcement`.
- Evidence-Grounded and AI advisory panels render `llm_status` in their own contexts.
- Knowledge Q&A can show insufficient knowledge / unavailable-style response text, but it does not expose a structured health object for Ollama, model availability, Chroma, or embeddings.
- System/debug UI does not currently provide a consolidated runtime health summary.

## 8. Current Gaps / Ambiguity

| Question | Current answer |
|---|---|
| Can UI tell whether Ollama is reachable? | Not as a structured startup-safe health status. Provider/RAG failures may surface indirectly through answer/status output. |
| Can UI tell whether `qwen2.5:7b` exists? | No structured model availability probe. |
| Can UI tell whether `gemma4:e4b` exists? | No structured model availability probe. |
| Can UI tell whether Chroma path exists? | Not in the Streamlit UI health surface. RAGQA can detect missing path during initialization, but that initialization is heavy. |
| Can UI tell whether Chroma collection is usable? | Not without initializing RAG/Chroma. No lightweight read-only probe currently exists. |
| Can UI tell whether embeddings are available? | Not without entering RAG initialization/import paths. |
| Can UI tell whether RAG is lazy / initialized / unavailable? | `LazyRAGQA.initialized` exists, but it is not surfaced as a consolidated UI health summary. |
| Can UI tell whether fallback is available? | Full AI/Event-QA panels show fallback/provider status after rendering, but there is no standalone fallback health row. |

## 9. Proposed v3.8 Scope

v3.8 should add a safe, observable runtime health layer without changing detector, risk, decision, RAG answer semantics, graph behavior, or enforcement behavior.

Recommended scope:

1. Read-only health probe backend.
2. Pure UI renderer for health results.
3. Small Streamlit health panel, likely under System / Debug or an existing non-primary status area.
4. Focused tests proving no heavy imports on default health-probe import and safe behavior when services are unavailable.
5. Documentation update explaining that health checks are read-only and do not start services.

Out of scope for v3.8:

- starting Ollama;
- starting Chroma;
- downloading models;
- running embeddings by default;
- requiring live LLM/API/network in CI;
- changing RAG answer behavior;
- changing graph behavior;
- changing official detection/verdict authority;
- adding real enforcement.

## 10. Proposed New Files / Changed Files

Likely new files:

- `modules/runtime_health.py` or `modules/health/runtime_probe.py`
- `modules/ui/runtime_health_view.py`
- `tests/test_runtime_health.py`
- `tests/test_ui_runtime_health_view.py`
- `docs/V3_8_RUNTIME_HEALTH_PLAN.md` or implementation summary after work begins

Likely changed files:

- `ui/streamlit_app.py` for a small health panel under System / Debug.
- `modules/ui/i18n.py` for English / zh-TW health labels.
- `docs/TECH_NOTES.md` and `docs/RUNTIME_MODE_MATRIX.md` if implementation changes the visible health surface.

## 11. Proposed v3.8 Design

Prefer a read-only health probe module such as `modules/runtime_health.py`.

### Health Probe Rules

The health probe should:

- never download models;
- never auto-start Ollama;
- never auto-start Chroma;
- avoid initializing embeddings unless explicitly requested;
- use short timeouts;
- return structured status objects, not raise to callers for normal unavailable states;
- be safe for CI;
- be safe for Streamlit startup;
- not change detector, risk, decision, RAG answer, Graph, ToolPolicy, or case/knowledge behavior;
- not add real enforcement.

### Recommended Status Fields

| Field | Values |
|---|---|
| `provider_mode` | `disabled`, `live`, `unknown` |
| `ollama_server` | `not_checked`, `reachable`, `unreachable` |
| `primary_model` | `ready`, `missing`, `not_checked`, `unavailable` |
| `agent_model` | `ready`, `missing`, `not_checked`, `unavailable` |
| `chroma_path` | `exists`, `missing`, `not_checked` |
| `rag_runtime` | `lazy_not_initialized`, `ready`, `unavailable`, `not_checked` |
| `embeddings` | `configured`, `available`, `not_checked`, `unavailable` |
| `fallback` | `available`, `unavailable` |

### Suggested Data Contracts

Potential dataclasses or Pydantic models:

- `RuntimeHealthConfig`
- `RuntimeHealthResult`
- `OllamaHealth`
- `ModelHealth`
- `ChromaHealth`
- `RAGRuntimeHealth`
- `FallbackHealth`

### Probe Modes

- `passive`: default. Reads config/env/path state only. No network, no model calls, no Chroma initialization, no embeddings import.
- `local_status`: optional/manual. Short-timeout HTTP probe to local Ollama API and path checks. No model generation.
- `rag_light`: optional/manual. Chroma path/metadata checks only; no embeddings/model initialization unless explicitly requested later.

The default Streamlit display should use `passive` mode to avoid slow startup or accidental live-provider behavior.

## 12. Proposed Tests

Do not implement in this planning pass. Recommended tests:

- importing `modules.runtime_health` does not import `chromadb`, `langchain`, `sentence_transformers`, `ChatOllama`, or RAG runtime modules;
- provider-disabled path reports fallback available and does not require Ollama;
- missing Ollama returns `unreachable`, not crash;
- missing `qwen2.5:7b` returns model missing / unavailable, not crash;
- missing `gemma4:e4b` returns model missing / unavailable, not crash;
- missing Chroma path returns `missing`, not crash;
- passive health probe does not call `RAGQA.is_ready()` because that initializes RAG;
- UI can render a mocked health result;
- health UI labels are readable in English and zh-TW;
- no detector/risk/decision changes;
- no real enforcement text/action appears;
- CI does not require live LLM, Chroma, embeddings, model files, or network.

## 13. Risks And Do-Not-Change List

Risks:

- A naive health check could accidentally initialize RAG by calling `RAGQA.is_ready()`.
- A naive Ollama check could auto-start local services if it shells out to `ollama` CLI. Prefer short-timeout HTTP status checks only when explicitly requested, and never run `ollama ps` automatically in passive mode.
- A model availability check could be mistaken for proof that live generation quality is validated. Health only means availability, not answer quality.
- Streamlit health UI could slow startup if it performs network or heavy imports by default.

Do not change:

- Rule-Based Detector authority;
- Risk Level / Decision semantics;
- simulated BLOCK / MONITOR / ALLOW behavior;
- RAG retrieval / answer semantics;
- graph runtime behavior;
- ToolPolicy enforcement;
- Knowledge Capture approval / export safety behavior;
- case draft write behavior;
- final presentation package;
- any real firewall, WAF, EDR, account, cloud, SIEM, or SOAR state.

## 14. Recommended First Implementation Milestones

1. `v3.8-A`: passive health probe schema and config/path/env checks.
2. `v3.8-B`: optional short-timeout Ollama HTTP readiness probe, off by default in Streamlit startup.
3. `v3.8-C`: pure UI renderer and System / Debug panel integration.
4. `v3.8-D`: mocked tests for unavailable/missing/ready statuses and heavy-import regression.
5. `v3.8-E`: manual smoke checklist for live local provider / RAG readiness.

## 15. Audit Constraints Observed

- No Ollama process was started.
- No Chroma server was started.
- No model download was triggered.
- No embeddings were initialized.
- No RAG runtime was initialized by this audit.
- No runtime behavior was changed.
- No push/tag/release/merge/rebase/reset was performed.
- Final presentation package was not touched.
