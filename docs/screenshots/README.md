# Screenshot Feature Gallery

This gallery is a feature index for the public screenshots. It is not a tutorial and not a project report. Use [../UI_WALKTHROUGH.md](../UI_WALKTHROUGH.md) for demo steps and [../../REPORT.md](../../REPORT.md) for the formal report.

Screenshots are public review aids and do not contain secrets or credentials.

## Screenshot Sets

- English UI screenshots: [en/](en/) - primary screenshot source for English public docs.
- Traditional Chinese UI screenshots: [zh-TW/](zh-TW/) - screenshot source for Traditional Chinese docs.
- Root docs/screenshots PNG files are legacy compatibility references and should not be the primary source for English public docs.

## English Feature Gallery

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

## v2.9 Evidence-Grounded AI Brief (branch)

These v2.9 images are rendered from the live Evidence-Grounded AI Brief panel markup and the console CSS, so they show the exact panel content the analyst sees (the surrounding Streamlit chrome is omitted). They reflect current `v2.9-evidence-grounded-ai-brief` branch behavior.

| Screenshot | Feature area | What to look for | Safety note |
|---|---|---|---|
| [11_evidence_grounded_ai_brief.png](en/11_evidence_grounded_ai_brief.png) | Evidence-Grounded AI Brief | Official Verdict (Risk HIGH / Decision BLOCK), `llm_status: not_used_deterministic_fallback`, schema chip, and cited deterministic evidence (rule-001 / ev-001). | Advisory-only; the official verdict is copied from deterministic policy and cannot be overridden. |
| [12_structured_similar_case_graph_context.png](en/12_structured_similar_case_graph_context.png) | Structured Similar Cases / Graph context | After Find Similar Cases, the Advisory Context cites case-001 and graph-001. | Similar cases are not proof of compromise; graph context is not a detection source. |
| [13_evidence_grounded_markdown_export.png](en/13_evidence_grounded_markdown_export.png) | Markdown export | Exported brief section with schema_version, official_risk_level / official_decision, and case-001 / graph-001 citations. | Export is for human review; it is not enforcement and does not write live knowledge. |

## Traditional Chinese Screenshots

Traditional Chinese UI screenshots are preserved under [zh-TW/](zh-TW/) using the same main file names where available. The Traditional Chinese documents under docs/zh-TW/ should point to that folder or describe it as the Traditional Chinese screenshot source. A Traditional Chinese full-window capture of the Evidence-Grounded AI Brief is available as [zh-TW/17_zh_tw_evidence_grounded_ai_brief.png](zh-TW/17_zh_tw_evidence_grounded_ai_brief.png) — note the brief panel strings render in English (only the surrounding UI chrome is Traditional Chinese).

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
