---
doc_id: report.security_triage_report
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Report Structure
  - JSON Incident Report
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
  - Security Triage Report
  - report structure
  - findings
  - evidence
  - final verdict
---

# Security Triage Report

The Security Triage Report is the unified human-readable report format used by this prototype. It gives an analyst or student reviewer a compact view of what was observed, how the system interpreted it, and what simulated response decision was produced.

A report usually includes:

- Status: the current state, such as CLEAN, REVIEW, SUSPICIOUS, or ALERT.
- Risk Level: LOW, MEDIUM, or HIGH severity.
- Decision: the simulated policy result, such as ALLOW, MONITOR, or BLOCK.
- Findings: F-ID records that describe the interpreted security pattern.
- Evidence: EV-ID records that support a finding.
- AI Assist: optional advisory reasoning from LLMAssist.
- Simulation Notice: a reminder that the prototype does not perform real enforcement.

For machine-readable workflows, the same Incident can be exported as a JSON Incident Report. The human-readable report helps explain the case; the JSON export helps preserve structure for tests, indexing, or downstream tooling.

The final verdict is deterministic and policy-controlled. LLM and RAG features are advisory or explanatory only. They can help explain why the report says HIGH or MONITOR, but they do not replace the final Risk Level or Decision.
