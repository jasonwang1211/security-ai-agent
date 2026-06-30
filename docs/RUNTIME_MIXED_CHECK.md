# Classroom Runtime LLM Fallback Check

Date/time: 2026-06-27 Asia/Taipei

Scope: emergency read-only runtime/code/test check for whether the current UI / AI-assisted paths require a live LLM or can succeed through provider-disabled deterministic fallback when Ollama is not running.

Important incident during check: `ollama ps` on this Windows machine is not a pure read-only status check when the Ollama app is not already running. It auto-started `ollama app.exe --hide --fast-startup` and `ollama.exe serve`. I stopped those processes afterward. Final post-check state: no Ollama process was listed and port 11434 had no listener.

## Executive Conclusion

Label: **MIXED**

- **Full AI-Assisted Advisory Result:** fallback-capable with provider disabled. It does not require live Ollama in the public/default UI path.
- **Event-Aware Q&A safe question:** fallback-capable with provider disabled. It calls the provider abstraction, receives disabled status, and returns a deterministic event-aware answer.
- **Event-Aware Q&A unsafe question:** refused before provider call. It does not require live Ollama.
- **Follow-up / 追問:** mixed. Active event/auth incident follow-up is deterministic first; natural/contextual follow-up can route into RAG follow-up helpers that may initialize RAG/ChatOllama and then degrade if unavailable.
- **RAG / Knowledge Q&A:** mixed/live-runtime-dependent for real knowledge answers. The UI forces the existing KnowledgeQASkill/RAG path; `SecurityAgent.build_rag_answer()` returns KB unavailable if `rag_qa.is_ready()` is false. `RAGQA` readiness requires vectorstore and ChatOllama over `MODEL_NAME`.

Safe classroom statement: do not say every AI/RAG feature works as a live LLM path without Ollama. Say the v3.2 Full AI-assisted showcase and Event-Aware Q&A can demonstrate deterministic fallback/guardrails, while Knowledge Q&A/RAG depends on the RAG runtime or shows an unavailable/no-context state.

## Step 1 - Ollama Runtime Check

Commands requested:

```powershell
Get-Process ollama -ErrorAction SilentlyContinue
netstat -ano | findstr :11434
ollama ps
```

Observed results:

- Initial `Get-Process ollama` output: no Ollama process listed.
- Initial `netstat -ano | findstr :11434` output: no port 11434 listener listed.
- `ollama ps` behavior: it printed Windows Ollama startup logs and auto-started Ollama:
  - `starting Ollama`
  - `starting ui server`
  - `starting ollama server`
  - process later observed as `ollama app.exe --hide --fast-startup` plus `ollama.exe serve`
- `ollama ps` model list output had only the table header:

```text
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
```

Interpretation:

- Before `ollama ps`, there was no visible Ollama process and no 11434 listener.
- `ollama ps` itself started Ollama on this Windows machine, so it cannot be treated as a passive check in classroom conditions.
- No loaded model was shown by `ollama ps`.
- I stopped `ollama app.exe` and `ollama.exe serve` after this accidental auto-start. Final check showed no remaining Ollama process and no 11434 listener.

## Step 2 - Code Path Inspection

### Model configuration

File: `config.py`

```python
MODEL_NAME = "qwen2.5:7b"
AGENT_MODEL_NAME = "gemma4:e4b"
```

Answers:

1. `MODEL_NAME`: **qwen2.5:7b**
2. `AGENT_MODEL_NAME`: **gemma4:e4b**

### Provider abstraction

File: `modules/ai_advisory/llm_provider.py`

Relevant evidence:

- `DEFAULT_PROVIDER_MODE = "disabled"`
- `PROVIDER_MODE_ENV = "SENTINEL_AI_PROVIDER_MODE"`
- `normalize_provider_mode(...)` only accepts `local` and `openai_compatible` from environment; `fake` is not enabled from env.
- `build_default_provider(...)` returns:
  - `LocalLLMProvider(...)` only if env mode is `local`
  - `OpenAICompatibleProvider(...)` only if env mode is `openai_compatible`
  - otherwise `DisabledLLMProvider()`
- `LocalLLMProvider.generate(...)` lazily imports `langchain_community.chat_models.ChatOllama` only inside the call path.
- `LocalLLMProvider` uses `AGENT_MODEL_NAME` through `_default_local_model_name()` if no `SENTINEL_LOCAL_LLM_MODEL` is set.

### Full AI-Assisted path

Files/functions:

- `ui/streamlit_app.py`, lines 1175-1189: AI Analyst tab calls `render_full_ai_assisted_panel_html(...)`.
- `modules/ui/full_ai_assisted_view.py::render_full_ai_assisted_panel_html(...)`
- `modules/ui/full_ai_assisted_view.py::build_full_ai_assisted_result_from_cli_state(...)`
- `modules/ai_advisory/full_ai_assisted.py::run_full_ai_assisted(...)`

