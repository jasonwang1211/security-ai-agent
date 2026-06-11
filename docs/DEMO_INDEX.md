# Demo Index / 展示索引

This index collects the recommended demo path, screenshot evidence, and supporting documents for the current Sentinel Project console.

本索引整理目前 Sentinel Project 主控台的建議展示流程、截圖證據與支援文件。

## Start the Streamlit SOC Console / 啟動 Streamlit SOC 主控台

Recommended:

```powershell
.\venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

If your active Python environment already contains the project dependencies, this also works:

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

## Core Materials / 核心文件

| Material | Link |
|---|---|
| Bilingual user operation guide / 雙語操作指南 | [USER_OPERATION_GUIDE.md](USER_OPERATION_GUIDE.md) |
| Screenshot index / UI 截圖索引 | [screenshots/README.md](screenshots/README.md) |
| Test report / 測試報告 | [TEST_REPORT.md](TEST_REPORT.md) |
| Code review audit / 程式碼檢視稽核 | [CODE_REVIEW_AUDIT.md](CODE_REVIEW_AUDIT.md) |
| Demo presentation guide / 展示簡報指南 | [demo_presentation_guide.md](demo_presentation_guide.md) |
| Final smoke checklist / 最終展示檢查表 | [final_demo_smoke_checklist.md](final_demo_smoke_checklist.md) |
| v2.7 release notes | [v2.7_release_notes.md](v2.7_release_notes.md) |
| v2.8 startup import audit | [v2.8_startup_import_audit.md](v2.8_startup_import_audit.md) |
| v2.8 cache cleanup checklist | [v2.8_cache_cleanup_checklist.md](v2.8_cache_cleanup_checklist.md) |
| Project README | [../README.md](../README.md) |

## Recommended Live Demo Path / 建議現場展示流程

1. Start the Streamlit console.
2. Confirm the home screen, language selector, analysis mode selector, and Demo Scenario Launcher.
3. Switch UI language if needed; AI Analyst Brief, Evidence Gap, and Knowledge Q&A output follow the selected language.
4. Load or type the Command Injection demo input: `test; rm -rf /tmp/test`.
5. Show Fast deterministic analysis: `Command Injection`, `HIGH`, simulated `BLOCK`.
6. Open the AI Analyst tab and show AI Analyst Brief plus Evidence Gap Analyzer.
7. Ask Knowledge Q&A about HTTP/2 Resource Exhaustion or CVE.
8. Click Find Similar Cases and show `CASE-SEED-001` as advisory historical context.
9. Show Graph Relations for event, attack type, rule, evidence, risk, decision, and similar case links.
10. Show Case Draft and Export Report boundaries.
11. Load `HTTP/2 Resource Exhaustion Suspicion` and emphasize that the launcher card is a short preview, while the textarea receives the full synthetic incident summary with safety lines.

## Screenshot-Guided Path / 截圖導覽

| Step | Screenshot | What to show |
|---|---|---|
| 1 | [01_console_home.png](screenshots/01_console_home.png) | Console home, mode selector, language selector, demo launcher. |
| 2 | [02_fast_command_injection_analysis.png](screenshots/02_fast_command_injection_analysis.png) | Fast command-injection result with deterministic `HIGH` / simulated `BLOCK`. |
| 3 | [03_ai_analyst_brief.png](screenshots/03_ai_analyst_brief.png) | AI Analyst Brief: deterministic advisory / no LLM. |
| 4 | [04_evidence_gap_analyzer.png](screenshots/04_evidence_gap_analyzer.png) | Evidence Gap Analyzer and review questions. |
| 5 | [05_knowledge_qa_rag.png](screenshots/05_knowledge_qa_rag.png) | Knowledge Q&A / RAG defensive answer. |
| 6 | [06_similar_cases.png](screenshots/06_similar_cases.png) | Approved Similar Cases with `CASE-SEED-001`. |
| 7 | [07_relationship_graph.png](screenshots/07_relationship_graph.png) | Relationship Graph visualization. |
| 8 | [08_case_draft_export.png](screenshots/08_case_draft_export.png) | Case Draft and Export Report tabs. |
| 9 | [09_http2_resource_exhaustion_demo.png](screenshots/09_http2_resource_exhaustion_demo.png) | Safe HTTP/2 Resource Exhaustion scenario. |
| 10 | [10_full_ai_assisted_optional.png](screenshots/10_full_ai_assisted_optional.png) | Optional Full AI-assisted mode, only if local AI/RAG is ready. |

## Expected Demo Outputs / 預期展示輸出

| Scenario | Input | Expected result |
|---|---|---|
| Command Injection | `test; rm -rf /tmp/test` | Command Injection / `HIGH` / simulated `BLOCK` / similar case `CASE-SEED-001` |
| SQL Injection | `?id=1' OR '1'='1` | SQL Injection / `HIGH` / simulated `BLOCK` / similar case `CASE-SEED-003` |
| Authentication Incident | `demo_logs\scenario_a_mixed_auth.log` | Possible account compromise suspicion / `HIGH` / simulated `MONITOR` / similar case `CASE-SEED-002` |
| HTTP/2 Resource Exhaustion Suspicion | Demo Scenario Launcher | Synthetic incident summary only; no traffic generation and no real enforcement |

Note: the HTTP/2 launcher card intentionally shows a compact preview. The full synthetic input is preserved when the scenario is loaded into the main textarea.

## What To Emphasize / 展示重點

- Detection is rule-based.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated labels.
- AI Analyst Brief, Evidence Gap, RAG, Similar Cases, and Graph are advisory context.
- Similar cases do not prove compromise or execution in the current event.
- The HTTP/2 Resource Exhaustion scenario is synthetic and safe.
- Output language follows UI language selection for AI Analyst Brief, Evidence Gap, and Knowledge Q&A.
- Human review is required.

## What Not To Claim / 不要宣稱

- Do not claim the system blocks real traffic.
- Do not claim it changes firewall, WAF, EDR, account, cloud, SIEM, or SOAR state.
- Do not claim RAG or LLM decides the final verdict.
- Do not claim CVE context proves an asset was exploited.
- Do not provide exploit, PoC, or traffic-generation instructions.

## v2.7/v2.8 Evidence Links

- Manual smoke evidence: [v2.7_manual_smoke_report.md](v2.7_manual_smoke_report.md)
- Release gate: [v2.7_release_gate.md](v2.7_release_gate.md)
- Release notes: [v2.7_release_notes.md](v2.7_release_notes.md)
- Startup import audit: [v2.8_startup_import_audit.md](v2.8_startup_import_audit.md)
- Cache cleanup checklist: [v2.8_cache_cleanup_checklist.md](v2.8_cache_cleanup_checklist.md)
