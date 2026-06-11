# Screenshot Gallery

This gallery documents the current Sentinel Project Streamlit console states used for public review. Screenshots do not contain secrets or credentials.

## Safety Reminder

- Rule-Based Detector is the detection authority.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated.
- RAG, LLM, AI Analyst Brief, and Evidence Gap provide advisory context only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, proof-of-concept, or traffic generation is provided.
- Human review is required.

## Current Screenshot Set

| # | File | Description | Feature area |
|---|---|---|---|
| 1 | [01_console_home.png](01_console_home.png) | Console home, status bar, language/mode controls, and Demo Scenario Launcher. | Console overview |
| 2 | [02_fast_command_injection_analysis.png](02_fast_command_injection_analysis.png) | Fast deterministic Command Injection result with `HIGH / BLOCK` and rule evidence. | Deterministic triage |
| 3 | [03_ai_analyst_brief.png](03_ai_analyst_brief.png) | AI Analyst Brief showing selected-language output, deterministic advisory, no LLM, and boundary language. | AI advisory |
| 4 | [04_evidence_gap_analyzer.png](04_evidence_gap_analyzer.png) | Evidence Gap Analyzer listing missing evidence and unsafe assumptions. | AI advisory |
| 5 | [05_knowledge_qa_rag.png](05_knowledge_qa_rag.png) | Knowledge Q&A / RAG answer following selected UI language and remaining advisory only. | Knowledge Q&A |
| 6 | [06_similar_cases.png](06_similar_cases.png) | Approved Similar Cases showing advisory historical comparison for Command Injection. | Case intelligence |
| 7 | [07_relationship_graph.png](07_relationship_graph.png) | Relationship Graph showing current event, risk/decision, shared fields, and approved case context. | Case intelligence |
| 8 | [08_case_draft_export.png](08_case_draft_export.png) | Case Draft and Markdown Export preview. | Draft / export |
| 9 | [09_http2_resource_exhaustion_demo.png](09_http2_resource_exhaustion_demo.png) | Safe HTTP/2 Resource Exhaustion synthetic demo with compact launcher preview and full safety-preserving input. | Safe scenario |
| 10 | [10_full_ai_assisted_optional.png](10_full_ai_assisted_optional.png) | Optional Full AI-assisted path showing AI/RAG-assisted mode. | Optional AI-assisted mode |

Older screenshots from previous development passes may exist for comparison, but the table above is the current public gallery.
