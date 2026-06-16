# Screenshot Feature Gallery

This gallery is a feature index for the public screenshots. It is not a tutorial and not a project report. Use [../UI_WALKTHROUGH.md](../UI_WALKTHROUGH.md) for demo steps and [../../REPORT.md](../../REPORT.md) for the formal report.

Screenshots are public review aids and do not contain secrets or credentials.

## Screenshot Sets

- English UI screenshots: [en/](en/) - primary screenshot source for English public docs.
- Traditional Chinese UI screenshots: [zh-TW/](zh-TW/) - screenshot source for Traditional Chinese docs.
- Root docs/screenshots PNG files are legacy compatibility references and should not be the primary source for English public docs.

Where to look: the **v3.0 README Screenshots** section below is the current, readable set used by the root README (six starred images). **English Feature Gallery** is an extended feature index; the **v2.9 Evidence-Grounded AI Brief** and **v3.0 Full-Window** sections are additional references. For Traditional Chinese demos, use the **v3.0 Traditional Chinese (zh-TW) Key Screenshots** section (`zh-TW/20`–`31`).

## English Feature Gallery (extended feature index)

| Screenshot | Feature area | What to look for | Safety note |
|---|---|---|---|
| [01_console_home.png](en/01_console_home.png) | Console home | Four demo cards, language/mode controls, input area, active context, and safety framing. | Scenario cards are safe presets and do not execute traffic. |
| [02_fast_command_injection_analysis.png](en/02_fast_command_injection_analysis.png) | Deterministic triage | Command Injection result with HIGH / BLOCK and rule evidence. | BLOCK is simulated. |
| [03_ai_analyst_brief.png](en/03_ai_analyst_brief.png) | AI Analyst Brief | Advisory summary, deterministic verdict context, no LLM authority, and next steps. | AI does not override Risk Level or Decision. |
| [04_evidence_gap_analyzer.png](en/04_evidence_gap_analyzer.png) | Evidence Gap Analyzer | Confirmed facts, missing evidence, recommended checks, and unsafe assumptions. | Missing evidence requires human review. |
| [05_knowledge_qa_rag.png](en/05_knowledge_qa_rag.png) | Knowledge Q&A / RAG | Defensive knowledge panel and advisory framing. | RAG is not proof of current exploitation. |
| [06_similar_cases.png](en/06_similar_cases.png) | Approved Similar Cases | Curated similar-case comparison with reasons and differences. | Historical cases do not prove the current event. |
| [07_relationship_graph.png](en/07_relationship_graph.png) | Relationship Graph | Event, rule, risk, decision, and case context. | Graph context is explanatory only. |
| [08_case_draft_export.png](en/08_case_draft_export.png) | Case Draft / Export | Reviewable case draft area and Markdown export preview. | Human review is required. |
| [09_http2_resource_exhaustion_demo.png](en/09_http2_resource_exhaustion_demo.png) | HTTP/2 safe synthetic demo | Compact launcher preview, full synthetic input, and cleared stale context. | No exploit, PoC, or traffic generation. |
| [10_full_ai_assisted_optional.png](en/10_full_ai_assisted_optional.png) | Optional Full AI-assisted mode | Optional AI/RAG-assisted mode selection. | Deterministic policy remains authoritative. |

## v3.0 README Screenshots (current, readable)

The current English screenshot set for the README, captured from the live console
(system Chrome via Playwright). Overviews show layout; detail crops are element /
clip captures at 2x device scale so panel text stays readable. The README main text
uses the six starred (★) images; the rest are extended gallery references.

| Screenshot | Type | What to look for |
|---|---|---|
| ★ [20_console_home_overview.png](en/20_console_home_overview.png) | overview | Console home: scenario cards, mode controls, and "BLOCK / MONITOR / ALLOW are simulated" framing. |
| ★ [21_command_injection_overview.png](en/21_command_injection_overview.png) | overview | Command Injection result: Active Context HIGH / BLOCK / CMD-001. |
| [22_ai_analyst_tab_overview.png](en/22_ai_analyst_tab_overview.png) | overview | AI Analyst tab: the full Evidence-Grounded AI Brief structure. |
| ★ [23_brief_official_verdict_detail.png](en/23_brief_official_verdict_detail.png) | detail crop | Official Verdict (Risk HIGH / Decision BLOCK), llm_status fallback, schema chip. |
| [24_brief_supporting_evidence_detail.png](en/24_brief_supporting_evidence_detail.png) | detail crop | Supporting Evidence with rule-001 / ev-001 / ev-002 citations. |
| [25_brief_evidence_gap_detail.png](en/25_brief_evidence_gap_detail.png) | detail crop | Evidence Gap Summary (missing evidence) with gap-001 citations. |
| ★ [26_brief_advisory_context_detail.png](en/26_brief_advisory_context_detail.png) | detail crop | Advisory Context: case-001 (not proof of compromise) and graph-001 (not a detection source). |
| ★ [13_evidence_grounded_markdown_export.png](en/13_evidence_grounded_markdown_export.png) | detail (render) | Markdown export Evidence-Grounded section: schema_version, official_risk_level / official_decision, case-001 / graph-001. Rendered from the real export markdown. |
| [28_knowledge_qa_detail.png](en/28_knowledge_qa_detail.png) | detail crop | Knowledge Q&A panel: advisory framing ("advisory only — it may return no answer"). |
| ★ [29_http2_safe_demo_overview.png](en/29_http2_safe_demo_overview.png) | overview | HTTP/2 Resource Exhaustion Suspicion: MEDIUM / MONITOR / HTTP2-RES-001, no traffic / no real enforcement. |

