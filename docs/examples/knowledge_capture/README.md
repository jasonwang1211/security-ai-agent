# Knowledge Capture Examples

This folder contains synthetic examples for the v3.5 human-approved knowledge capture foundation. Do not store real user/private content here.

## Example Lifecycle

1. `sample_candidate_note.json` shows a pending defensive analyst note with source event, question, answer summary, evidence/rule/gap/RAG/case/graph IDs, and copied official Risk Level / Decision.
2. `sample_approved_note.json` shows the same kind of note after human approval.
3. `sample_rejected_note.json` shows a safe but insufficient note that remains non-exportable.
4. `sample_rag_export.md` shows the approved-only advisory markdown candidate for future reviewed RAG ingestion.
5. `sample_graph_candidates.json` shows advisory-only graph node/edge candidates derived from the approved note.

## Safety Boundary

All examples are synthetic and defensive. They are advisory-only, are not detection sources, do not prove compromise, do not override deterministic Risk Level / Decision, and authorize no real firewall / WAF / EDR / account / cloud / SIEM / SOAR action.

v3.5 uses runtime JSONL paths under `data/knowledge_capture/`, but tests and demos should use temporary directories. The sample files in this folder do not run Chroma, embeddings, live RAG ingest, graph mutation, LLMs, network calls, or API keys.
