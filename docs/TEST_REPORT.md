# Test Report

This document summarizes validation evidence for the current demo-ready Sentinel Project state. It is a public validation summary and does not change runtime behavior.

## Validation Philosophy

The tests are organized around the safety boundary:

- Rule-Based Detector is the detection authority.
- Risk Level and Decision are deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` are simulated.
- RAG, LLM, AI Analyst Brief, and Evidence Gap provide advisory context only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, proof-of-concept, or traffic generation is provided.
- Human review is required.

## Current Validation Snapshot

| Check | Result |
|---|---|
| `python -m pytest` | Passed: `1168 passed` |
| `python -m ruff check .` | Passed |
| `python -m mypy app.py modules tests` | Passed |
| `git diff --check` | Passed |
| `gitleaks detect --source . --verbose --redact --gitleaks-ignore-path .gitleaksignore` | Passed; false-positive handling documented in `.gitleaksignore` |
| Screenshot refresh | Completed |

The current validation confirms language-aware output, Lazy RAG startup behavior, AI advisory panels, RAG prompt language policy, HTTP/2 safe synthetic demo behavior, and screenshot synchronization.

## Coverage Areas

Automated tests cover:

- Detection rule loading and rule-based detector behavior.
- Log ingestion and authentication incident correlation.
- Evidence, finding, incident, and report schemas.
- Deterministic risk and decision behavior.
- Controller routing, ToolPolicy, skill catalog, and skill wrappers.
- RAG routing, retrieval planning, controlled source assembly, answer guardrails, and controlled runtime behavior.
- CVE / CVSS terminology normalization and Resource Exhaustion knowledge routing.
- AI Analyst Brief backend and UI view helpers.
- Evidence Gap Analyzer backend and UI view helpers.
- Approved Similar Case retrieval and no-override boundary wording.
- Relationship graph builder, lookup, export, and UI view helpers.
- Case Draft, Case Memory, Export Report, route/policy, performance, and report section helpers.
- Streamlit UI helper parsing without importing Streamlit in pure helper tests.
- Demo scenarios and Lazy RAG startup regression checks.
- Output language policy normalization, prompt instruction selection, and lightweight import behavior.
- HTTP/2 launcher short-preview behavior while preserving full synthetic input on load.

## What Tests Do Not Prove

The tests do not prove production security effectiveness. They do not prove real-world exploit prevention, real firewall blocking, real EDR containment, real account action, real cloud enforcement, or SIEM/SOAR remediation.

They prove the prototype behavior and safety boundaries expected by this demo implementation.

## Manual Review Evidence

Manual review evidence is represented by the current screenshot gallery and release-gate documentation:

- [screenshots/README.md](screenshots/README.md)
- [v2.8_release_gate.md](v2.8_release_gate.md)

## Conclusion

The current validation evidence supports the demo-ready claim: deterministic security authority remains intact, advisory AI/RAG features are bounded, and the user-facing documentation and screenshots match the current console workflow.
