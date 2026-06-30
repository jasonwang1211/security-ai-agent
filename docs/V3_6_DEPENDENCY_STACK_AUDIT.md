# v3.6 Knowledge Capture / Review UI Dependency Stack Audit

Date: 2026-06-30

Scope: read-only dependency audit for importing Repo B v3.5/v3.6 Knowledge Capture / Review UI work into Repo A. No patches were applied, no cherry-picks were run, no merges/rebases/resets were run, and no code/tests/docs were edited except this audit report.

## 1. Repo A Current State

Repo A: `C:\Users\jason\Desktop\sentinel_project`

Observed state:

```text
branch: v3.7-post-final-runtime-truth
HEAD: ee8422c docs: add post-final runtime truth audit
git status --short --untracked-files=all: clean
```

Recent 20 commits:

```text
* ee8422c (HEAD -> v3.7-post-final-runtime-truth) docs: add post-final runtime truth audit
* 42d2859 (v3.3-post-presentation-hardening, safety/pre-vnext-codex-checkpoint) docs: add post-presentation hardening plan
* f0c2376 (origin/v3.2-full-ai-assisted-showcase, v3.2-full-ai-assisted-showcase) docs: update README showcase for v3.2 AI-assisted UI
* d535469 docs: add v3.2 AI-assisted showcase screenshots
* 65767b2 fix: collapse detailed evidence-grounded brief in AI Analyst tab
* fef90da fix: clear stale knowledge QA on new analysis
* 0741eac fix: localize v3.2 AI analyst UI labels
* 3ce7ad1 fix: clean up v3.2 event QA label and validation notes
* 1fe9899 docs: note v3.2 AI-assisted UI wiring scope
* 995995b feat: wire full AI-assisted showcase into AI Analyst tab
* 847500b feat: add event-aware advisory Q&A UI helper
* c0d9cc6 feat: render full AI-assisted advisory result in UI helper
* 917a86a feat: share UI evidence bundle construction
* 0e883e4 (origin/v3.1-full-ai-assisted-foundation, v3.1-full-ai-assisted-foundation) docs: clarify v3.1 baseline and live-provider status
* 010b6d5 docs: explain validation coverage and safety test scope
* f3fdf9e fix: render zh-TW event QA fallback with real newlines
* 2e9b291 fix: harden v3.1 AI provider fallbacks
* d43a45f fix: repair prompt contract zh-TW safety text
* b34bd7a fix: satisfy advisory lazy-import source guards
* ff5123f docs: document v3.1 full AI-assisted foundation
```

## 2. Repo B Current State

Repo B: `C:\Users\jason\Desktop\sentinel_project_review_ui`

Observed state:

```text
branch: v3.6-knowledge-capture-review-ui
HEAD: dee4d0b docs: add v3.6 review and UI smoke notes
git status --short --untracked-files=all: clean
```

Recent 40 commits:

```text
* dee4d0b (HEAD -> v3.6-knowledge-capture-review-ui) docs: add v3.6 review and UI smoke notes
* cb386ef test: add knowledge capture review UI safety tests
* f3ca04b feat: add knowledge capture review UI prototype
* 3663d2a docs: add v3.6 knowledge capture review UI plan
* 4238ed2 (v3.5-human-approved-knowledge-capture) docs: add knowledge capture demo artifacts and review notes
* a10090c test: harden knowledge capture approval and export safety
* 70266e9 test: add knowledge capture safety regressions
* 88dfdb3 feat: add human-approved knowledge capture foundation
* 4e32a2d docs: add knowledge capture design spec
* 0575360 (v3.4-post-report-hardening-start) test: add v3.4 post-report safety regressions
* d5ea78a docs: add v3.4 validation and provider smoke guidance
* d2eb9ad docs: add v3.4 execution notes
* 42d2859 (v3.3-post-presentation-hardening, safety/pre-vnext-codex-checkpoint) docs: add post-presentation hardening plan
* f0c2376 (origin/v3.2-full-ai-assisted-showcase, v3.2-full-ai-assisted-showcase) docs: update README showcase for v3.2 AI-assisted UI
* d535469 docs: add v3.2 AI-assisted showcase screenshots
* 65767b2 fix: collapse detailed evidence-grounded brief in AI Analyst tab
* fef90da fix: clear stale knowledge QA on new analysis
* 0741eac fix: localize v3.2 AI analyst UI labels
* 3ce7ad1 fix: clean up v3.2 event QA label and validation notes
* 1fe9899 docs: note v3.2 AI-assisted UI wiring scope
* 995995b feat: wire full AI-assisted showcase into AI Analyst tab
* 847500b feat: add event-aware advisory Q&A UI helper
* c0d9cc6 feat: render full AI-assisted advisory result in UI helper
* 917a86a feat: share UI evidence bundle construction
* 0e883e4 (origin/v3.1-full-ai-assisted-foundation, v3.1-full-ai-assisted-foundation) docs: clarify v3.1 baseline and live-provider status
* 010b6d5 docs: explain validation coverage and safety test scope
* f3fdf9e fix: render zh-TW event QA fallback with real newlines
* 2e9b291 fix: harden v3.1 AI provider fallbacks
* d43a45f fix: repair prompt contract zh-TW safety text
* b34bd7a fix: satisfy advisory lazy-import source guards
* ff5123f docs: document v3.1 full AI-assisted foundation
* 790b21a feat: add event-aware AI advisory Q&A backend
* dc01cc1 feat: add full AI-assisted provider foundation
* 689a81a feat: add v3.1 AI prompt safety contract
* 0d9ec53 (origin/v3.0-final-polish, v3.0-final-polish) docs: correct v3.0 baseline state and strengthen zh-TW safety boundary
* 736e972 docs(zh-TW): add v3.0 Traditional Chinese key screenshots and presentation notes
* cad4fc8 docs: tighten README safety boundary and screenshot gallery for public review
* 2473300 docs: replace README screenshots with readable v3.0 overviews and detail crops
* 9b8d05b docs: add v3.0 full-window screenshots and update gallery
* 5aceeb5 docs: add v3.0 demo script and link it from walkthrough, hub, and plan
```

## 3. Repo B Commits Relevant to Knowledge Capture / Review UI

The failed attempt to apply only `dee4d0b` is explained by this stack: `dee4d0b` modifies files introduced by earlier commits and depends on the v3.5 foundation plus v3.6 prototype/test commits.

| Commit | Subject | Files changed | Category | Likely dependencies |
| --- | --- | --- | --- | --- |
| `4e32a2d` | `docs: add knowledge capture design spec` | Adds `docs/KNOWLEDGE_CAPTURE_SPEC.md`, `docs/V3_5_KNOWLEDGE_CAPTURE_EXECUTION_PLAN.md`, `docs/examples/knowledge_capture/README.md` | Foundational docs | First knowledge capture design commit; no knowledge capture code dependency yet. |
| `88dfdb3` | `feat: add human-approved knowledge capture foundation` | Adds `modules/knowledge_capture/__init__.py`, `extractor.py`, `graph_export.py`, `rag_export.py`, `store.py`, `types.py` | Foundation code | Depends conceptually on `4e32a2d`; required by all later demo/UI/test commits. |
| `70266e9` | `test: add knowledge capture safety regressions` | Adds `tests/test_knowledge_capture_foundation.py` | Tests | Depends on `88dfdb3` modules. |
| `a10090c` | `test: harden knowledge capture approval and export safety` | Modifies `docs/KNOWLEDGE_CAPTURE_SPEC.md`, `docs/V3_5_KNOWLEDGE_CAPTURE_EXECUTION_PLAN.md`, `modules/knowledge_capture/extractor.py`, `graph_export.py`, `rag_export.py`, `store.py`, and `tests/test_knowledge_capture_foundation.py` | Safety hardening + tests + docs | Depends on `88dfdb3` and `70266e9`; should be imported with foundation, not separately. |
| `4238ed2` | `docs: add knowledge capture demo artifacts and review notes` | Adds `docs/V3_5_PR_DESCRIPTION_DRAFT.md`, `docs/V3_5_REVIEW_SUMMARY.md`, sample JSON/Markdown examples, `scripts/demo_knowledge_capture.py`, `tests/test_knowledge_capture_demo_artifacts.py`; modifies spec/example README | Demo artifacts + review docs + tests | Depends on v3.5 foundation and hardening commits. |
| `3663d2a` | `docs: add v3.6 knowledge capture review UI plan` | Adds `docs/V3_6_KNOWLEDGE_CAPTURE_REVIEW_UI_PLAN.md` | v3.6 planning docs | Depends conceptually on v3.5 but no runtime code dependency. |
| `f3ca04b` | `feat: add knowledge capture review UI prototype` | Adds `modules/ui/knowledge_capture_view.py`; modifies `docs/KNOWLEDGE_CAPTURE_SPEC.md`, `modules/ui/i18n.py`, `ui/streamlit_app.py` | UI prototype | Depends on v3.5 foundation modules. Adds the missing file that made `dee4d0b` fail. Touches Streamlit app and i18n, so it must be reviewed for conflicts. |
| `cb386ef` | `test: add knowledge capture review UI safety tests` | Adds `tests/test_ui_knowledge_capture_view.py` | UI tests | Depends on `f3ca04b` and v3.5 foundation modules. |
| `dee4d0b` | `docs: add v3.6 review and UI smoke notes` | Adds `docs/V3_6_PR_DESCRIPTION_DRAFT.md`, `docs/V3_6_REVIEW_SUMMARY.md`, `docs/V3_6_UI_MANUAL_SMOKE_CHECKLIST.md`; modifies `modules/ui/i18n.py`, `modules/ui/knowledge_capture_view.py`, `tests/test_ui_knowledge_capture_view.py` | Docs + UI/test polish | Depends on `f3ca04b` and `cb386ef`. Cannot be applied alone to Repo A. |

