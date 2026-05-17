---
doc_id: report.reading_the_report
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Evidence
  - Findings
  - Quick Verdict
related_tools:
  - report_followup
  - rag_security_qa
attack_types:
  - Possible Account Compromise
  - Brute Force
severity:
  - LOW
  - MEDIUM
  - HIGH
rule_ids: []
mitre_techniques: []
keywords:
  - read report
  - Security Triage Report
  - Evidence
  - Findings
  - Quick Verdict
---

# Reading the Security Triage Report

A Security Triage Report summarizes what the prototype observed and how the deterministic triage logic described it.

Key sections:

- Quick Verdict: the current status, Risk Level, and Decision.
- Summary: a short explanation of the suspicious behavior or benign outcome.
- Evidence: concrete EV-ID items used by the report, such as failed_count, time_window, or success_after_failures.
- Findings: F-ID items that connect evidence to a security interpretation.
- Risk Level: severity of the observed pattern.
- Decision: the simulated training decision, such as ALLOW, MONITOR, or BLOCK.
- AI Assist: advisory text only. It does not override the final deterministic decision.
- Simulation Notice: reminder that the prototype does not perform real enforcement.

Report-aware follow-up should explain the existing Incident, Finding, and Evidence. It should not invent new evidence or re-judge the verdict.
