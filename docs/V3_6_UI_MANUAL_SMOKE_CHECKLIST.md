# v3.6 Knowledge Capture Review UI Manual Smoke Checklist

This checklist is for the local review UI prototype only. It does not require live LLMs, API keys, Chroma, embeddings, network access, runtime RAG ingest, or runtime Graph mutation.

## Setup

1. From the v3.6 worktree, start Streamlit:

   ```powershell
   python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
   ```

2. Open the Streamlit console in the browser.
3. Confirm the existing Analysis / Case Intelligence / Draft Export / AI Analyst / System Debug groups still appear.
4. Open the AI Analyst tab.
5. Confirm the Knowledge Capture Review expander is present and collapsed by default.

## Empty State

1. Expand Knowledge Capture Review.
2. Confirm the store path is shown as `.tmp/knowledge_capture_ui/capture_store`.
3. Confirm the empty state says no local knowledge capture notes are available.
4. Confirm the empty state suggests:

   ```powershell
   python scripts/demo_knowledge_capture.py --output-dir .tmp/knowledge_capture_ui --clean
   ```

5. Confirm advisory-only labels are visible:
   - advisory-only
   - not a detection source
   - not proof of compromise
   - does not override Risk Level / Decision
   - no real enforcement
   - no automatic RAG ingestion or Graph mutation

## Generate Synthetic Demo Notes

1. Stop Streamlit only if needed, or leave it running and use a separate terminal.
2. Run:

   ```powershell
   python scripts/demo_knowledge_capture.py --output-dir .tmp/knowledge_capture_ui --clean
   ```

3. Confirm the script reports synthetic demo completion.
4. Confirm generated files are under `.tmp/knowledge_capture_ui/`.
5. Refresh the Streamlit page.
6. Re-open AI Analyst -> Knowledge Capture Review.

## Review Queue Behavior

1. Confirm pending / approved / rejected sections render from local JSONL files.
2. Confirm each note shows:
   - title
   - body
   - source event ID
   - source question
   - source answer summary
   - evidence/rule/gap/RAG/case/graph IDs
   - official Risk Level / Decision as copied deterministic context
3. For a pending note, enter a reviewer name.
4. Edit the note body with safe defensive wording.
5. Click Approve note.
6. Confirm the action succeeds. Refresh if needed to see the note move from pending to approved.
7. For another pending note, enter a reviewer name and reject reason.
8. Click Reject note.
9. Confirm the action succeeds. Refresh if needed to see the note move to rejected.

## Export Preview Checks

1. Expand an approved note.
2. Confirm RAG markdown preview is visible.
3. Confirm Graph candidate JSON preview is visible.
4. Confirm RAG preview includes advisory warning text.
5. Confirm Graph candidate JSON marks nodes/edges as:
   - `advisory_only: true`
   - `not_detection_source: true`
   - `not_proof: true`
6. Confirm there is no button or status message for:
   - ingest into RAG
   - write/mutate Graph
   - live LLM extraction
   - enforcement
   - auto-approval

## Safety Confirmation

Confirm all of the following remain true:

- No RAG ingest occurred.
- No Chroma or embedding operation occurred.
- No Graph runtime mutation occurred.
- No live LLM, API key, or network call was required.
- Official Risk Level / Decision did not change.
- Similar Cases were not presented as proof of compromise.
- Graph was not presented as a detection source.
- No exploit, PoC, traffic generation, load testing, or offensive automation was added.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action occurred.

## Expected Result

The review queue is usable as a local prototype for human-approved knowledge notes, while all RAG, Graph, detector, risk, decision, and enforcement boundaries remain unchanged.
