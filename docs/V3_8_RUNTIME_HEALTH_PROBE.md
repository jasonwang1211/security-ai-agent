
# v3.8 Runtime Health Probe

## Purpose

The v3.8 runtime health probe makes Sentinel Project's mixed runtime easier to inspect without changing runtime behavior. It gives reviewers a read-only view of provider fallback, configured local models, Chroma path presence, embedding configuration, and RAG lazy state.

The probe is not a detector, not a RAG answer path, and not a provider selector.

## Passive vs Active Checks

`collect_runtime_health()` defaults to passive mode:

- reads `config.py` values;
- reads relevant environment values;
- checks whether `CHROMA_PATH` exists using `pathlib` only;
- reports embeddings as configured, not initialized;
- reports RAG runtime as `lazy_not_initialized`;
- reports provider-disabled fallback as available.

Passive mode does **not**:

- contact Ollama;
- run `ollama` CLI commands;
- auto-start Ollama;
- auto-start Chroma;
- import Chroma, LangChain vector stores, sentence-transformers, or torch;
- initialize embeddings;
- download models;
- call `RAGQA.is_ready()`.

Optional active checks are explicit:

- `check_ollama=True` performs a short-timeout HTTP status/model-list request to the configured Ollama endpoint.
- `check_models=True` checks configured model names only if the Ollama status request succeeds.

Missing Ollama or missing models return structured unavailable/missing statuses instead of raising to callers.

## Status Fields

| Field | Meaning |
|---|---|
| `provider_mode` | `disabled`, `live`, or `unknown` based on provider environment configuration. |
| `ollama_server.status` | `not_checked`, `reachable`, or `unreachable`. |
| `primary_model.status` | `not_checked`, `ready`, `missing`, or `unavailable` for `MODEL_NAME`. |
| `agent_model.status` | `not_checked`, `ready`, `missing`, or `unavailable` for `AGENT_MODEL_NAME`. |
| `chroma_path.status` | `not_checked`, `exists`, or `missing`. |
| `rag_runtime.status` | `lazy_not_initialized`, `ready`, `unavailable`, or `not_checked`. Passive mode uses `lazy_not_initialized`. |
| `embeddings.status` | `configured`, `available`, `unavailable`, or `not_checked`. Passive mode uses `configured`. |
| `fallback.status` | `available` or `unavailable`. |

Configured values currently come from `config.py`:

- `MODEL_NAME = qwen2.5:7b`
- `AGENT_MODEL_NAME = gemma4:e4b`
- `CHROMA_PATH = ./chroma_db`
- `EMBED_MODEL = sentence-transformers/all-MiniLM-L6-v2`
- `TOP_K = 5`

## Safety Boundaries

The runtime health probe preserves the existing authority split:

- Rule-Based Detector remains detection authority.
- Official Risk Level / Decision remain deterministic.
- BLOCK / MONITOR / ALLOW remain simulated.
- AI / RAG / Similar Cases / Graph remain advisory-only.
- Similar Cases are not proof of compromise.
- Graph is not a detection source.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, PoC, traffic generation, load testing, or offensive automation is added.
- Human review remains required.

## Relationship To Mixed Runtime Truth

The probe supports the v3.7 mixed-runtime documentation:

- Full AI-Assisted Advisory Result can use provider-disabled deterministic fallback.
- Event-Aware Q&A safe questions can use deterministic fallback under default provider-disabled mode.
- Event-Aware Q&A unsafe questions are refused before provider call.
- Follow-up can be deterministic or RAG-backed depending on route and state.
- RAG / Knowledge Q&A true answering depends on local RAG runtime readiness.

## Why Passive Mode Does Not Call `RAGQA.is_ready()`

`RAGQA.is_ready()` calls `_ensure_initialized()`. That can import and initialize embeddings, ChatOllama, and Chroma. A passive health probe must be safe for CI and Streamlit startup, so it reports RAG as `lazy_not_initialized` rather than triggering runtime initialization.

A future explicit active RAG health check may be added, but it should be manual, clearly labeled, short-timeout, and separate from default UI startup.

## Streamlit Runtime Health Panel

The Streamlit console now includes a small Runtime Health panel under the
System / Debug tab.

Default behavior:

- calls `collect_runtime_health()` with passive defaults;
- does not check Ollama or models;
- does not initialize Chroma, embeddings, or RAG;
- does not call `RAGQA.is_ready()`;
- shows `not_checked`, `lazy_not_initialized`, and `configured` statuses plainly.

Optional live check:

- the `Check live Ollama / models` button calls
  `collect_runtime_health(passive=False, check_ollama=True, check_models=True)`;
- active results are displayed as `runtime_health: active_live_check`, not passive;
- the check contacts Ollama `/api/tags` only and uses the short timeout from
  `modules/runtime_health.py`;
- no model generation or inference is performed;
- no RAG, Chroma, or embedding initialization is performed;
- unreachable Ollama or missing models are displayed as structured status values,
  not as unhandled exceptions.

Windows launch note:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m streamlit run .\ui\streamlit_app.py
```
