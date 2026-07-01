# v3.8 Runtime Health Manual Smoke Result

## 1. Branch and HEAD

- Branch: `v3.8-live-provider-rag-health`
- Starting HEAD: `e0163a0 fix: clarify runtime health active check display`
- Scope: documentation-only record of manual Streamlit smoke results.

## 2. Launch Command

Manual smoke launched Streamlit with:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m streamlit run .\ui\streamlit_app.py
```

The System / Debug tab opened successfully, and the Runtime Health panel was visible.

## 3. Passive Runtime Health Panel Result

Default passive runtime health displayed:

- `runtime_health: passive`
- `Provider mode: disabled`
- `Fallback: available`
- `Ollama server: not_checked`
- `Primary model: not_checked · qwen2.5:7b`
- `Agent model: not_checked · gemma4:e4b`
- `Chroma path: exists · ./chroma_db`
- `Embeddings: configured · sentence-transformers/all-MiniLM-L6-v2`
- `RAG runtime: lazy_not_initialized`

The passive boundary text was visible:

> Passive health check does not start Ollama, initialize Chroma, initialize embeddings, or call RAGQA.is_ready().

## 4. Active Live Ollama / Model Check Result

Clicking `Check live Ollama / models` returned quickly and did not crash.

The active live check displayed:

- `runtime_health: active_live_check`
- `Provider mode: disabled`
- `Fallback: available`
- `Ollama server: reachable`
- `Primary model: ready · qwen2.5:7b`
- `Agent model: ready · gemma4:e4b`
- `Chroma path: exists · ./chroma_db`
- `Embeddings: configured · sentence-transformers/all-MiniLM-L6-v2`
- `RAG runtime: not_checked`

The active boundary text was visible:

> Live health check contacts Ollama /api/tags only; it does not initialize RAG, Chroma, embeddings, or call RAGQA.is_ready().

Label/value rows now have visible separators, including:

- `Provider mode: disabled`
- `Fallback: available`
- `Ollama server: reachable`

## 5. Full AI-Assisted Fallback Observation

The Full AI-Assisted advisory result still showed provider-disabled deterministic fallback:

- `provider_mode: disabled`
- `provider_status: disabled`
- `llm_status: not_used_deterministic_fallback`
- `guardrail_status: not_run`

Official Risk Level and Decision remained deterministic.

## 6. Safety Confirmations

- No RAG, Chroma, or embedding initialization was observed from the Runtime Health panel.
- No model generation or inference was performed by the Runtime Health panel.
- No detector, risk, or decision behavior changed.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR enforcement was observed.
- Full AI-assisted output remained advisory-only under provider-disabled deterministic fallback.
- Final presentation package was untouched.

## 7. Caveats and Remaining Risks

- Active live check only verifies Ollama reachability and configured model availability through `/api/tags`.
- Active live check does not prove RAG / Knowledge Q&A can answer successfully.
- `RAG runtime: not_checked` during active live check is expected because the check intentionally does not initialize RAG or call `RAGQA.is_ready()`.
- This smoke confirms `qwen2.5:7b` and `gemma4:e4b` were available while Ollama was running.
- Earlier smoke also observed unreachable/unavailable behavior when Ollama was unavailable, without crashing.

## 8. PR / Merge Readiness

Manual Streamlit smoke passed for the v3.8 Runtime Health panel. Passive mode remained non-invasive, active live check correctly displayed active_live_check and model readiness, and no RAG/Chroma/embedding initialization or detector/risk/decision behavior change was observed.

Based on this manual smoke and the existing validation baseline, v3.8 is ready for PR / merge review. A reviewer should still treat live RAG / Knowledge Q&A readiness as separate from the Runtime Health panel's passive and Ollama model checks.

## 9. Documentation Task Confirmation

During this documentation task:

- No code was modified.
- No tests were modified.
- No runtime behavior was changed.
- No push, tag, release, merge, rebase, or reset was performed.
- The final presentation package was untouched.
