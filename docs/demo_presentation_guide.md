# Demo Presentation Guide / 展示簡報指南

This guide is for a short professor or reviewer walkthrough. It pairs the live Streamlit console with the refreshed screenshot evidence in `docs/screenshots/`.

本指南適合課堂、教授審查或作品集展示使用，可搭配 Streamlit 主控台與 `docs/screenshots/` 截圖證據。

## Presentation Goal / 展示目標

Show that Sentinel Project can provide useful AI-assisted analyst context while preserving a deterministic safety boundary.

要傳達的重點是：系統可以提供 AI 輔助的分析脈絡，但最終偵測、風險與決策仍由確定性邏輯負責。

One-sentence framing:

> Sentinel is a safe SOC analyst console: deterministic detection makes the verdict, while AI/RAG-style panels help the analyst understand, compare, and document the case.

## Recommended Talk Track / 建議講稿流程

1. Open the console and show the language selector, analysis mode, and Demo Scenario Launcher.
2. Explain that UI language controls AI Analyst Brief, Evidence Gap, and Knowledge Q&A output style.
3. Load the Command Injection demo or enter `test; rm -rf /tmp/test`.
4. Point out the deterministic result: `Command Injection`, `HIGH`, simulated `BLOCK`.
5. Open AI Analyst and show AI Analyst Brief.
6. Show Evidence Gap Analyzer and explain that it asks what evidence is still missing.
7. Ask Knowledge Q&A about HTTP/2 Resource Exhaustion or CVE.
8. Click Find Similar Cases and explain that `CASE-SEED-001` is historical advisory context only.
9. Open Graph Relations and show how event, rule, evidence, risk, decision, and case context connect.
10. Show Case Draft / Export Report and explain the human-review boundary.
11. Load HTTP/2 Resource Exhaustion Suspicion and stress that its card is a short preview while the full textarea input remains safety-complete.

## Suggested Timing / 建議時間分配

| Time | Topic | Notes |
|---|---|---|
| 0:00-0:40 | Opening | Explain safe AI-assisted SOC triage. |
| 0:40-1:30 | Architecture | Rule-based detection -> deterministic risk/decision -> advisory panels. |
| 1:30-2:30 | Command Injection | Show `HIGH` / simulated `BLOCK`. |
| 2:30-3:30 | AI Analyst + Evidence Gap | Show advisory summary and missing evidence. |
| 3:30-4:15 | RAG + Similar Cases + Graph | Show context, not authority. |
| 4:15-5:00 | HTTP/2 scenario + boundaries | Synthetic scenario, no traffic, no real enforcement, human review required. |

## Screenshot Support / 截圖輔助

Use screenshots if the local demo environment is slow or optional Full AI-assisted mode is not ready.

| Screenshot | Use |
|---|---|
| [01_console_home.png](screenshots/01_console_home.png) | Start screen and controls. |
| [02_fast_command_injection_analysis.png](screenshots/02_fast_command_injection_analysis.png) | Fast deterministic command-injection result. |
| [03_ai_analyst_brief.png](screenshots/03_ai_analyst_brief.png) | AI Analyst Brief. |
| [04_evidence_gap_analyzer.png](screenshots/04_evidence_gap_analyzer.png) | Evidence Gap Analyzer. |
| [05_knowledge_qa_rag.png](screenshots/05_knowledge_qa_rag.png) | Knowledge Q&A / RAG. |
| [06_similar_cases.png](screenshots/06_similar_cases.png) | Similar case retrieval. |
| [07_relationship_graph.png](screenshots/07_relationship_graph.png) | Relationship Graph. |
| [08_case_draft_export.png](screenshots/08_case_draft_export.png) | Case Draft and Export Report. |
| [09_http2_resource_exhaustion_demo.png](screenshots/09_http2_resource_exhaustion_demo.png) | HTTP/2 Resource Exhaustion safe demo. |
| [10_full_ai_assisted_optional.png](screenshots/10_full_ai_assisted_optional.png) | Optional Full AI-assisted mode. |

## Key Talking Points / 核心說明

- The detector is rule-based, not LLM-based.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions.
- AI Analyst Brief is deterministic advisory context and says no LLM.
- Evidence Gap helps avoid overclaiming by listing missing evidence.
- RAG answers are defensive knowledge support, not final verdicts, and follow the selected UI language.
- Approved Similar Cases are read-only references and never prove the current event.
- Graph Relations visualize context, not detection authority.
- Case Draft and Export Report require human review.
- HTTP/2 Resource Exhaustion demo is synthetic and safe; the launcher card is compact, and Load Scenario preserves the full safety text.

## What Not To Overclaim / 不要過度宣稱

Avoid these claims:

- The prototype blocks real network traffic.
- The prototype changes firewall, WAF, EDR, account, cloud, SIEM, or SOAR state.
- The LLM decides whether an attack happened.
- RAG evidence overrides Risk Level or Decision.
- CVE information proves active exploitation.
- Similar historical cases prove compromise.
- The HTTP/2 demo generates attack traffic.

Safer phrasing:

- “This is simulated enforcement.”
- “This is advisory analyst context.”
- “The current event still needs evidence review.”
- “Human review is required.”

## Backup Plan / 備援方案

If Streamlit is slow, use the screenshots in `docs/screenshots/` and the operation guide in `docs/USER_OPERATION_GUIDE.md`.

If Full AI-assisted mode is slow or local AI services are unavailable, stay in Fast deterministic mode. Fast mode is the primary demo path because it proves the core safety boundary without relying on local model availability.

If Knowledge Q&A is slow on first use, explain that v2.8 intentionally lazy-loads RAG only when knowledge retrieval is requested.

## Related Documents / 相關文件

- [USER_OPERATION_GUIDE.md](USER_OPERATION_GUIDE.md)
- [DEMO_INDEX.md](DEMO_INDEX.md)
- [final_demo_smoke_checklist.md](final_demo_smoke_checklist.md)
- [TEST_REPORT.md](TEST_REPORT.md)
- [CODE_REVIEW_AUDIT.md](CODE_REVIEW_AUDIT.md)
- [screenshots/README.md](screenshots/README.md)