### v3.4 commits nearby but not strictly Knowledge Capture

Repo B's full diff from `42d2859..dee4d0b` also includes v3.4 files:

- `docs/PROVIDER_SAFETY_SMOKE_PLAN.md`
- `docs/V3_4_EXECUTION_NOTES.md`
- `docs/V3_4_VALIDATION_CHECKLIST.md`
- `scripts/validate_v3_4.ps1`
- `tests/test_ai_advisory_v3_4_contracts.py`
- `tests/test_v3_4_validation_tooling.py`

These are not required for the v3.5/v3.6 Knowledge Capture UI stack based on path history, but they may be useful if the intended v3.7 scope includes broader post-report hardening.

## 4. Missing Files in Repo A

All knowledge capture and review UI files checked below exist in Repo B but not Repo A:

| File | Repo A | Repo B |
| --- | --- | --- |
| `modules/ui/knowledge_capture_view.py` | missing | exists |
| `tests/test_ui_knowledge_capture_view.py` | missing | exists |
| `tests/test_knowledge_capture_foundation.py` | missing | exists |
| `tests/test_knowledge_capture_demo_artifacts.py` | missing | exists |
| `modules/knowledge_capture/__init__.py` | missing | exists |
| `modules/knowledge_capture/extractor.py` | missing | exists |
| `modules/knowledge_capture/graph_export.py` | missing | exists |
| `modules/knowledge_capture/rag_export.py` | missing | exists |
| `modules/knowledge_capture/store.py` | missing | exists |
| `modules/knowledge_capture/types.py` | missing | exists |
| `docs/KNOWLEDGE_CAPTURE_SPEC.md` | missing | exists |
| `docs/V3_5_KNOWLEDGE_CAPTURE_EXECUTION_PLAN.md` | missing | exists |
| `docs/V3_5_REVIEW_SUMMARY.md` | missing | exists |
| `docs/V3_5_PR_DESCRIPTION_DRAFT.md` | missing | exists |
| `docs/V3_6_KNOWLEDGE_CAPTURE_REVIEW_UI_PLAN.md` | missing | exists |
| `docs/V3_6_REVIEW_SUMMARY.md` | missing | exists |
| `docs/V3_6_PR_DESCRIPTION_DRAFT.md` | missing | exists |
| `docs/V3_6_UI_MANUAL_SMOKE_CHECKLIST.md` | missing | exists |
| `scripts/demo_knowledge_capture.py` | missing | exists |
| `docs/examples/knowledge_capture/README.md` | missing | exists |
| `docs/examples/knowledge_capture/sample_candidate_note.json` | missing | exists |
| `docs/examples/knowledge_capture/sample_approved_note.json` | missing | exists |
| `docs/examples/knowledge_capture/sample_rejected_note.json` | missing | exists |
| `docs/examples/knowledge_capture/sample_rag_export.md` | missing | exists |
| `docs/examples/knowledge_capture/sample_graph_candidates.json` | missing | exists |

