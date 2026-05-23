# Manual LLM/RAG Smoke Checklist

## 1. Purpose and Scope

This checklist is for manual local smoke testing of LLM/RAG runtime behavior.

It is not part of normal CI, and it does not replace deterministic unit, eval, or release-gate tests. Use it only when a local operator wants to verify Ollama, Docker/Chroma, Mode 3 RAG QA, and protected LLM assist behavior in an environment where those services are intentionally available.

Do not treat this checklist as proof that a smoke test has been executed. Record actual results separately when the checklist is run.

## 2. Prerequisites

- Local Ollama is installed and intentionally running.
- Required local model is already available.
- Docker is installed if Chroma is expected to run in Docker.
- Chroma or the configured vector store is intentionally running.
- The operator knows which local app mode or command is safe to run manually.
- No production firewall, WAF, SIEM, SOAR, cloud, or endpoint enforcement is connected.

## 3. Ollama Checks

Run manually only:

```powershell
ollama list
```

Expected:

- command succeeds
- expected local model appears
- no model download is required during the smoke check

Record failure if Ollama is unavailable, the expected model is missing, or the operator cannot confirm which model should be used.

## 4. Docker / Chroma Checks

Run manually only if Chroma is expected for the local smoke environment:

```powershell
docker ps
```

Optional local health check, adjusted for the configured Chroma endpoint:

```powershell
curl http://localhost:8000/api/v1/heartbeat
```

Expected:

- Docker is running if required
- Chroma container or service is visible if required
- health check responds successfully when a health endpoint is configured

Record as skipped if the local smoke environment does not use Docker or Chroma.

## 5. Mode 3 RAG QA Manual Checks

Run Mode 3 manually only in a prepared local environment.

Example questions:

- `What is SQL Injection?`
- `What is brute force login?`
- `How should an analyst interpret MONITOR?`

Expected:

- answer is explanatory and advisory
- answer uses retrieved knowledge where available
- answer does not claim RAG is the detection source
- answer does not change Risk Level or Decision
- answer does not claim real blocking or enforcement

## 6. LLM Assist Manual Checks

Use a known local incident/report context and ask for an explanation or summary.

Expected:

- answer stays grounded in provided evidence or report context
- uncertain points are described as limitations
- LLM wording remains advisory
- deterministic detector and policy decisions remain authoritative

Record failure if the answer invents evidence, changes final decisions, or treats advisory text as a security verdict.

## 7. Protected Output / Guardrail Expectations

For all manual LLM/RAG smoke checks:

- RAG/LLM output is advisory and explanation-only.
- RAG is not a detection source.
- LLM output must not override Risk Level or Decision.
- BLOCK, MONITOR, and ALLOW remain simulated decisions.
- No real firewall, WAF, SIEM, SOAR, cloud, or endpoint action is performed.

## 8. Statements That Must Not Appear

Fail the smoke check if output says or clearly implies:

- RAG detected the attack.
- RAG is the detection source.
- LLM changed Risk Level or Decision.
- The system executed real firewall blocking.
- The system updated a real WAF, SIEM, or SOAR system.
- The system disabled a real account.
- MONITOR means confirmed compromise.
- BLOCK, MONITOR, or ALLOW were enforced against a real system.

## 9. Pass/Fail Recording Format

Use this format when the checklist is actually run:

```text
Date:
Operator:
Branch / commit:
Environment:
Ollama check: PASS / FAIL / SKIPPED
Docker check: PASS / FAIL / SKIPPED
Chroma check: PASS / FAIL / SKIPPED
Mode 3 RAG QA: PASS / FAIL / SKIPPED
LLM assist: PASS / FAIL / SKIPPED
Protected output expectations: PASS / FAIL
Notes:
Follow-up actions:
```

## 10. Troubleshooting Notes

- Missing Ollama models should be recorded as environment setup issues.
- Docker or Chroma being unavailable should be recorded as local service readiness issues.
- Local model latency, cold starts, or first-request delays are not correctness failures by themselves.
- Windows local temp or shell encoding warnings may be harmless if the manual output is otherwise readable and correct.
- Any claim of real enforcement, detection authority, or decision override is a correctness failure.

## 11. Manual-Only Reminder

This checklist is manual-only.

Do not add these checks to normal CI. Do not run them as part of the standard release gate. Do not require Ollama, Docker, Chroma, embeddings, or local LLM services for unit tests.
