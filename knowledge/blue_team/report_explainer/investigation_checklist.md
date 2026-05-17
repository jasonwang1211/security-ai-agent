---
doc_id: report.investigation_checklist
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Investigation
  - Evidence
  - Findings
related_tools:
  - report_followup
  - rag_security_qa
attack_types:
  - Possible Account Compromise
  - Brute Force
severity:
  - MEDIUM
  - HIGH
rule_ids: []
mitre_techniques: []
keywords:
  - investigation checklist
  - brute_force_candidate
  - possible_account_compromise
  - analyst review
  - immediate checks
---

# Investigation Checklist

Use this checklist to review suspicious authentication and report evidence without changing the prototype verdict.

For brute_force_candidate:

- Confirm failed_count, source_ip, target, and time range.
- Check whether the same source attempted multiple users.
- Compare status codes, endpoint, and user-agent if available.

For possible_account_compromise:

- Review the successful login session after repeated failures.
- Check whether source_ip, user, and target match across failures and success.
- Look for post-login activity, privilege changes, or unusual access.
- Compare with known user location and normal login timing.

Immediate checks:

- Authentication logs.
- Session records.
- Source IP reputation.
- Related endpoint access logs.

Short-term checks:

- Preserve raw logs and EV-ID evidence.
- Review account activity with an analyst.
- Consider session revocation or password reset after analyst review.

Containment options require analyst review. This prototype does not perform real enforcement.
