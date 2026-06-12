# Sentinel Project Documentation Hub

This hub is the entry point for the public documentation. The main README is intentionally short; detailed report, operation, walkthrough, validation, and screenshot materials live here.

## Start Here by Reader Type

| Reader goal | Recommended document |
|---|---|
| Professor, evaluator, or first-time reviewer | [Project report](../REPORT.md) |
| Quick GitHub overview | [Repository README](../README.md) |
| Run the Streamlit demo | [User operation guide](USER_OPERATION_GUIDE.md) |
| Follow the UI step by step | [UI walkthrough](UI_WALKTHROUGH.md) |
| Inspect screenshots and feature evidence | [Screenshot gallery](screenshots/README.md) |
| Review test and release validation | [Test report](TEST_REPORT.md) and [v2.8 release gate](v2.8_release_gate.md) |
| Understand current architecture choices | [Technical notes](TECH_NOTES.md) |
| Review code-quality findings | [Code review audit](CODE_REVIEW_AUDIT.md) |
| See roadmap and non-goals | [Roadmap](ROADMAP.md) |
| Read Traditional Chinese materials | [Traditional Chinese overview](zh-TW/README.zh-TW.md) and [Traditional Chinese report](zh-TW/PROJECT_REPORT.zh-TW.md) |

## Current Public Docs

- [Repository README](../README.md): GitHub landing page and fast orientation.
- [Project report](../REPORT.md): Formal English project report.
- [User operation guide](USER_OPERATION_GUIDE.md): Setup, launch, operation, and troubleshooting.
- [UI walkthrough](UI_WALKTHROUGH.md): Step-by-step demo walkthrough.
- [Screenshot gallery](screenshots/README.md): Feature gallery for English and Traditional Chinese screenshots.
- [Test report](TEST_REPORT.md): Validation summary.
- [v2.8 release gate](v2.8_release_gate.md): Release gate evidence.
- [Technical notes](TECH_NOTES.md): Current v2.8 technical overview.
- [Roadmap](ROADMAP.md): Current baseline, next work, and non-goals.
- [Code review audit](CODE_REVIEW_AUDIT.md): Public code review audit.

## Screenshot Sets

- English UI screenshots: [screenshots/en/](screenshots/en/)
- Traditional Chinese UI screenshots: [screenshots/zh-TW/](screenshots/zh-TW/)
- Root docs/screenshots PNG files are legacy compatibility references and should not be the primary source for English public docs.

## Historical Archive

Historical specifications, older release notes, and previous planning documents are stored under [archive/](archive/). They are useful for development history, but they are not the main entry point for v2.8.

## Safety Boundary to Preserve

All public documentation should preserve this project positioning:

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated decisions only.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph provide advisory context only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit code, PoC generation, traffic generation, or offensive automation is provided.
- Human review is required.
