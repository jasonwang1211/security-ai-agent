# v3.6 Knowledge Capture Review UI Summary

Branch: `v3.6-knowledge-capture-review-ui`

## Branch Purpose

v3.6 adds a low-risk local Streamlit review queue prototype for the v3.5 Human-Approved Knowledge Capture foundation. It makes pending/approved/rejected local notes visible from the AI Analyst tab without changing runtime RAG, runtime Graph, detector, risk scoring, decision logic, or official verdict authority.

## Base And Current HEAD

- Base commit: `4238ed2 docs: add knowledge capture demo artifacts and review notes`
- Current HEAD before this review-pass commit: `cb386ef`

## Commits Included

- `3663d2a docs: add v3.6 knowledge capture review UI plan`
- `f3ca04b feat: add knowledge capture review UI prototype`
- `cb386ef test: add knowledge capture review UI safety tests`
- This review-pass commit: `docs: add v3.6 review and UI smoke notes`

## Files Changed

- `docs/V3_6_KNOWLEDGE_CAPTURE_REVIEW_UI_PLAN.md`
- `docs/V3_6_REVIEW_SUMMARY.md`
- `docs/V3_6_PR_DESCRIPTION_DRAFT.md`
- `docs/V3_6_UI_MANUAL_SMOKE_CHECKLIST.md`
- `docs/KNOWLEDGE_CAPTURE_SPEC.md`
- `modules/ui/knowledge_capture_view.py`
- `modules/ui/i18n.py`
- `ui/streamlit_app.py`
- `tests/test_ui_knowledge_capture_view.py`

## UI Behavior Added

- Adds a collapsed Knowledge Capture Review expander in the existing AI Analyst tab.
- Reads local review notes from `.tmp/knowledge_capture_ui/capture_store/` by default.
- Shows empty-state guidance that points to `scripts/demo_knowledge_capture.py --output-dir .tmp/knowledge_capture_ui --clean`.
- Shows pending, approved, and rejected notes from `KnowledgeCaptureStore`.
- Shows note title, body, provenance, copied official Risk Level / Decision, and advisory-only boundary text.
- Allows manual approval through `approve_note(...)`, including edited body revalidation.
- Allows manual rejection through `reject_note(...)` with a reason.
- Shows approved-only RAG markdown and Graph candidate JSON previews.

## Behavior Not Changed

- No detector changes.
- No risk scoring changes.
- No deterministic decision policy changes.
- No runtime RAG behavior changes.
- No Chroma or embedding ingestion.
- No runtime Graph mutation.
- No live LLM/provider/network/API behavior.
- No case draft or ToolPolicy behavior changes.
- No final presentation package changes.

## Safety Boundaries Preserved

- Rule-Based Detector remains detection authority.
- Official Risk Level / Decision remain deterministic.
- BLOCK / MONITOR / ALLOW remain simulated only.
- Knowledge Capture output is advisory-only.
- Similar Cases are not proof of compromise.
- Graph context is not a detection source.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action.
- No exploit / PoC / traffic generation.
- No auto-approval.
- No automatic RAG ingestion.
- No automatic Graph mutation.
- Human review remains required.

## Validation Results

- `python -m pytest` -> `1343 passed in 15.14s`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed, `Success: no issues found in 196 source files`
- `git diff --check` -> passed; Git reported line-ending normalization warnings only
- `git status --short --untracked-files=all` -> expected uncommitted review-pass files before this commit

## Known Risks

- This is a prototype review surface, not a production governance workflow.
- After an approve/reject click, Streamlit may require a normal rerun/refresh before the list display above the action controls reflects the moved note.
- The local `.tmp` store is intentionally not a durable production knowledge base.
- Manual smoke should confirm the default demo script output and UI store path remain aligned.

## Deferred Items

- Production audit log and governance workflow.
- Durable role-based review permissions.
- Runtime RAG ingestion into Chroma/embeddings.
- Runtime Graph fact promotion or mutation.
- Live LLM note extraction.
- Screenshot refresh and README showcase updates.

## Reviewer Checklist

- Confirm the review queue is collapsed by default and does not disturb existing AI Analyst panels.
- Confirm empty state points to the synthetic demo script.
- Confirm default store path stays under `.tmp/knowledge_capture_ui/capture_store/`.
- Confirm no UI control says or performs RAG ingest, Graph write/mutation, live LLM extraction, enforcement, or auto-approval.
- Confirm pending note approval calls the hardened `approve_note(...)` path.
- Confirm unsafe edited text stays pending and surfaces safety flags.
- Confirm approved RAG/Graph outputs are preview-only.
- Confirm official Risk Level / Decision are copied context only.
- Confirm Similar Cases are not described as proof.
- Confirm Graph is not described as a detection source.

## Merge Recommendation

Ready for human review after the presentation. Merge risk is low because runtime RAG, runtime Graph, detector, risk, decision, and ToolPolicy behavior are unchanged. The remaining review focus should be UI wording, manual smoke ergonomics, and whether to keep the prototype collapsed in the AI Analyst tab.
