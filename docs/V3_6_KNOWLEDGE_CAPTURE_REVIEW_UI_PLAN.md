# v3.6 Knowledge Capture Review UI Plan

Branch: `v3.6-knowledge-capture-review-ui`

## Purpose

v3.6 prototypes a low-risk Streamlit review queue for the v3.5 human-approved knowledge capture foundation. The goal is to make pending/approved/rejected local notes reviewable without changing detector authority, deterministic Risk Level / Decision, runtime RAG, runtime Graph, or official verdict behavior.

## Current UI Hook Points

- `modules/ui/event_qa_view.py` is a pure renderer for Event-Aware Q&A output and already avoids Streamlit imports.
- `modules/ui/evidence_grounded_brief_view.py` builds shared evidence bundles and renders escaped HTML without retrieval, graph work, file writes, or enforcement.
- `modules/ui/full_ai_assisted_view.py` renders the v3.2 Full AI-assisted advisory result with provider disabled by default.
- `modules/ui/console_state.py` owns lightweight Streamlit session state helpers and stale-state clearing.
- `ui/streamlit_app.py` owns the actual Streamlit layout and the AI Analyst tab ordering.
- Existing tests prefer pure helper assertions and static source checks where possible.

## Proposed Review Queue Flow

1. Load a local `KnowledgeCaptureStore` from a safe demo/review directory.
2. Show pending notes with title, body, provenance, copied official Risk Level / Decision, and advisory-only boundary text.
3. Let a reviewer edit body text before approval.
4. Call `KnowledgeCaptureStore.approve_note(...)`; approval-time revalidation remains the authority for edited text.
5. Let a reviewer reject a note with a reason via `KnowledgeCaptureStore.reject_note(...)`.
6. Show approved notes.
7. Preview approved-only RAG markdown export via `export_approved_note_to_rag_markdown(...)`.
8. Preview approved-only Graph node/edge candidates via `export_approved_note_to_graph_candidates(...)`.
9. Show explicit labels that captured notes are advisory-only, not detection sources, not proof of compromise, do not override Risk Level / Decision, and authorize no real enforcement.

## Storage Behavior

- Default prototype store path should be `.tmp/knowledge_capture_ui/`.
- The UI must not write to `data/knowledge_capture/` by default.
- Tests should use temporary directories.
- The review UI can point users to `scripts/demo_knowledge_capture.py` when no local notes exist.
- No real user/private captured content should be committed.

## Safety Boundaries

- No auto-approval.
- No automatic RAG ingestion.
- No automatic Graph mutation.
- No live LLM extraction.
- No API keys, network, Chroma, or embeddings.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action.
- No exploit / PoC / traffic generation.
- No change to official Risk Level / Decision.
- Similar Cases are not proof of compromise.
- Graph is not a detection source.
- Human review remains required before approval/export.

## Expected Files To Change

- `modules/ui/knowledge_capture_view.py`
- `tests/test_ui_knowledge_capture_view.py`
- `ui/streamlit_app.py` only if integration remains small and isolated.
- `modules/ui/i18n.py` only if new labels need translation.
- `docs/KNOWLEDGE_CAPTURE_SPEC.md`

## Tests To Add

- Empty-state rendering when no notes exist.
- Pending note display includes advisory boundary and copied official Risk Level / Decision.
- Approve action calls `store.approve_note(...)` and surfaces validation errors.
- Unsafe edited approval keeps the note pending.
- Reject action calls `store.reject_note(...)`.
- Approved note preview calls RAG/Graph export helpers.
- Export previews label advisory-only / not detection source / not proof.
- The UI exposes no auto-ingest, live LLM, Chroma, graph mutation, or enforcement actions.
- No final package paths are referenced.

## Rollback Plan

If this prototype becomes risky:

1. Stop before wiring into `ui/streamlit_app.py`.
2. Keep only the pure component and tests, or revert the branch commit.
3. Remove the isolated worktree if needed:
   - `git worktree remove <review-ui-worktree>`
4. Delete the branch if desired:
   - `git branch -D v3.6-knowledge-capture-review-ui`

## Deferred Items

- Production governance workflow.
- Persistent audit log beyond local JSONL records.
- RAG ingestion into Chroma or embeddings.
- Graph fact promotion or mutation.
- Live LLM note extraction.
- Full UI design polish and screenshots.
- README showcase updates.
