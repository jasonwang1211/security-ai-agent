---
id: behavior_attack_triage
authority: explainer
question_intents:
  - explain_finding
  - why_risk
  - why_decision
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
