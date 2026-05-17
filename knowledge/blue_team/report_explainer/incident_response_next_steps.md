---
doc_id: report.incident_response_next_steps
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Incident Response
  - Next Steps
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
  - next steps
  - investigation
  - analyst review
  - authentication logs
  - incident response
---

# Incident Response Next Steps

Use these steps after a Security Triage Report identifies suspicious behavior such as possible_account_compromise.

Start with the report:

- Review the Finding ID and all referenced Evidence IDs.
- Confirm EV-001 failed_count, EV-002 time_window, and EV-003 success_after_failures if present.
- Check whether the same source_ip attempted other users.
- Check whether the same user had failures or success from other locations.

Review related data:

- Authentication logs.
- Session records.
- Identity provider events.
- Endpoint or web access logs after the successful login.
- Source IP reputation or known testing ranges.

Preserve evidence:

- Keep raw logs.
- Preserve timestamps, source_ip, user, endpoint, and status fields.
- Record what was reviewed and what remains unknown.

Containment options such as session revocation, password reset, MFA reset, IP blocking, or account disablement require analyst review and approved operational process.

Escalate if additional signals appear, such as unusual post-login activity, privilege changes, impossible travel, suspicious downloads, or repeated attempts against multiple users.

This prototype does not perform real actions. It provides a structured training report and deterministic evidence context.
