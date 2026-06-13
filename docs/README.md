# Documentation Hub

This hub is the main navigation page for Sentinel Project documentation. The root README is the GitHub landing page; this file tells each reader where to go next.

## Start Here

| Reader | Best entry point |
|---|---|
| First-time GitHub visitor | [Repository README](../README.md) |
| Professor or project evaluator | [Project report](../REPORT.md) |
| Portfolio or interview reviewer | [Repository README](../README.md), [project report](../REPORT.md), and [UI walkthrough](UI_WALKTHROUGH.md) |
| Demo operator | [User operation guide](USER_OPERATION_GUIDE.md) and [UI walkthrough](UI_WALKTHROUGH.md) |
| Technical reviewer | [Technical notes](TECH_NOTES.md) and [Code review audit](CODE_REVIEW_AUDIT.md) |
| Validation reviewer | [Test report](TEST_REPORT.md) and [v2.8 release gate](v2.8_release_gate.md) |
| Traditional Chinese reader | [zh-TW overview](zh-TW/README.zh-TW.md) and [zh-TW project report](zh-TW/PROJECT_REPORT.zh-TW.md) |
| Screenshot reviewer | [Screenshot feature gallery](screenshots/README.md) |

## For Professors, Reviewers, and Portfolio Readers

Read these in order:

1. [Repository README](../README.md) for the project summary, screenshots, and safety boundary.
2. [Project report](../REPORT.md) for formal motivation, architecture, scope, safety boundary, validation, and future work.
3. [Screenshot feature gallery](screenshots/README.md) for visual evidence of the Streamlit analyst console.
4. [Test report](TEST_REPORT.md) and [v2.8 release gate](v2.8_release_gate.md) for recorded validation evidence.

## For Demo Operators

Use these documents when preparing or running the demo:

- [User operation guide](USER_OPERATION_GUIDE.md): environment assumptions, launch commands, mode selection, lazy RAG behavior, troubleshooting, and safety reminders.
- [UI walkthrough](UI_WALKTHROUGH.md): step-by-step Streamlit demo flow with what to click, what should appear, what to say, and the safety note for each major panel.
- [Screenshot feature gallery](screenshots/README.md): quick visual reference for each feature area.

## For Technical Review

Use these documents when evaluating architecture and code quality:

- [Technical notes](TECH_NOTES.md): current v2.8 technical overview.
- [Code review audit](CODE_REVIEW_AUDIT.md): code review and public-readiness findings.
- [Roadmap](ROADMAP.md): current baseline, short-term polish, v2.9 candidates, long-term ideas, and non-goals.

## For Validation Evidence

Use these documents when checking whether the demo-ready state was validated:

- [Test report](TEST_REPORT.md)
- [v2.8 release gate](v2.8_release_gate.md)
- [Screenshot feature gallery](screenshots/README.md)

The validation summary is a recorded release-gate snapshot. A documentation-only patch does not imply pytest, ruff, mypy, or gitleaks were rerun unless explicitly stated.

## For Traditional Chinese Readers

Traditional Chinese materials are intentionally kept under [zh-TW/](zh-TW/) instead of mixing full bilingual text into every English public document.

- [Traditional Chinese overview](zh-TW/README.zh-TW.md)
- [Traditional Chinese project report](zh-TW/PROJECT_REPORT.zh-TW.md)

Traditional Chinese UI screenshots are under [screenshots/zh-TW/](screenshots/zh-TW/).

## Screenshot Sets

- English UI screenshots: [screenshots/en/](screenshots/en/)
- Traditional Chinese UI screenshots: [screenshots/zh-TW/](screenshots/zh-TW/)
- Root docs/screenshots PNG files are legacy compatibility references and should not be the primary source for English public docs.

## Historical Documents

Historical specifications, older release notes, planning artifacts, and previous technical notes are stored under [archive/](archive/). They are useful for project history, but they are not the main entry point for the current v2.8 demo-ready state.

Do not link public landing material to local-only demo helper files.

## Safety Boundary To Preserve

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated decisions only.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph provide advisory context only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit code, PoC generation, traffic generation, or offensive automation is provided.
- Human review is required.