This explains the earlier failed `dee4d0b` patch attempt: the patch modifies files that are absent in Repo A.

## 5. Candidate Import Stack

### Smallest safe commit stack for Knowledge Capture Foundation + Review UI

Recommended candidate stack, in order:

1. `4e32a2d docs: add knowledge capture design spec`
2. `88dfdb3 feat: add human-approved knowledge capture foundation`
3. `70266e9 test: add knowledge capture safety regressions`
4. `a10090c test: harden knowledge capture approval and export safety`
5. `4238ed2 docs: add knowledge capture demo artifacts and review notes`
6. `3663d2a docs: add v3.6 knowledge capture review UI plan`
7. `f3ca04b feat: add knowledge capture review UI prototype`
8. `cb386ef test: add knowledge capture review UI safety tests`
9. `dee4d0b docs: add v3.6 review and UI smoke notes`

This stack covers:

- Knowledge Capture foundation: commits 1-5
- Review UI: commits 6-9
- zh-TW/i18n review UI labels: commits 7 and 9 through `modules/ui/i18n.py`
- Tests: commits 3, 4, 5, 8, 9
- Docs/manual smoke checklist: commits 1, 5, 6, 9

### Alternative file stack if commit stack is too hard to apply

Manual file import would need at minimum:

- `modules/knowledge_capture/*`
- `modules/ui/knowledge_capture_view.py`
- `tests/test_knowledge_capture_foundation.py`
- `tests/test_knowledge_capture_demo_artifacts.py`
- `tests/test_ui_knowledge_capture_view.py`
- `scripts/demo_knowledge_capture.py`
- `docs/KNOWLEDGE_CAPTURE_SPEC.md`
- `docs/V3_5_*`
- `docs/V3_6_*`
- `docs/examples/knowledge_capture/*`
- The specific `modules/ui/i18n.py` keys added in v3.6
- The `ui/streamlit_app.py` integration hunk from `f3ca04b`

Manual import is riskier because `i18n.py` and `streamlit_app.py` are high-churn files and easy to partially wire incorrectly.

## 6. Risk Analysis

Answers based on Repo B file inspection and term scan:

| Question | Answer |
| --- | --- |
| Does the stack change detector / risk / decision semantics? | No evidence found. Knowledge Capture copies official Risk Level / Decision and keeps advisory boundaries. |
| Does it change RAG runtime behavior? | No runtime RAG behavior change found. Docs and script say no runtime RAG ingest. RAG export creates advisory markdown candidates only. |
| Does it change Graph runtime behavior? | No runtime Graph mutation found. Graph export creates advisory candidate JSON only. |
| Does it add live LLM calls? | No evidence found. v3.6 docs/checklist explicitly state no live LLM/API/network requirement. |
| Does it add Chroma ingestion? | No. Docs explicitly say no Chroma ingestion or embeddings. |
| Does it add embeddings execution? | No evidence found. Demo script says no Chroma/embeddings/network. |
| Does it add exploit / PoC / traffic generation? | No. Safety patterns reject unsafe content; docs repeat no exploit / PoC / traffic generation. |
| Does it add real enforcement? | No. UI copy/docs include no real firewall / WAF / EDR / account / cloud / SIEM / SOAR action. |
| Does it add auto-approval or auto-ingest? | No. Docs state no auto-approve and no auto-ingest. UI tests assert unsafe labels/no forbidden actions. |
| Does it touch final presentation package? | No. All paths are inside repository code/docs/tests/scripts. |

Main integration risks:

1. `ui/streamlit_app.py` conflict risk: `f3ca04b` modifies Streamlit wiring. Repo A already has v3.7 docs commit but same v3.3 codebase, so this may apply cleanly; still needs check.
2. `modules/ui/i18n.py` conflict risk: this file has high churn and was the first failed patch hunk from `dee4d0b`.
3. Dependency order risk: applying `dee4d0b` alone fails. The stack must be applied in order.
4. Scope creep risk: importing full `42d2859..dee4d0b` also imports v3.4 provider smoke tooling. That may be okay later, but it is not the smallest Knowledge Capture / Review UI stack.
5. Runtime write-risk: Review UI defaults to `.tmp/knowledge_capture_ui/capture_store`, not real RAG/Graph storage. Preserve that default.

