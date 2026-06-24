# v3.5 Human-Approved Knowledge Capture Execution Plan

Branch: `v3.5-human-approved-knowledge-capture`

This branch starts the next project direction: human-approved knowledge capture for future RAG and Knowledge Graph workflows. The final presentation package remains frozen and outside the repository.

## Current Architecture Summary

### RAG

- Runtime RAG is centered around `modules/rag_qa.py` and helper modules under `modules/rag/`.
- Heavy vector dependencies are lazily initialized by `RAGQA`; CI and public showcase paths do not require live LLMs, Chroma, embeddings, API keys, or network access.
- RAG output is advisory-only. It explains defensive knowledge and does not change official Risk Level or Decision.
- Current RAG retrieval reads approved knowledge sources; v3.5 must not auto-ingest unreviewed AI output.

### Graph / Similar Cases

- Graph helpers live under `modules/graph/` and related UI/advisory helpers.
- Graph context is read-only explanation context and is explicitly not a detection source.
- Approved Similar Cases are manually curated seed cases. Similar Cases are advisory comparisons only and do not prove compromise.
- v3.5 can produce graph export candidates, but must not write directly into graph facts or treat graph outputs as official detection evidence.

### AI Advisory / Event-Aware Q&A

- `modules/ai_advisory/evidence_bundle.py` builds deterministic `EvidenceGroundingBundle` objects from already-computed facts.
- `modules/ai_advisory/event_qa.py` answers current-event questions and refuses unsafe questions before provider calls.
- `modules/ui/event_qa_view.py` and `ui/streamlit_app.py` are future hook points, but UI wiring is deferred for this branch unless explicitly approved.

## Proposed Knowledge Capture Pipeline

1. User asks an Event-Aware Q&A question, adds analyst context, or reviews an AI advisory answer.
2. A deterministic extractor creates a `CandidateKnowledgeNote` with provenance.
3. Safety filtering flags unsafe content, verdict-override attempts, missing provenance, or unsupported proof claims.
4. Candidate is appended to a pending review queue.
5. A human analyst reviews, edits, approves, or rejects the candidate.
6. Approved notes are stored separately from pending/rejected notes.
7. Only approved notes can be exported as advisory RAG markdown snippets or graph node/edge candidates.
8. Exported artifacts remain advisory-only and are not detection sources.

## Data Model

Selected v3.5 model types:

- `KnowledgeCaptureProvenance`
- `CandidateKnowledgeNote`
- `ApprovedKnowledgeNote`
- `RejectedKnowledgeNote`
- `GraphNodeCandidate`
- `GraphEdgeCandidate`
- `RagIngestionCandidate`

Required provenance includes source event, question, answer summary, evidence/rule/gap/RAG/case/graph IDs, timestamps, actor fields, status, confidence label, and safety flags.

## Storage Design

Use simple local JSONL files:

- `data/knowledge_capture/pending_notes.jsonl`
- `data/knowledge_capture/approved_notes.jsonl`
- `data/knowledge_capture/rejected_notes.jsonl`

For this branch, tests should use temporary directories. Do not commit real user/private captured notes. Example schemas can live under `docs/examples/knowledge_capture/`.

## UI Review Flow

Deferred. Future Streamlit hook points:

- Event-Aware Q&A answer panel: offer "Save as candidate note" after answer review.
- AI Analyst advisory panel: offer capture from generated summary/evidence gap text.
- Case/Draft area: offer capture from analyst-written notes.
- Review queue panel: list pending notes, allow edit/approve/reject.

This branch should not modify Streamlit layout.

## RAG Ingestion Flow

v3.5 foundation exports approved notes as markdown snippets with provenance headers and advisory-only warnings. It does not call Chroma, embeddings, ingest scripts, or live RAG update logic.

## Knowledge Graph Export Flow

v3.5 foundation exports approved notes as graph node/edge candidate JSON. Exports must label nodes/edges as advisory-only and not detection sources. No graph builder or persisted graph facts are modified.

## Safety Constraints

- No auto-approval.
- No auto-ingest of unreviewed notes.
- No unsafe content capture.
- No exploit, PoC, traffic generation, load testing, or offensive automation.
- No PII/secret capture.
- No claim that captured notes prove compromise.
- Similar Cases remain advisory-only.
- Graph remains advisory-only and not a detection source.
- RAG remains advisory-only.
- Official Risk Level and Decision remain deterministic.
- Human review is required before approval/export.

## Selected Tasks For This Branch

1. Add docs/spec for human-approved knowledge capture.
2. Add deterministic `modules/knowledge_capture` foundation:
   - types
   - safety extraction/filtering
   - JSONL store
   - RAG markdown export
   - graph candidate export
3. Add deterministic unit tests for safety, storage, and export boundaries.
4. Update `docs/ROADMAP.md` and `docs/TECH_NOTES.md` only with minimal v3.5 notes if needed.

## Expected Files

- `docs/V3_5_KNOWLEDGE_CAPTURE_EXECUTION_PLAN.md`
- `docs/KNOWLEDGE_CAPTURE_SPEC.md`
- `docs/examples/knowledge_capture/README.md`
- `modules/knowledge_capture/__init__.py`
- `modules/knowledge_capture/types.py`
- `modules/knowledge_capture/extractor.py`
- `modules/knowledge_capture/store.py`
- `modules/knowledge_capture/rag_export.py`
- `modules/knowledge_capture/graph_export.py`
- `tests/test_knowledge_capture_*.py`

## Test Plan

- Candidate note requires provenance.
- Unsafe content is flagged or rejected.
- Risk/Decision override attempts are flagged.
- Pending notes cannot be exported.
- Only approved notes can be exported.
- RAG markdown includes advisory-only warning and provenance.
- Graph export labels nodes/edges as advisory-only.
- Graph export does not mark anything as detection source.
- Similar Case references are not treated as proof.
- Exploit/PoC/traffic-generation content is not accepted.

## Rollback Plan

If the branch becomes risky:

1. Stop work in the isolated worktree.
2. From the source repository, remove the worktree:
   - `git worktree remove <knowledge-capture-worktree>`
3. Delete the branch if desired:
   - `git branch -D v3.5-human-approved-knowledge-capture`
4. The original repository and final presentation package should remain unaffected.

## Deferred Tasks

- Streamlit UI review queue.
- Real RAG ingestion into Chroma or embeddings.
- Graph builder integration.
- Live LLM-assisted note extraction.
- Knowledge promotion workflow in the public UI.
- Audit log beyond local JSONL provenance.
