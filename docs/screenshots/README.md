# Demo Screenshots / 展示截圖

Final UI screenshots of the Security AI Agent Streamlit SOC console, captured for
presentation / demo / interview materials (v2.6-AC visual QA pass).

- Captured from `ui/streamlit_app.py` running locally
  (`python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none`).
- Interface language: **繁體中文 (zh-TW)** — the project's primary demo language.
  English / 中英雙語 labels are fully supported (language selector in the control panel).
- Viewport: 1480 px wide desktop.

> **Reminders**
> - `BLOCK` / `MONITOR` / `ALLOW` are **simulated** project decisions — no real firewall,
>   WAF, EDR, account, password reset, monitoring deployment, or enforcement action is executed.
> - Detection is **rule-based** (not LLM-based). Risk Level and Decision are deterministic.
> - **AI / RAG output is advisory analyst context only** and does **not** override the
>   deterministic Risk Level or Decision. Human review is required before trusting or
>   promoting any case draft.

## Screenshots

| # | File | Shows |
|---|------|-------|
| 1 | `01_console_home.png` | Initial console — SOC status bar, Input / Control Panel, Demo Scenario Launcher (3 SOC playbook cards), no active context. |
| 2 | `02_fast_command_injection_analysis.png` | Fast deterministic Command Injection result — Active Context hero + cyan `⚡ 快速確定性` mode banner + Analysis Report. |
| 3 | `03_full_ai_assisted_analysis.png` | Full AI-assisted Command Injection result — hero with `完整 AI 輔助` + `AI/RAG 輔助` chips + purple `🧠 完整 AI 輔助` mode banner + Analysis Report. |
| 4 | `04_ai_analyst_followup.png` | AI Analyst → Follow-up Assistant answering a follow-up; response card with the cyan `確定性追問 / Deterministic follow-up` route badge. |
| 5 | `05_knowledge_qa_rag.png` | AI Analyst → Knowledge Q&A (RAG); response card with the purple `RAG / 知識問答 / Knowledge Q&A` route badge. |
| 6 | `06_similar_cases.png` | Case Intelligence → Approved Similar Cases, top match `CASE-SEED-001`. |
| 7 | `07_graph_relations.png` | Case Intelligence → Graph Relations, the relationship graph (Current Event → HIGH / BLOCK → shared fields → CASE-SEED-001). |
| 8 | `08_case_draft_export.png` | Draft / Export tab — Case Draft status + safety boundary, and the in-memory Markdown Export Report preview. |

## Exact scenario / input per screenshot

| # | Language | Analysis mode | Input / action | Expected output |
|---|----------|---------------|----------------|-----------------|
| 1 | zh-TW | Fast deterministic (default) | App opened; no run | Demo launcher visible; Active Context = none (📡 empty state). |
| 2 | zh-TW | Fast deterministic | Load **Command Injection Demo** (`test; rm -rf /tmp/test`) → Run input | `Command Injection` · `HIGH` · `BLOCK`; cyan Fast mode banner. |
| 3 | zh-TW | Full AI-assisted | Same input, Full AI-assisted → Run input | `Command Injection` · `HIGH` · `BLOCK`; AI/RAG explanation layer executed; purple Full banner + `AI/RAG 輔助` chip. |
| 4 | zh-TW | Full AI-assisted (context) | AI Analyst → ask `這代表命令真的執行了嗎？` | Deterministic active-context explanation: matching a payload does **not** prove the command executed; advisory boundary. Skill: `ExplainActiveEventSkill`. |
| 5 | zh-TW | — (advisory RAG) | AI Analyst → Knowledge Q&A → ask `什麼是 Command Injection？` | RAG / knowledge-base explanation of Command Injection. Skill: `KnowledgeQASkill`. |
| 6 | zh-TW | (current context) | Find Similar Cases | Approved similar case `CASE-SEED-001` (Command Injection Payload With Simulated BLOCK). |
| 7 | zh-TW | (current context) | Graph Relations panel | Relationship graph linking the current event and `CASE-SEED-001` via attack / rule / evidence / risk / decision / similar. |
| 8 | zh-TW | (current context) | Draft / Export tab | Case Draft = no pending draft (approval-gated, `safety_reviewed` false); Export Report Markdown preview (advisory, in-memory, no repo write). |

## Notes

- Screenshots 4 and 5 demonstrate the two AI Analyst surfaces:
  **Follow-up Assistant** = deterministic active-context explanation (cyan badge),
  **Knowledge Q&A** = RAG / security knowledge lookup (purple badge). Both are advisory.
- The Full AI-assisted first run is slower because the AI/RAG explanation layer loads its
  embedding model on first use (the UI shows a warm-up note in Full mode).