Provider call evidence:

- `modules/ai_advisory/full_ai_assisted.py::run_full_ai_assisted(...)` creates `selected_provider = provider or request.provider or build_default_provider()`.
- It calls `selected_provider.generate(...)` once.
- If provider response is disabled/unavailable, it returns `build_deterministic_grounded_brief(...)` with `llm_status="not_used_deterministic_fallback"` for disabled or `"unavailable_fallback"` for unavailable.
- Unexpected provider exceptions are caught and return unavailable fallback.

Conclusion: default/public path is provider-disabled deterministic fallback. No live LLM required unless env explicitly enables `SENTINEL_AI_PROVIDER_MODE=local` or `openai_compatible`.

### Event-Aware Q&A path

Files/functions:

- `ui/streamlit_app.py`, lines 1090-1112: `render_event_aware_qa_panel(...)` builds result from current session state.
- `modules/ui/event_qa_view.py::build_event_aware_qa_result_from_cli_state(...)`
- `modules/ai_advisory/event_qa.py::answer_event_aware_question(...)`

Provider call evidence:

- `answer_event_aware_question(...)` checks `_unsafe_question_reason(request.question)` before creating/calling the provider.
- Unsafe question: returns deterministic refusal with `provider_mode="disabled"`, `provider_status="disabled"`, `llm_status="not_used_deterministic_fallback"`.
- Safe question: creates `selected_provider = provider or request.provider or build_default_provider()` and calls `selected_provider.generate(...)`.
- Disabled provider response returns deterministic event-aware answer with `llm_status="not_used_deterministic_fallback"`.
- Unexpected provider exceptions return unavailable fallback.

Conclusion: unsafe Event-Aware Q&A does not call a provider; safe Event-Aware Q&A calls the provider abstraction but falls back deterministically when disabled/unavailable.

### Follow-up / 追問 path

Files/functions:

- `ui/streamlit_app.py::run_followup_question(...)`, lines 458-476, sends the question through `_run_orchestrator_with_timing(...)` and `record_followup_output(...)`.
- `modules/agent.py::SecurityAgent._handle_followup(...)`
- `modules/event_followup.py::answer_event_followup(...)`
- `modules/incident_followup.py::answer_incident_followup(...)`
- `modules/rag_qa.py::RAGQA.handle_natural_followup(...)`

Behavior evidence:

- Active incident follow-up is tried first through `answer_incident_followup(...)` when `active_context_kind == "incident"`.
- Active event follow-up is tried through `answer_event_followup(...)` when `active_context_kind == "event"`.
- If deterministic active-context follow-up returns no answer and the query is natural/contextual follow-up, the code can call `self.rag_qa.handle_natural_followup(...)`.
- `LazyRAGQA.handle_natural_followup(...)` lazy-loads `modules.rag_qa.RAGQA`.
- `RAGQA.handle_natural_followup(...)` uses RAG/LLM internals and `ChatOllama(model=MODEL_NAME, temperature=0)` after initialization, then uses safe fallback strings if LLM is unavailable.

Conclusion: active-context follow-up can be deterministic; broader natural/contextual follow-up can involve RAG/ChatOllama and may degrade if unavailable.

### RAG / Knowledge Q&A path

Files/functions:

- `ui/streamlit_app.py::run_knowledge_question(...)`, lines 479-499, forces the KnowledgeQASkill path.
- `modules/agent.py::SecurityAgent.build_rag_answer(...)`
- `modules/lazy_rag.py::LazyRAGQA`
- `modules/rag_qa.py::RAGQA`

Behavior evidence:

- `SecurityAgent.build_rag_answer(...)` checks `if not self.rag_qa.is_ready(): return self.KB_UNAVAILABLE_MESSAGE`.
- `LazyRAGQA.is_ready()` imports/constructs `modules.rag_qa.RAGQA` only when used.
- `RAGQA._initialize_components()` lazily imports:
  - `HuggingFaceEmbeddings(model_name=EMBED_MODEL)`
  - `ChatOllama(model=MODEL_NAME, temperature=0)`
  - `Chroma(persist_directory=CHROMA_PATH, embedding_function=self.embeddings)`
- `RAGQA.is_ready()` requires both vectorstore and llm.

Conclusion: Knowledge Q&A/RAG is not the same as the v3.1 provider-disabled fallback path. It can fail closed to KB unavailable / no context if RAG/LLM is unavailable. Real knowledge answers depend on RAG runtime readiness.

### Legacy LLMAssist path

File/function:

- `modules/llm_assist.py::LLMAssist`

Evidence:

- `LLMAssist._initialize_llm()` imports `ChatOllama` and uses `AGENT_MODEL_NAME`.
- `judge_suspicious_behavior(...)` and `explain_alert(...)` call `_ensure_llm_initialized()` and return fallback if `self.llm is None` or exceptions occur.
- This path uses `gemma4:e4b` when live Ollama is available, but fallback is implemented when unavailable.

