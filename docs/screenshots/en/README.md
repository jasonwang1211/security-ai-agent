# English UI Screenshots

This folder contains verified English-language Streamlit console screenshots for
public GitHub documentation. These PNGs are used by the English `README.md`,
`REPORT.md`, `docs/UI_WALKTHROUGH.md`, and the
[main screenshot gallery](../README.md).

Traditional Chinese UI screenshots are preserved under [`../zh-TW/`](../zh-TW/).
The legacy root `docs/screenshots/*.png` files are retained for history and are
not the English documentation source.

## Files

| Screenshot | Feature area |
|---|---|
| [01_console_home.png](01_console_home.png) | Console home and demo scenario launcher |
| [02_fast_command_injection_analysis.png](02_fast_command_injection_analysis.png) | Fast deterministic Command Injection analysis |
| [03_ai_analyst_brief.png](03_ai_analyst_brief.png) | AI Analyst Brief |
| [04_evidence_gap_analyzer.png](04_evidence_gap_analyzer.png) | Evidence Gap Analyzer |
| [05_knowledge_qa_rag.png](05_knowledge_qa_rag.png) | Knowledge Q&A / RAG panel |
| [06_similar_cases.png](06_similar_cases.png) | Approved Similar Cases |
| [07_relationship_graph.png](07_relationship_graph.png) | Relationship Graph |
| [08_case_draft_export.png](08_case_draft_export.png) | Case Draft / Markdown Export |
| [09_http2_resource_exhaustion_demo.png](09_http2_resource_exhaustion_demo.png) | HTTP/2 Resource Exhaustion safe synthetic demo |
| [10_full_ai_assisted_optional.png](10_full_ai_assisted_optional.png) | Optional Full AI-assisted mode |

## Capture Notes

- Captured from the Streamlit analyst console with Interface Language set to English.
- The HTTP/2 screenshot uses the safe synthetic demo input and shows no active stale Command Injection context.
- The Knowledge Q&A screenshot uses the English panel safe state rather than forcing a slow RAG generation.
- Screenshots contain no secrets or credentials.
