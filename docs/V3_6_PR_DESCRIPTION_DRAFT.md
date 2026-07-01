# v3.6 PR Description Draft

## Summary

Adds a local Streamlit review queue prototype for Human-Approved Knowledge Capture. The UI is collapsed by default inside the AI Analyst tab and reads from a local `.tmp` review store. It allows manual approve/reject actions and preview-only RAG markdown / Graph candidate exports.

## Motivation

v3.5 introduced the knowledge capture foundation and demo artifacts, but review still required direct script/model usage. v3.6 makes the workflow easier to inspect from the analyst console while preserving the strict advisory-only and human-review boundaries.

## What Changed

- Added `modules/ui/knowledge_capture_view.py` for pure review queue rendering and approve/reject/export-preview helpers.
- Added a collapsed Knowledge Capture Review expander to the existing AI Analyst tab.
- Added i18n labels for the review queue controls and captions.
- Added deterministic UI tests covering empty state, pending/approved rendering, approve/reject helpers, export previews, safe default store path, and forbidden-action wording.
- Updated `docs/KNOWLEDGE_CAPTURE_SPEC.md` with the local review UI prototype scope.
- Added review summary and manual smoke checklist docs.

## What Did Not Change

- No detector changes.
- No risk scoring changes.
- No deterministic decision policy changes.
- No runtime RAG behavior changes.
- No Chroma ingestion or embeddings.
- No runtime Graph mutation.
- No live LLM/provider/network/API behavior.
- No case draft or ToolPolicy behavior changes.
- No final presentation package changes.

## Safety Boundaries

- Rule-Based Detector remains detection authority.
- Official Risk Level / Decision remain deterministic.
- BLOCK / MONITOR / ALLOW remain simulated only.
- Captured notes remain advisory-only.
- Similar Cases are not proof of compromise.
- Graph context is not a detection source.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action.
- No exploit / PoC / traffic generation.
- No auto-approval.
- No automatic RAG ingestion.
- No automatic Graph mutation.
- Human review required.

## Tests

- `tests/test_ui_knowledge_capture_view.py`
- Existing knowledge capture foundation and demo artifact tests remain in place.

## Validation

- `python -m pytest` -> `1343 passed in 15.14s`
- `python -m ruff check .` -> passed
- `python -m mypy app.py modules tests` -> passed, `Success: no issues found in 196 source files`
- `git diff --check` -> passed; Git reported line-ending normalization warnings only
- `git status --short --untracked-files=all` -> expected uncommitted review-pass files before this commit

## Screenshots / Demo Notes

Screenshots: N/A for this patch.

Manual smoke should use:

```powershell
python scripts/demo_knowledge_capture.py --output-dir .tmp/knowledge_capture_ui --clean
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

Then open the AI Analyst tab and expand Knowledge Capture Review.

## Risk Level

Low. The patch adds a collapsed local review UI and pure helper tests. It does not wire any runtime RAG/Graph mutation or live provider behavior.

## Rollback Plan

Revert the v3.6 commits or remove the isolated worktree/branch:

```powershell
git worktree remove <review-ui-worktree>
git branch -D v3.6-knowledge-capture-review-ui
```

## Reviewer Notes

Focus review on UI wording, local store path behavior, manual approve/reject ergonomics, and ensuring future RAG/Graph integration remains explicitly reviewed rather than automatic.
