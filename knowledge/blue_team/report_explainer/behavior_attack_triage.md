---
doc_id: report.behavior_attack_triage
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Findings
  - Attack Type
  - Risk Level
related_tools:
  - report_followup
  - rag_security_qa
attack_types:
  - Possible Account Compromise
  - Brute Force
severity:
  - HIGH
rule_ids: []
mitre_techniques: []
keywords:
  - behavior triage
  - brute_force_candidate
  - possible_account_compromise
  - repeated failures
  - successful login
---

# Behavior Attack Triage

Behavior-based findings describe patterns across events, not just one suspicious line.

Examples:

- brute_force_candidate: repeated authentication failures from the same source against the same target.
- possible_account_compromise: repeated authentication failures followed by a later successful login for the same source, user, and target.

Time-window aggregation looks for repeated events within a defined period. Sequence correlation checks the order of events, such as failures first and success afterward.

Repeated failures followed by success is suspicious because it can indicate password guessing, credential stuffing, or successful access after multiple attempts. The pattern becomes stronger when the same source_ip, user, and endpoint are consistent.

In v1.3, possible_account_compromise is treated as HIGH / MONITOR. HIGH reflects the seriousness of the pattern. MONITOR reflects that this is suspicious but not confirmed compromise. The prototype does not know whether the user expected the login, whether MFA succeeded, or what happened after the session began.

Analyst review is required before real containment. Review authentication logs, session activity, source reputation, user context, and any post-login behavior before escalating.