Detail crops are real-UI element / clip captures, except `13`, which is a faithful
render of the export markdown (labeled). The earlier full-window captures (`14`–`17`)
and the v2.9 panel renders (`11`–`13`) remain below as additional references.

## v2.9 Evidence-Grounded AI Brief (branch)

These v2.9 images are rendered from the live Evidence-Grounded AI Brief panel markup and the console CSS, so they show the exact panel content the analyst sees (the surrounding Streamlit chrome is omitted). They reflect current `v2.9-evidence-grounded-ai-brief` branch behavior.

| Screenshot | Feature area | What to look for | Safety note |
|---|---|---|---|
| [11_evidence_grounded_ai_brief.png](en/11_evidence_grounded_ai_brief.png) | Evidence-Grounded AI Brief | Official Verdict (Risk HIGH / Decision BLOCK), `llm_status: not_used_deterministic_fallback`, schema chip, and cited deterministic evidence (rule-001 / ev-001). | Advisory-only; the official verdict is copied from deterministic policy and cannot be overridden. |
| [12_structured_similar_case_graph_context.png](en/12_structured_similar_case_graph_context.png) | Structured Similar Cases / Graph context | After Find Similar Cases, the Advisory Context cites case-001 and graph-001. | Similar cases are not proof of compromise; graph context is not a detection source. |
| [13_evidence_grounded_markdown_export.png](en/13_evidence_grounded_markdown_export.png) | Markdown export | Exported brief section with schema_version, official_risk_level / official_decision, and case-001 / graph-001 citations. | Export is for human review; it is not enforcement and does not write live knowledge. |

## Traditional Chinese Screenshots

Traditional Chinese UI screenshots are preserved under [zh-TW/](zh-TW/) using the same main file names where available. The Traditional Chinese documents under docs/zh-TW/ should point to that folder or describe it as the Traditional Chinese screenshot source. A Traditional Chinese full-window capture of the Evidence-Grounded AI Brief is available as [zh-TW/17_zh_tw_evidence_grounded_ai_brief.png](zh-TW/17_zh_tw_evidence_grounded_ai_brief.png) — note the brief panel strings render in English (only the surrounding UI chrome is Traditional Chinese).

## v3.0 Traditional Chinese (zh-TW) Key Screenshots (current, readable)

The current zh-TW screenshot set for Chinese-reader / professor demos, captured from
the live console with Interface Language = 繁體中文 (system Chrome via Playwright).
Overviews show layout; detail crops are element / clip captures at 2x device scale so
text stays readable. Items marked ★ are the recommended demo set for a Chinese review.

Mixed-language note: the deterministic path (Rule-Based Detector, Risk Level, Decision,
Analysis Report, Safety Boundary) and all UI chrome render in Traditional Chinese. The
v2.9 **Evidence-Grounded AI Brief panel keeps English section labels** (Official Verdict,
Supporting Evidence, Advisory Context, Citations, …) regardless of UI language; its
content is mixed (some English, some — e.g. the evidence-gap / next-step items — follow
the UI language). So shots `24`–`28` show Traditional Chinese chrome with an English /
mixed brief panel. This is a known limitation, not full localization — see
[v3.0_presentation_notes.zh-TW §9](../zh-TW/v3.0_presentation_notes.zh-TW.md).

