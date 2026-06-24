# Post-Presentation Hardening Plan

Branch: `v3.3-post-presentation-hardening`

This branch is for safe work after the classroom presentation package has been frozen. It should not be merged before the report unless explicitly reviewed and approved. The final presentation claims, screenshots, speaker notes, and demo-video plan should remain stable until the presentation is complete.

## Current Strengths

- The public showcase path is deterministic and reproducible: provider-disabled deterministic fallback is the default.
- The Rule-Based Detector remains the detection authority.
- Official Risk Level and Decision are deterministic and cannot be overwritten by AI output.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions only.
- AI, RAG, Similar Cases, and Graph context are advisory-only.
- Similar Cases are explicitly not proof of compromise.
- Graph context is explicitly not a detection source.
- Event-Aware Q&A refuses unsafe questions before provider calls.
- Provider failures and unsafe provider output degrade to deterministic fallback.
- v3.2 validation covers detector/policy behavior, evidence bundles, guardrails, provider failure modes, Event-Aware Q&A safety, stale-state clearing, UI helpers, ruff, and mypy.
- Public documentation and screenshots are aligned with the provider-disabled public showcase path.

## Do Not Change Before Presentation

These items affect the frozen report narrative or classroom demo expectations and should not be changed before the presentation:

- Detection rules, detector authority, risk scoring, or decision policy.
- RAG retrieval semantics, knowledge content, Similar Case corpus, or graph builder behavior.
- Streamlit AI Analyst layout used in final screenshots or the demo video.
- Validation numbers quoted in the presentation unless a full new validation pass is intentionally rerun and the presentation is updated.
- PPTX, embedded speaker notes, final screenshots, or demo-video script after they are packaged.
- Any wording that could imply live LLM behavior in the public showcase.
- Any behavior that performs real firewall/WAF/EDR/account/cloud/SIEM/SOAR enforcement.
- Any exploit, PoC, traffic generation, load testing, or offensive automation.

## Post-Presentation Improvement Candidates

| Candidate | Type | Tests needed | Risk | Notes |
| --- | --- | --- | --- | --- |
| Add a one-command validation script | tooling-only | script smoke plus existing test gate | low | Wrap pytest, ruff, mypy, diff check, and wording scans for release prep. |
| Add a final release checklist | docs-only | markdown link/diff check | low | Keep presentation package, release gate, screenshot refresh, and safety-boundary review in one place. |
| Improve docs consistency checks | tooling/docs | focused script tests if script is committed | low | Scan for local paths, stale validation numbers, broken links, and forbidden live-provider wording. |
| Add provider manual-smoke plan | docs-only | markdown check | low | Describe how to manually test optional local/openai-compatible providers without making CI depend on them. |
| Strengthen stale-state UI regression tests | tests-only | focused UI helper tests plus full pytest | medium | Useful after the presentation; avoid destabilizing before report. |
| Negation-aware guardrail research | code/tests | unit tests for negated unsafe phrases and proof claims | medium | Important future hardening, but could alter guardrail behavior and requires careful review. |
| Larger evaluation corpus | data/tests/docs | corpus schema tests and regression expectations | medium | Useful for credibility, but may require maintaining expected outputs. |
| Artifact packaging guide | docs-only | markdown check | low | Document how to package PPTX, notes, PDF, video, and repo state without committing presentation files. |
| Optional live-provider smoke harness | tooling/tests/docs | manual-only smoke; CI disabled by default | medium-high | Must not require network/API keys in CI. Keep separate from public deterministic showcase. |
| Export polish for AI advisory sections | UI/docs/tests | export tests and markdown snapshots | medium | Useful, but changes demo output and should wait until after presentation. |

## Suggested Order

### v3.3: Safe post-presentation hardening

1. Add or refine validation helper scripts.
2. Add release/final-package checklist documentation.
3. Add documentation consistency scan for local paths, stale validation numbers, and safety-boundary language.
4. Add focused stale-state regression tests if there is a clear low-risk target.
5. Document optional live-provider manual-smoke steps without enabling live providers by default.

### v3.4: Evidence and provider hardening

1. Expand the controlled evaluation corpus with additional defensive synthetic incidents.
2. Improve guardrails for negated unsafe language and overclaiming patterns.
3. Add optional manual smoke harnesses for local/openai-compatible providers.
4. Improve advisory export formatting after UI behavior is stable.
5. Revisit screenshot and documentation showcase only after behavior is validated.

## Docs-Only Tasks

- Final release checklist.
- Artifact packaging guide.
- Provider manual-smoke guide.
- Public documentation consistency checklist.
- Updated roadmap for v3.3/v3.4 after the report.

## Tooling-Only Tasks

- `scripts/validate_release.ps1` or equivalent wrapper for pytest, ruff, mypy, `git diff --check`, forbidden wording scan, and local-path scan.
- Markdown link checker for public docs.
- Package verification script that checks required final-submission files are present without adding them to git.

## Code Changes That Require Tests

- Any guardrail or unsafe-pattern change.
- Any Event-Aware Q&A fallback change.
- Any provider-mode behavior change.
- Any stale-state clearing behavior change.
- Any export formatting change that affects generated output.
- Any RAG, Similar Case, or Graph context integration change.

## Too Risky Before The Report

- Live LLM integration or provider selector UI.
- Detector/risk/decision changes.
- RAG retrieval changes.
- Graph builder or Similar Case corpus changes.
- Streamlit layout redesign.
- Screenshot refresh or README showcase rewrite.
- Any new feature that changes the presentation story or validation numbers.

## Safety Boundary To Preserve

- Rule-Based Detector is detection authority.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated decisions only.
- AI/RAG/Similar Cases/Graph are advisory-only.
- Similar Cases are not proof of compromise.
- Graph context is not a detection source.
- No live LLM behavior should be claimed for the public showcase unless separately smoke-tested and documented.
- No real firewall/WAF/EDR/account/cloud/SIEM/SOAR enforcement.
- No exploit, PoC, traffic generation, load testing, or offensive automation.
- Human review is required.

## Presentation Package Note

The final classroom presentation package should stay outside the repository. PPTX, speaker notes, backup PDF, and demo-video helper files belong in the local submission package, not in git.