## 7. Recommended Integration Method

Recommended method: **B. format-patch stack**

Why:

- This is a cross-worktree import from Repo B into Repo A.
- The earlier single-commit patch failed because dependencies were missing.
- A format-patch stack can preserve the original commit order and messages while still allowing `git apply --check` / `git am --3way` safety gates.
- It avoids relying on whether Repo A has Repo B's local branch refs/objects available.
- It makes the imported range explicit and reviewable before applying.

Not recommended:

- Applying only `dee4d0b`: already failed and is known incomplete.
- Manual file import: possible, but higher risk for `i18n.py` and `streamlit_app.py` partial wiring mistakes.
- Full `42d2859..dee4d0b` import: includes v3.4 provider-smoke docs/tests/scripts, which are not necessary for the stated Knowledge Capture / Review UI goal.

If v3.4 hardening should also be integrated, do it as a separate explicit batch after this stack.

## 8. Exact Next Commands for a Safe Import

Do not run these during this audit. They are proposed next-step commands.

### Option B: format-patch stack, v3.5/v3.6 only

```powershell
$repoA = "C:\Users\jason\Desktop\sentinel_project"
$repoB = "C:\Users\jason\Desktop\sentinel_project_review_ui"
$patchDir = Join-Path $env:TEMP "sentinel_v36_kc_patch_stack"
Remove-Item -LiteralPath $patchDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $patchDir | Out-Null

# Generate only the v3.5/v3.6 Knowledge Capture / Review UI stack.
git -C $repoB format-patch --binary --output-directory $patchDir 4e32a2d^..dee4d0b

# Inspect patch list before applying.
Get-ChildItem $patchDir -File | Sort-Object Name | Select-Object Name,Length

# Ensure Repo A is on the intended branch and clean.
git -C $repoA branch --show-current
git -C $repoA status --short --untracked-files=all

# Dry-run every patch first.
foreach ($patch in Get-ChildItem $patchDir -File | Sort-Object Name) {
  git -C $repoA apply --check --whitespace=warn $patch.FullName
  if ($LASTEXITCODE -ne 0) { throw "Patch check failed: $($patch.Name)" }
}

# If all checks pass, apply as commits preserving authors/messages.
git -C $repoA am --3way --keep-cr (Get-ChildItem $patchDir -File | Sort-Object Name | ForEach-Object { $_.FullName })
```

If `git am` stops for conflicts:

```powershell
git -C $repoA status --short --untracked-files=all
# Stop and inspect. Do not silently resolve.
# If abandoning the in-progress import after review:
# git -C $repoA am --abort
```

### Alternative: selective cherry-pick, only if Repo A has the objects

```powershell
$repoA = "C:\Users\jason\Desktop\sentinel_project"
git -C $repoA branch --show-current
git -C $repoA status --short --untracked-files=all

git -C $repoA cherry-pick 4e32a2d 88dfdb3 70266e9 a10090c 4238ed2 3663d2a f3ca04b cb386ef dee4d0b
```

Use this only if Repo A can resolve those commit hashes locally. If a cherry-pick conflicts, stop and inspect; do not continue mechanically.

### Validation after import

```powershell
python -m pytest tests/test_knowledge_capture_foundation.py tests/test_knowledge_capture_demo_artifacts.py tests/test_ui_knowledge_capture_view.py -q
python -m pytest -q tests -k "knowledge_capture or runtime or fallback or rag or event_aware or provider" --maxfail=3
python -m ruff check .
python -m mypy app.py modules tests
git diff --check
git status --short --untracked-files=all
```

If those pass and runtime is reasonable, optionally run:

```powershell
python -m pytest -q
```

## Final Recommendation

Do not import `dee4d0b` alone. Import the v3.5/v3.6 stack in order, preferably via a generated format-patch stack from `4e32a2d^..dee4d0b` with dry-run checks before applying.

The stack appears safety-compatible with Repo A's v3.7 runtime-truth direction because it keeps knowledge capture human-reviewed, advisory-only, and non-ingesting. The main practical risk is merge friction in `modules/ui/i18n.py` and `ui/streamlit_app.py`, not detector/RAG/Graph authority changes.
