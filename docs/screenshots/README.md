# Screenshot Gallery

This gallery keeps screenshot sets separated by UI language so the English
public documentation does not mix English text with Traditional Chinese UI
captures.

Screenshots are public review aids and do not contain secrets or credentials.

## Screenshot Sets

- **English UI screenshots:** [`en/`](en/) - complete current public set used by
  the English `README.md`, `REPORT.md`, and `docs/UI_WALKTHROUGH.md`.
- **Traditional Chinese UI screenshots:** [`zh-TW/`](zh-TW/) - Traditional
  Chinese UI captures used by the documents under `docs/zh-TW/`.
- The legacy root `docs/screenshots/*.png` files are retained for history and
  are not the primary source for English public documentation.

## English Screenshot Set

| Screenshot | Feature area | What to look for | Safety note |
|---|---|---|---|
| [01_console_home.png](en/01_console_home.png) | Console home | Four demo cards, language/mode controls, input area, active context, and visible safety framing. | Scenario cards are safe presets and do not execute traffic. |
| [02_fast_command_injection_analysis.png](en/02_fast_command_injection_analysis.png) | Deterministic triage | Command Injection result with HIGH / BLOCK and rule evidence. | BLOCK is simulated. |
| [03_ai_analyst_brief.png](en/03_ai_analyst_brief.png) | AI Analyst Brief | Advisory summary, deterministic verdict context, no LLM authority, and next steps. | AI does not override Risk Level or Decision. |
| [04_evidence_gap_analyzer.png](en/04_evidence_gap_analyzer.png) | Evidence Gap Analyzer | Confirmed facts, missing evidence, review tasks, and unsafe assumptions. | Missing evidence must be reviewed by a human. |
| [05_knowledge_qa_rag.png](en/05_knowledge_qa_rag.png) | Knowledge Q&A / RAG | Defensive knowledge panel and advisory framing in English UI mode. | RAG is not proof of current exploitation. |
| [06_similar_cases.png](en/06_similar_cases.png) | Approved Similar Cases | Curated similar-case comparison with reasons and differences. | Historical cases do not prove the current event. |
| [07_relationship_graph.png](en/07_relationship_graph.png) | Relationship Graph | Event, rule, risk, decision, and case context. | Graph context is explanatory only. |
| [08_case_draft_export.png](en/08_case_draft_export.png) | Case Draft / Export | Reviewable case draft area and Markdown export preview. | Human review is required. |
| [09_http2_resource_exhaustion_demo.png](en/09_http2_resource_exhaustion_demo.png) | HTTP/2 safe synthetic demo | Compact launcher preview, full synthetic input, and cleared stale context. | No exploit, PoC, or traffic generation. |
| [10_full_ai_assisted_optional.png](en/10_full_ai_assisted_optional.png) | Optional Full AI-assisted mode | Optional AI/RAG-assisted mode selection. | Deterministic policy remains authoritative. |

## Traditional Chinese Screenshots

Traditional Chinese UI screenshots are preserved under [`zh-TW/`](zh-TW/) using
the same file naming convention where available. The Traditional Chinese
documents link to or reference that folder directly.

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit / PoC / traffic generation is provided.
- Human review is required.