Conclusion: legacy LLMAssist may attempt a local model but has fallback behavior. It must not be presented as proof of live LLM availability unless separately smoke-tested.

## Step 3 - Targeted Smoke Tests

I did not run full pytest. I ran targeted tests with pytest cache disabled and bytecode disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider `
  tests/test_ai_advisory_llm_provider.py `
  tests/test_ai_advisory_full_ai_assisted.py `
  tests/test_ai_advisory_event_qa.py `
  tests/test_ui_full_ai_assisted_view.py `
  tests/test_ui_event_qa_view.py `
  tests/test_lazy_rag_startup.py `
  --maxfail=3
```

Result:

```text
50 passed in 4.08s
```

Second targeted group:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider `
  tests/test_event_followup.py `
  tests/test_incident_followup.py `
  tests/test_report_followup.py `
  tests/test_rag_qa_controlled_runtime.py `
  tests/test_rag_intent.py `
  --maxfail=3
```

Result:

```text
131 passed in 2.90s
```

Test evidence supports:

- default provider disabled behavior
- Full AI-assisted deterministic fallback
- Event-Aware Q&A deterministic fallback
- unsafe Event-Aware Q&A refusal before provider call
- provider cannot overwrite official risk/decision in tested paths
- lazy RAG startup behavior
- deterministic event/incident/report follow-up helpers
- controlled RAG runtime safety behavior in tests

## Step 4 - Runtime Behavior Matrix

| Path | Live LLM called? | provider.generate called? | Fallback shown? | Model involved | Evidence |
| --- | --- | --- | --- | --- | --- |
| Full AI-Assisted | No by default; only if provider env enables local/openai-compatible | Yes, through `run_full_ai_assisted(...)`; default provider is disabled | Yes: `not_used_deterministic_fallback` | none by default; `gemma4:e4b` only if local provider mode enabled via env/default local model | `modules/ui/full_ai_assisted_view.py`; `modules/ai_advisory/full_ai_assisted.py`; `modules/ai_advisory/llm_provider.py`; tests passed |
| Event-Aware Q&A safe question | No by default; only if provider env enables local/openai-compatible | Yes for safe question, but default provider is disabled | Yes: deterministic event-aware answer | none by default; `gemma4:e4b` only if local provider mode enabled | `modules/ui/event_qa_view.py`; `modules/ai_advisory/event_qa.py`; tests passed |
| Event-Aware Q&A unsafe question | No | No; refused before provider construction/call | Yes: refusal fallback | none | `answer_event_aware_question(...)` checks `_unsafe_question_reason(...)` first; tests passed |
| follow-up / 追問 | Mixed | No v3.1 provider.generate; active-context follow-up is deterministic; natural/contextual follow-up may use RAGQA | Yes for deterministic active-context helpers; RAG fallback/unavailable possible | active-context: none; natural/contextual RAG follow-up can involve `qwen2.5:7b` | `ui/streamlit_app.py::run_followup_question`; `modules/agent.py::_handle_followup`; `modules/event_followup.py`; `modules/incident_followup.py`; `modules/rag_qa.py` |
| RAG / Knowledge Q&A | Yes for real RAG answer generation when ready | No v3.1 provider.generate; uses RAGQA/ChatOllama directly | KB unavailable/no context fallback if not ready | `qwen2.5:7b` | `ui/streamlit_app.py::run_knowledge_question`; `modules/agent.py::build_rag_answer`; `modules/lazy_rag.py`; `modules/rag_qa.py` |

## Step 5 - Safe Presentation Wording

Because result is **MIXED**, use this classroom-safe sentence:

「部分功能可在 provider disabled 下 fallback，部分功能在 live provider 啟用時會接本機模型。這次報告以畫面狀態為準，不誇大 live LLM 行為。」

Additional safe lines:

1. 「v3.2 的 Full AI-Assisted Advisory Result 和 Event-Aware Q&A 有 provider-disabled deterministic fallback；即使不啟動 Ollama，也能展示 guardrail、fallback、官方判定不可被覆蓋。」
2. 「Knowledge Q&A / RAG 是另一條路徑，實際知識回答依賴 RAG runtime；如果 RAG/LLM 不可用，就應顯示 unavailable 或 no-context 狀態，而不是誇大成 live LLM 成功。」
3. 「開發設定中 `MODEL_NAME` 是 `qwen2.5:7b`，`AGENT_MODEL_NAME` 是 `gemma4:e4b`；但公開展示要以當下 provider status / llm_status 為準。」

## Final Notes

- No git commands were run.
- No code/config/docs were modified except this single requested report file.
- Ollama was not intentionally started, but the requested `ollama ps` command auto-started it on Windows. I stopped the resulting `ollama app.exe` and `ollama.exe serve` processes afterward.
- Final post-stop check showed no Ollama process and no port 11434 listener.
