---
id: ai_assist_limitations
authority: explainer
question_intents:
  - ai_assist_disagreement
  - why_decision
---

# AI Assist Limitations

LLMAssist is advisory only. It may help explain evidence, summarize suspicious behavior, or suggest a risk/action pair for review, but it cannot override the final deterministic verdict.

Important boundaries:

- LLMAssist must cite Evidence IDs when making suspicious claims.
- It should explain the current Incident, not invent new evidence.
- It may suggest a higher concern, but final Risk Level and Decision remain policy-controlled.
- It should not downgrade a deterministic HIGH finding to LOW or MEDIUM.
- It should not unilaterally turn MONITOR into BLOCK as if it were enforcement.

LLMGuardrails validate advisory output before it is trusted as report context. Guardrails check evidence references, downgrade attempts, unilateral BLOCK recommendations, unknown attack types, and confidence sanity.

If LLM output is invalid, unsafe, or unsupported, the deterministic result remains. The report can still show that AI Assist was unavailable or rejected, but the final verdict is unchanged.

Treat LLMAssist as a reviewer aid. It is not the source of truth for enforcement or final triage policy.
