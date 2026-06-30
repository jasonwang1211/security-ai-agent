# Runtime Mode Matrix

This document records the post-final v3.7 runtime truth. Sentinel Project is a **mixed-runtime** prototype: some AI-advisory panels can run through provider-disabled deterministic fallback, while Knowledge Q&A / RAG paths depend on retrieval and local LLM readiness when real knowledge answers are requested.

Use the UI runtime status, provider status, and error/unavailable messages as the source of truth during demos. Do not describe the whole project as no-LLM, and do not describe every answer as live-LLM output.

## Configured Components

| Component | Current value | Used by |
|---|---:|---|
| `MODEL_NAME` | `qwen2.5:7b` | Knowledge Q&A / RAG runtime and query planning paths. |
| `AGENT_MODEL_NAME` | `gemma4:e4b` | Agent/follow-up/provider paths where enabled. |
| `CHROMA_PATH` | `./chroma_db` | Local Chroma vector store for RAG. |
| `EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | RAG embedding model. |
| `TOP_K` | `5` | RAG retrieval result count. |

## Runtime Paths

| Path | Runtime truth | Live LLM / RAG dependency | Safety boundary |
|---|---|---|---|
| Full AI-Assisted Advisory Result | Provider-disabled deterministic fallback is supported and is the public showcase default unless a provider is explicitly enabled and separately smoke-tested. | No live provider is required for the fallback path. Optional provider contracts exist. | Official Risk Level / Decision are copied from deterministic policy and cannot be changed by AI output. |
| Event-Aware Q&A: safe question | With the default provider disabled, the backend can return a deterministic event-aware fallback answer from the active EvidenceGroundingBundle. | No live provider is required for default fallback. Optional provider output must pass guardrails. | Similar Cases remain advisory and are not proof; Graph context is not a detection source. |
| Event-Aware Q&A: unsafe question | Unsafe questions are refused before provider call. | Provider should not be called for refused unsafe questions. | Refuses exploit, PoC, traffic generation, load testing, real enforcement, and verdict-override requests. |
| Follow-up / 追問 | Mixed path. Active event / incident follow-up can be deterministic. Natural or contextual follow-up may enter RAG follow-up behavior. | Depends on which follow-up path is selected and whether RAG/LLM runtime is available. | Follow-up cannot override official Risk Level / Decision or perform enforcement. |
| RAG / Knowledge Q&A | True knowledge answering depends on RAG runtime, ChatOllama, Chroma, and embedding readiness. If unavailable, it should fail closed to unavailable/no-context behavior rather than overclaim. | Yes for real knowledge answers. | RAG is advisory context only and is not detection authority. |

## What To Say In Demos

- The public showcase path demonstrates deterministic verdict authority, advisory AI panels, provider status, guardrails, and fallback behavior.
- Some backend contracts can connect to optional local or OpenAI-compatible providers, but live provider behavior requires separate manual smoke testing before being presented as working runtime behavior.
- Knowledge Q&A / RAG is a different runtime path from provider-disabled Full AI/Event-QA fallback. It should be described as retrieval-dependent.

## What Not To Claim

- Do not claim the whole project is no-LLM.
- Do not claim every UI answer is live LLM output.
- Do not claim Knowledge Q&A works without RAG/Chroma/Ollama readiness unless the current UI status confirms it.
- Do not claim AI can modify official Risk Level or Decision.
- Do not claim Similar Cases prove compromise.
- Do not claim Graph is a detection source.
- Do not claim real firewall, WAF, EDR, account, cloud, SIEM, or SOAR enforcement.
- Do not claim exploit, PoC, traffic generation, load testing, or offensive automation support.
