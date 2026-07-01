# Post-Final Audit and v3.7 Planning

Date: 2026-06-30

Scope: post-final read-only audit and v3.7 planning. This report intentionally does not merge branches, change runtime code, update tests, or change configuration.

## 1. Current Git Branch and Working Tree State

Observed before creating this report:

```text
branch: v3.3-post-presentation-hardening
HEAD: 42d2859 docs: add post-presentation hardening plan
working tree status:
?? classroom_runtime_llm_fallback_check.md
```

Notes:

- The existing untracked `classroom_runtime_llm_fallback_check.md` is the classroom runtime truth report from the final presentation check.
- This audit creates one additional file: `docs/POST_FINAL_AUDIT_v3.7.md`.
- No merge, rebase, cherry-pick, reset, tag, or release action was performed during this audit.

## 2. Branches Relevant to Post-Final Integration

Relevant local branches observed:

| Branch | Current role / interpretation |
| --- | --- |
| `main` | Public merged baseline. Remote `origin/main` points at v3.0 final polish merge. |
| `v3.0-final-polish` | Final presentation/documentation polish baseline. |
| `v3.1-full-ai-assisted-foundation` | Backend provider contracts, prompt contract, Full AI-assisted contract, Event-Aware Q&A backend. |
| `v3.2-full-ai-assisted-showcase` | Streamlit AI Analyst tab wiring for Full AI-assisted fallback and Event-Aware Q&A. Remote branch exists. |
| `v3.3-post-presentation-hardening` | Current branch; contains post-presentation hardening plan. |
| `v3.4-post-report-hardening-start` | Post-report safety regressions and provider smoke guidance. |
| `v3.5-human-approved-knowledge-capture` | Human-approved knowledge capture foundation and demo artifacts. |
| `v3.6-knowledge-capture-review-ui` | Knowledge capture review UI prototype and review/smoke docs. |
| `safety/pre-vnext-codex-checkpoint` | Points at same commit as current `v3.3-post-presentation-hardening`. |

Recent branch topology shows v3.4, v3.5, and v3.6 are linear descendants after v3.3 in local history:

```text
v3.3 42d2859 docs: add post-presentation hardening plan
v3.4 0575360 test: add v3.4 post-report safety regressions
v3.5 4238ed2 docs: add knowledge capture demo artifacts and review notes
v3.6 dee4d0b docs: add v3.6 review and UI smoke notes
```

Recommended v3.7 planning should treat v3.4-v3.6 as integration candidates, not automatically merge them without a dedicated conflict/risk pass.

## 3. Current Test Status

Full suite was not run for this first audit pass because the user requested planning and allowed targeted tests if full suite is expensive.

Targeted command run with pytest cache disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider `
  tests/test_ai_advisory_llm_provider.py `
  tests/test_ai_advisory_full_ai_assisted.py `
  tests/test_ai_advisory_event_qa.py `
  tests/test_ui_full_ai_assisted_view.py `
  tests/test_ui_event_qa_view.py `
  tests/test_lazy_rag_startup.py `
  tests/test_event_followup.py `
  tests/test_incident_followup.py `
  tests/test_report_followup.py `
  tests/test_rag_qa_controlled_runtime.py `
  tests/test_rag_intent.py `
  --maxfail=3
```

Result:

```text
181 passed in 12.83s
```

Coverage represented by this targeted set:

- provider-disabled fallback
- provider contract behavior
- Full AI-assisted fallback and guardrail behavior
- Event-Aware Q&A safe/unsafe behavior
- lazy RAG startup checks
- deterministic event/incident follow-up helpers
- report follow-up guardrails
- controlled RAG runtime behavior
- RAG intent behavior

What this does not prove:

- full project release-gate status
- live Ollama/provider quality
- live Chroma retrieval quality on this machine
- production IDS/IPS effectiveness
- real enforcement readiness

## 4. Current Runtime Mode Documentation Accuracy

The most accurate current runtime description is **mixed runtime**:

- Full AI-Assisted Advisory Result can run through provider-disabled deterministic fallback.
- Event-Aware Q&A safe questions can run through provider-disabled deterministic fallback.
- Event-Aware Q&A unsafe questions are refused before provider call.
- Active event/auth follow-up can be deterministic.
- Natural/contextual follow-up may enter RAG follow-up helpers.
- RAG / Knowledge Q&A true knowledge answering depends on RAG runtime readiness: ChatOllama, Chroma, embeddings, and available local model/runtime.
- Current config:
  - `MODEL_NAME = "qwen2.5:7b"`
  - `AGENT_MODEL_NAME = "gemma4:e4b"`
  - `CHROMA_PATH = "./chroma_db"`
  - `EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"`

