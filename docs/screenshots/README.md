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

## Traditional Chinese Screenshots

Traditional Chinese UI screenshots are preserved under [zh-TW/](zh-TW/) using the same main file names where available. The Traditional Chinese documents under docs/zh-TW/ should point to that folder or describe it as the Traditional Chinese screenshot source.

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated decisions only.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph provide advisory context only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit code, PoC generation, traffic generation, or offensive automation is provided.
- Human review is required.