| Screenshot | Type | What to look for |
|---|---|---|
| ★ [20_zhtw_console_home_overview.png](zh-TW/20_zhtw_console_home_overview.png) | overview | zh-TW console home: 示範情境卡, 介面語言 = 繁體中文, 模式 = 快速確定性, and the "BLOCK / MONITOR / ALLOW 是專案模擬決策" safety caption. |
| [21_zhtw_command_injection_input_overview.png](zh-TW/21_zhtw_command_injection_input_overview.png) | overview | Loaded payload `test; rm -rf /tmp/test` in the input with an empty 目前脈絡 below — the app loads but does not execute the payload. |
| ★ [22_zhtw_deterministic_result_overview.png](zh-TW/22_zhtw_deterministic_result_overview.png) | overview | After 執行輸入: 目前脈絡 Command Injection / HIGH / BLOCK / CMD-001 plus the zh-TW 分析報告. |
| ★ [23_zhtw_active_context_detail.png](zh-TW/23_zhtw_active_context_detail.png) | detail crop | Active-context hero card: 攻擊/事件 Command Injection, 風險 HIGH, 決策 BLOCK, 規則/證據 CMD-001. |
| ★ [24_zhtw_ai_analyst_tab_overview.png](zh-TW/24_zhtw_ai_analyst_tab_overview.png) | overview | AI 分析助理 tab: the full Evidence-Grounded AI Brief structure (English labels, mixed content). |
| ★ [25_zhtw_brief_official_verdict_detail.png](zh-TW/25_zhtw_brief_official_verdict_detail.png) | detail crop | Official Verdict (Risk HIGH / Decision BLOCK), simulated_decision: true, authority: deterministic_policy. |
| [26_zhtw_brief_supporting_evidence_detail.png](zh-TW/26_zhtw_brief_supporting_evidence_detail.png) | detail crop | Supporting Evidence with rule-001 / ev-001 / ev-002 citations. |
| ★ [27_zhtw_brief_advisory_context_detail.png](zh-TW/27_zhtw_brief_advisory_context_detail.png) | detail crop | Advisory Context: case-001 (not proof of compromise) and graph-001 (not a detection source). |
| [28_zhtw_markdown_export_detail.png](zh-TW/28_zhtw_markdown_export_detail.png) | detail crop | Markdown export `## Evidence-Grounded AI Brief` section: schema_version, official_risk_level / official_decision, case-001 / graph-001. The export markdown is mixed zh-TW / English. |
| ★ [29_zhtw_http2_safe_demo_overview.png](zh-TW/29_zhtw_http2_safe_demo_overview.png) | overview | HTTP/2 資源耗盡疑似事件: MEDIUM / MONITOR / HTTP2-RES-001, no traffic generated / no real enforcement. |
| [30_zhtw_clear_context_empty_state.png](zh-TW/30_zhtw_clear_context_empty_state.png) | overview | After 清除脈絡: 目前脈絡 empty ("尚無目前脈絡") — switching scenarios leaves no stale event. |
| [31_zhtw_safety_boundary_detail.png](zh-TW/31_zhtw_safety_boundary_detail.png) | detail crop | zh-TW 安全邊界 panel: simulated BLOCK only, no real enforcement, similar cases / graph do not override the verdict. |

The legacy zh-TW set (`zh-TW/01`–`10`, `17`) remains for compatibility; the `20`–`31`
set above is the current readable source for Traditional Chinese demos.

## v3.0 Full-Window Screenshots

Full-window app captures (with the Streamlit chrome), driven through the live console.
They complement the v2.9 panel renders above (`en/11`–`13`).

| Screenshot | Feature area | What to look for | Safety note |
|---|---|---|---|
| [14_full_window_ai_analyst_evidence_grounded_brief.png](en/14_full_window_ai_analyst_evidence_grounded_brief.png) | Full-window AI Analyst tab | Active Context (Command Injection / HIGH / BLOCK / CMD-001) and the Evidence-Grounded AI Brief: Official Verdict HIGH / BLOCK, `llm_status: not_used_deterministic_fallback`, schema, rule-001 / ev-001 citations. | Advisory-only; the official verdict is copied from deterministic policy and cannot be overridden. |
| [15_full_window_similar_case_graph_context.png](en/15_full_window_similar_case_graph_context.png) | Full-window after Find Similar Cases | The brief's Advisory Context cites case-001 ("not proof of current compromise") and graph-001 ("is not a detection source"), with matching Unsafe Assumptions. | Similar cases are not proof of compromise; graph context is not a detection source. |
| [16_full_window_markdown_export.png](en/16_full_window_markdown_export.png) | Full-window Draft / Export | Markdown export preview with the `## Evidence-Grounded AI Brief` section: schema_version, official_risk_level / official_decision, and case-001 / graph-001 citations. | Export is for human review; it is not enforcement and does not write live knowledge. |
| [zh-TW/17_zh_tw_evidence_grounded_ai_brief.png](zh-TW/17_zh_tw_evidence_grounded_ai_brief.png) | Traditional Chinese UI (full window) | zh-TW app chrome (tabs / controls) with the Evidence-Grounded AI Brief in context. | The brief panel strings are currently English-only (not yet localized); only the surrounding UI chrome is Traditional Chinese. |

Note: the Evidence-Grounded AI Brief panel labels render in English regardless of UI
language, so screenshot 17 shows Traditional Chinese chrome with an English brief
panel. Localizing the brief panel strings is a possible follow-up.

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated decisions only.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph provide advisory context only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit code, PoC generation, traffic generation, or offensive automation is provided.
- Human review is required.