Documentation accuracy status:

- `README.md` is mostly accurate because it scopes provider-disabled fallback to the public Streamlit showcase and CI path.
- `docs/TECH_NOTES.md` is mostly accurate, but v3.7 should make the mixed runtime summary more explicit near the top.
- `docs/ROADMAP.md` has at least one stale/broad statement that can imply live LLM integration is still fully out of scope and deterministic fallback only. That was true for earlier branches but is no longer the cleanest wording after v3.1/v3.2 provider contracts.
- Historical files under `docs/archive/` and v2.9 release docs may say "no live LLM client is wired yet". That is acceptable for historical documents if they are clearly treated as historical, but they should not be used as current runtime truth.

## 5. Files That Still Imply the Whole Project Is Provider-Disabled / No LLM / No RAG

These are candidates for v3.7 wording cleanup, not necessarily bugs:

| File | Concern |
| --- | --- |
| `docs/ROADMAP.md` | Contains "Optional live LLM client integration remains out of scope (deterministic fallback only)." This is too broad after v3.1 provider contracts and v3.2 UI wiring. Better: public showcase defaults to fallback; optional provider contracts exist; live-provider demo remains manually gated. |
| `docs/zh-TW/v3.0_presentation_notes.zh-TW.md` | Says the build has no live LLM client. This may be fine as v3.0 presentation notes, but should be clearly historical if linked from current docs. |
| `docs/v2.9_release_notes.md` and `docs/v2.9_release_gate.md` | Historical v2.9 docs say no live LLM client is wired. Acceptable historically; avoid presenting as current v3.7 runtime truth. |
| `modules/ui/i18n.py` old AI Analyst Brief labels | Some older labels say "Deterministic advisory / no LLM". This is correct for deterministic AI Analyst Brief panels but can be confusing if read as the whole AI Analyst tab. Keep labels scoped to the specific panel. |
| `docs/v2.9_evidence_grounded_ai_brief_plan.md` | Planning/history file says no LLM call and deterministic fallback. Historical; avoid as current top-level docs. |

## 6. Files That Correctly Describe Mixed Runtime

| File | Accurate wording observed |
| --- | --- |
| `README.md` | States v3.2 public showcase uses provider-disabled deterministic fallback while v3.1/v3.2 provider contracts are optional and disabled by default; CI does not require live LLM/API key/Ollama/Chroma/embeddings/network. |
| `REPORT.md` | States v3.1 provider contracts are backend foundation work and live-provider quality/availability require separate manual smoke testing. |
| `docs/TECH_NOTES.md` | Describes v3.2 UI wiring, provider disabled default, Event-Aware Q&A using current bundle, and Knowledge Q&A/RAG as advisory. Needs a stronger top-level mixed-runtime summary. |
| `docs/USER_OPERATION_GUIDE.md` | Has an "If RAG / Ollama / Chroma / Embedding Is Unavailable" section, which correctly frames unavailable fallback behavior. |
| `docs/UI_WALKTHROUGH.md` | Notes provider-disabled deterministic fallback for v3.2 panels and separately states deterministic analysis still stands if Ollama/Chroma/embedding dependencies are unavailable. |
| `classroom_runtime_llm_fallback_check.md` | Most precise runtime truth from classroom check: final label was MIXED. It is currently untracked. |

## 7. Code Paths

### Full AI-Assisted

Primary files/functions:

- `ui/streamlit_app.py`, AI Analyst tab around `render_full_ai_assisted_panel_html(...)`.
- `modules/ui/full_ai_assisted_view.py::render_full_ai_assisted_panel_html(...)`.
- `modules/ui/full_ai_assisted_view.py::build_full_ai_assisted_result_from_cli_state(...)`.
- `modules/ai_advisory/full_ai_assisted.py::run_full_ai_assisted(...)`.
- `modules/ai_advisory/llm_provider.py::build_default_provider(...)`.

Runtime behavior:

- Builds an `EvidenceGroundingBundle` from current deterministic UI state plus optional already-loaded RAG answer, similar case result, and graph snapshot.
- Calls `run_full_ai_assisted(...)`.
- `run_full_ai_assisted(...)` selects injected provider or `build_default_provider()`.
- Default provider mode is `disabled` unless environment enables `local` or `openai_compatible`.
- It calls `selected_provider.generate(...)` once, then falls back safely if disabled, unavailable, invalid, unsafe, or exception-raising.
- Official Risk Level / Decision are copied from deterministic bundle and cannot be overwritten by provider output.

### Event-Aware Q&A

Primary files/functions:

- `ui/streamlit_app.py::render_event_aware_qa_panel(...)`.
- `modules/ui/event_qa_view.py::build_event_aware_qa_result_from_cli_state(...)`.
- `modules/ai_advisory/event_qa.py::answer_event_aware_question(...)`.

Runtime behavior:

- Uses the active `EvidenceGroundingBundle` only.
- Unsafe questions are refused before provider call through `_unsafe_question_reason(...)`.
- Safe questions select injected provider or default provider.
- Default provider disabled path returns deterministic event-aware answer with `llm_status = "not_used_deterministic_fallback"`.
- Provider exceptions return unavailable fallback.
- Similar Cases are advisory only and not proof; Graph is advisory only and not detection source.

### Follow-up / 追問

Primary files/functions:

- `ui/streamlit_app.py::run_followup_question(...)`.
- `modules/agent.py::SecurityAgent._handle_followup(...)`.
- `modules/event_followup.py::answer_event_followup(...)`.
- `modules/incident_followup.py::answer_incident_followup(...)`.
- `modules/rag_qa.py::RAGQA.handle_natural_followup(...)`.

Runtime behavior:

- Active-context follow-up first tries deterministic event/incident helpers.
- If those do not answer and the query is natural/contextual follow-up, it may call RAG follow-up helpers through `rag_qa.handle_natural_followup(...)`.
- Since `rag_qa` is `LazyRAGQA`, RAG runtime is imported/initialized only when a RAG-facing method is used.
- This path is mixed: deterministic for active-context answers, RAG/LLM-dependent for broader natural/contextual follow-up.

### RAG / Knowledge Q&A

Primary files/functions:

- `ui/streamlit_app.py::run_knowledge_question(...)`.
- `modules/agent.py::SecurityAgent.build_rag_answer(...)`.
- `modules/lazy_rag.py::LazyRAGQA`.
- `modules/rag_qa.py::RAGQA`.

Runtime behavior:

- Streamlit forces Knowledge Q&A through the existing KnowledgeQASkill/RAG path.
- `SecurityAgent.build_rag_answer(...)` returns KB unavailable if `rag_qa.is_ready()` is false.
- `RAGQA._initialize_components(...)` initializes embeddings, `ChatOllama(model=MODEL_NAME)`, query planner, and `Chroma` if available.
- Real RAG answers therefore depend on RAG runtime readiness.
- Controlled retrieval tests can pass without proving the classroom live RAG runtime is ready.

### Legacy LLMAssist

Primary files/functions:

- `modules/llm_assist.py::LLMAssist`.

Runtime behavior:

- `LLMAssist._initialize_llm()` lazily imports `ChatOllama` and uses `AGENT_MODEL_NAME`.
- `judge_suspicious_behavior(...)` and `explain_alert(...)` return fallback when unavailable/invalid.
- This is not the v3.1 provider abstraction, but it is still a live-model-capable legacy advisory path.

## 8. Recommended v3.7 Scope

Recommended v3.7 theme: **Runtime Truth and Post-Final Integration Hardening**.

Suggested scope:

1. Merge/integrate only after a dedicated branch audit:
   - v3.4 post-report hardening
   - v3.5 human-approved knowledge capture foundation
   - v3.6 knowledge capture review UI
2. Normalize documentation around mixed runtime:
   - public showcase: provider-disabled deterministic fallback
   - optional v3.1/v3.2 provider contracts: disabled by default; live-provider manual smoke required
   - RAG / Knowledge Q&A: depends on RAG runtime readiness
   - active-context follow-up: deterministic first; natural/contextual can enter RAG path
3. Add a lightweight runtime status/diagnostic helper, if needed, that reports:
   - provider mode
   - Ollama process/port status without invoking `ollama ps`
   - Chroma path presence
   - RAG readiness state
   - current model names from config
