# Feature Gallery

This gallery documents the current Sentinel Project Streamlit analyst console. Screenshots are public review aids and do not contain secrets or credentials.

## Gallery

| Screenshot | Feature area | What to look for | Safety note |
|---|---|---|---|
| [01_console_home.png](01_console_home.png) | Console home | Four demo cards, language/mode controls, input area, active context, and visible safety framing. | Scenario cards are safe presets and do not execute traffic. |
| [02_fast_command_injection_analysis.png](02_fast_command_injection_analysis.png) | Deterministic triage | Command Injection result with HIGH / BLOCK and rule evidence. | BLOCK is simulated. |
| [03_ai_analyst_brief.png](03_ai_analyst_brief.png) | AI Analyst Brief | Advisory summary, deterministic verdict context, no LLM authority, and next steps. | AI does not override Risk Level or Decision. |
| [04_evidence_gap_analyzer.png](04_evidence_gap_analyzer.png) | Evidence Gap Analyzer | Confirmed facts, missing evidence, review tasks, and unsafe assumptions. | Missing evidence must be reviewed by a human. |
| [05_knowledge_qa_rag.png](05_knowledge_qa_rag.png) | Knowledge Q&A / RAG | Defensive answer following selected UI language and advisory framing. | RAG is not proof of current exploitation. |
| [06_similar_cases.png](06_similar_cases.png) | Approved Similar Cases | Curated similar-case comparison with reasons and differences. | Historical cases do not prove the current event. |
| [07_relationship_graph.png](07_relationship_graph.png) | Relationship Graph | Event, rule, risk, decision, and case context. | Graph context is explanatory only. |
| [08_case_draft_export.png](08_case_draft_export.png) | Case Draft / Export | Reviewable case draft and Markdown export preview. | Human review is required. |
| [09_http2_resource_exhaustion_demo.png](09_http2_resource_exhaustion_demo.png) | HTTP/2 safe synthetic demo | Compact launcher preview, full synthetic input, and cleared stale context. | No exploit, PoC, or traffic generation. |
| [10_full_ai_assisted_optional.png](10_full_ai_assisted_optional.png) | Optional Full AI-assisted mode | Optional AI/RAG-assisted path. | Deterministic policy remains authoritative. |

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit / PoC / traffic generation is provided.
- Human review is required.