4. Avoid starting Ollama as part of passive checks. The classroom check showed `ollama ps` can auto-start Ollama on Windows.
5. Add tests/documentation that prevent overclaiming:
   - no doc should imply all AI paths are provider-disabled fallback
   - no doc should imply RAG answers work without RAG runtime readiness
   - no UI label should imply live LLM unless provider status confirms it
6. Consider a `docs/RUNTIME_MODES.md` or `docs/V3_7_RUNTIME_TRUTH.md` page and link it from README/TECH_NOTES.

## 9. Recommended Files to Update in v3.7

Documentation candidates:

- `README.md`
- `REPORT.md`
- `docs/TECH_NOTES.md`
- `docs/ROADMAP.md`
- `docs/USER_OPERATION_GUIDE.md`
- `docs/UI_WALKTHROUGH.md`
- `docs/zh-TW/README.zh-TW.md`
- `docs/zh-TW/PROJECT_REPORT.zh-TW.md`
- New: `docs/RUNTIME_MODES.md` or `docs/V3_7_RUNTIME_TRUTH.md`

Testing candidates:

- `tests/test_lazy_rag_startup.py`
- `tests/test_ui_full_ai_assisted_view.py`
- `tests/test_ui_event_qa_view.py`
- `tests/test_agent_skill_orchestrator.py`
- `tests/test_rag_qa_controlled_runtime.py`
- Possible new doc/runtime assertion tests for wording or status helpers.

Runtime/helper candidates, only if v3.7 chooses implementation:

- `modules/runtime_status.py` or `modules/ui/runtime_status_view.py`
- `ui/streamlit_app.py` only for a small status panel if needed
- `modules/ui/i18n.py` only for status labels

Branches to inspect before integration:

- `v3.4-post-report-hardening-start`
- `v3.5-human-approved-knowledge-capture`
- `v3.6-knowledge-capture-review-ui`

## 10. Risks / Do-Not-Change List

Do not casually change:

- detector semantics
- risk scoring
- deterministic decision policy
- BLOCK / MONITOR / ALLOW simulated-only boundary
- ToolPolicy enforcement
- RAG retrieval semantics
- Chroma DB contents or ingest behavior
- graph builder/provenance semantics
- approved similar-case corpus semantics
- case draft write behavior
- knowledge capture approval gate semantics
- provider guardrails that block verdict override, Similar Cases-as-proof, Graph-as-detection-source, enforcement, exploit/PoC/traffic-generation wording

Key risks:

1. Documentation overclaiming:
   - Saying "no live LLM" for the whole project is now inaccurate.
   - Saying "live LLM works" is also inaccurate without manual smoke.
   - Correct wording is mixed runtime with provider-disabled public showcase.
2. Passive runtime checks can mutate environment:
   - `ollama ps` can auto-start Ollama on Windows.
   - v3.7 diagnostics should avoid CLI commands that start background services.
3. Branch integration risk:
   - v3.5/v3.6 introduce knowledge capture foundation/UI review queue. They should remain human-approved, non-ingesting, and non-mutating until deliberately wired.
4. RAG readiness ambiguity:
   - Controlled RAG tests do not prove classroom Chroma/Ollama/model readiness.
5. UI state contamination:
   - v3.2 already fixed stale Knowledge Q&A leaking into new analysis; v3.7 should preserve this behavior.

## Recommended v3.7 First Milestones

1. **v3.7-A Runtime Truth Docs**
   - Add a concise runtime modes document.
   - Update README/TECH_NOTES/ROADMAP wording.
   - Explicitly distinguish provider-disabled Full AI/Event-QA fallback from RAG/Knowledge Q&A runtime dependency.

2. **v3.7-B Safe Runtime Status Probe**
   - Add a pure helper that checks env/config/path state without starting Ollama or Chroma.
   - Avoid `ollama ps`.
   - Tests should mock process/port checks.

3. **v3.7-C Branch Integration Audit**
   - Inspect v3.4/v3.5/v3.6 diffs against current branch.
   - Decide merge order and conflict plan.
   - Do not merge until validation plan is clear.

4. **v3.7-D Knowledge Capture Merge Prep**
   - If v3.5/v3.6 are integrated, keep runtime RAG/Graph mutation deferred.
   - Preserve human approval and final safety validation.

5. **v3.7-E Release Gate**
   - Run full pytest, ruff, mypy, diff check, secret scan if available.
   - Add a release/readiness note only after validation.
