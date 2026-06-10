"""Approval-gated local case draft capture helpers.

The helpers in this module write isolated markdown drafts only after explicit
approval. They do not ingest knowledge, update Chroma, mutate graph state, or
perform real enforcement actions.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from modules.event_followup import ActiveEventContext
from modules.incident_followup import ActiveAuthIncidentContext

DEFAULT_CASE_DRAFT_DIR = Path("workbench/case_drafts")
DRAFT_SCHEMA_VERSION = "v2.5-case-draft1"
DRAFT_TYPE = "incident_case_capture"
DRAFT_REVIEW_STATUS = "draft_pending_human_review"
DRAFT_INGEST_STATUS = "not_ingested"
DRAFT_SOURCE_SKILL = "DraftCaseCaptureSkill"
PENDING_CASE_DRAFT_KEY = "pending_case_draft_request"

ContextType = Literal["active_event", "active_auth_incident"]

SECRET_WARNING = "Secret-like value was redacted before draft rendering."
PII_WARNING = "Possible identifying information is present and requires human review; no comprehensive anonymization is claimed."
DUPLICATE_WARNING = "A case draft with the same stable fingerprint already exists; no file was overwritten."

_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(
        r"(?i)\b(api[_-]?key|password|passwd|pwd|session[_-]?id|session|cookie|token|secret)\s*[:=]\s*[\"']?[^\s\"']+"
    ),
]
_PII_PATTERNS = [
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?i)\buser(?:name)?\s*[:=]\s*[^\s,;]+"),
]


class PendingCaseDraftRequest(BaseModel):
    """Frozen enough case facts captured at draft-request time."""

    source_context_type: ContextType
    title: str
    captured_at: str
    fingerprint: str
    safe_context: dict[str, Any]
    safety_warnings: list[str] = Field(default_factory=list)


class CaseDraftWriteResult(BaseModel):
    """Result of an approved draft-write attempt."""

    created: bool
    duplicate: bool = False
    draft_path: str | None = None
    fingerprint: str
    warnings: list[str] = Field(default_factory=list)


def build_pending_case_draft_request(
    state: dict[str, Any],
    user_text: str,
    *,
    now: datetime | None = None,
) -> PendingCaseDraftRequest | None:
    """Capture the current active event or incident context for later approval."""

    context_kind = state.get("active_context_kind")
    if context_kind == "event" and isinstance(state.get("active_event_context"), ActiveEventContext):
        return _event_context_to_pending(state["active_event_context"], user_text, now=now)
    if context_kind == "incident" and isinstance(
        state.get("active_incident_context"), ActiveAuthIncidentContext
    ):
        return _incident_context_to_pending(state["active_incident_context"], user_text, now=now)
    return None


def write_case_draft(
    pending: PendingCaseDraftRequest,
    *,
    output_dir: str | Path | None = None,
    now: datetime | None = None,
) -> CaseDraftWriteResult:
    """Write one isolated markdown draft, unless a duplicate already exists."""

    directory = _safe_output_dir(output_dir)
    filename = _draft_filename(pending)
    draft_path = directory / filename
    display_path = _display_path(draft_path)
    warnings = list(pending.safety_warnings)

    directory.mkdir(parents=True, exist_ok=True)
    if draft_path.exists():
        return CaseDraftWriteResult(
            created=False,
            duplicate=True,
            draft_path=display_path,
            fingerprint=pending.fingerprint,
            warnings=_dedupe([*warnings, DUPLICATE_WARNING]),
        )

    draft_path.write_text(_render_markdown(pending, now=now), encoding="utf-8")
    return CaseDraftWriteResult(
        created=True,
        draft_path=display_path,
        fingerprint=pending.fingerprint,
        warnings=warnings,
    )


def _event_context_to_pending(
    context: ActiveEventContext,
    user_text: str,
    *,
    now: datetime | None,
) -> PendingCaseDraftRequest:
    warnings: list[str] = []
    payload_evidence = _sanitize_text(context.original_input, warnings)
    matched_signatures = {
        str(attack_type): [_sanitize_text(signature, warnings) for signature in signatures]
        for attack_type, signatures in context.matched_signatures.items()
    }
    safe_context = {
        "source_origin": "payload_analysis",
        "attack_types": list(context.attack_types),
        "rule_ids": list(context.rule_ids),
        "rule_sources": list(context.rule_sources),
        "matched_signatures": matched_signatures,
        "risk_level": context.risk_level,
        "decision": context.decision,
        "simulated_decision": True,
        "payload_evidence": payload_evidence,
        "payload_sha256": _sha256_text(context.original_input),
    }
    warnings.extend(_pii_warnings(json.dumps(safe_context, ensure_ascii=False, sort_keys=True)))
    title = _title_from_context(
        "Case draft",
        [*context.attack_types] or ["payload event"],
        context.decision,
        user_text,
        warnings,
    )
    return _pending_from_safe_context(
        source_context_type="active_event",
        title=title,
        safe_context=safe_context,
        warnings=warnings,
        now=now,
    )


def _incident_context_to_pending(
    context: ActiveAuthIncidentContext,
    user_text: str,
    *,
    now: datetime | None,
) -> PendingCaseDraftRequest:
    incident = context.incident
    evidence_ids = sorted(incident.evidence_bundle.available_ids)
    finding_ids = [finding.id for finding in incident.findings]
    warnings: list[str] = []
    raw_source_log_path = _extract_source_log_path(context.rendered_summary)
    source_log_path = (
        _sanitize_text(raw_source_log_path, warnings)
        if raw_source_log_path is not None
        else None
    )
    safe_context = {
        "source_origin": _sanitize_text(context.source, warnings),
        "incident_id": incident.id,
        "incident_title": _sanitize_text(incident.title, warnings),
        "attack_type": _sanitize_text(incident.attack_type, warnings) if incident.attack_type else None,
        "risk_level": incident.risk_level,
        "decision": incident.decision,
        "simulated_decision": True,
        "evidence_ids": evidence_ids,
        "finding_ids": finding_ids,
        "finding_types": [finding.finding_type for finding in incident.findings],
        "source_log_path": source_log_path,
        "graph_provenance": "explicit_current_incident_graph_facts_only",
    }
    warning_source = json.dumps(incident.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    if source_log_path:
        warning_source += f" {source_log_path}"
    warnings.extend(_scan_warnings(warning_source))
    title = _title_from_context(
        "Case draft",
        [incident.id, incident.attack_type or incident.title],
        incident.decision,
        user_text,
        warnings,
    )
    return _pending_from_safe_context(
        source_context_type="active_auth_incident",
        title=title,
        safe_context=safe_context,
        warnings=warnings,
        now=now,
    )


def _pending_from_safe_context(
    *,
    source_context_type: ContextType,
    title: str,
    safe_context: dict[str, Any],
    warnings: list[str],
    now: datetime | None,
) -> PendingCaseDraftRequest:
    fingerprint = _context_fingerprint(source_context_type, safe_context)
    return PendingCaseDraftRequest(
        source_context_type=source_context_type,
        title=title,
        captured_at=_utc_iso(now),
        fingerprint=fingerprint,
        safe_context=safe_context,
        safety_warnings=_dedupe(warnings),
    )


def _render_markdown(pending: PendingCaseDraftRequest, *, now: datetime | None) -> str:
    context = pending.safe_context
    metadata = {
        "schema_version": DRAFT_SCHEMA_VERSION,
        "draft_type": DRAFT_TYPE,
        "title": pending.title,
        "created_at": _utc_iso(now),
        "source_context_type": pending.source_context_type,
        "review_status": DRAFT_REVIEW_STATUS,
        "safety_reviewed": False,
        "ingest_status": DRAFT_INGEST_STATUS,
        "promotion_allowed": False,
        "simulated_decision": True,
        "risk_level": context.get("risk_level"),
        "decision": context.get("decision"),
        "tags": [],
        "source_skill": DRAFT_SOURCE_SKILL,
        "fingerprint": pending.fingerprint,
        "safety_warnings": pending.safety_warnings,
    }
    frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip()
    provenance = json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True)
    warnings = "\n".join(f"- {warning}" for warning in pending.safety_warnings) or "- None recorded."
    return (
        f"---\n{frontmatter}\n---\n\n"
        f"# {pending.title}\n\n"
        "## Draft Status\n"
        "- This markdown file is an isolated case draft for later human review.\n"
        "- It is not live knowledge, not ingested, and not approved for promotion.\n"
        "- `safety_reviewed` is false by default.\n\n"
        "## Provenance\n"
        "```json\n"
        f"{provenance}\n"
        "```\n\n"
        "## Safety Warnings\n"
        f"{warnings}\n\n"
        "## Simulation And Authority Boundary\n"
        "- BLOCK, MONITOR, and ALLOW remain simulated project decisions.\n"
        "- The deterministic system Risk Level and Decision are not changed by this draft.\n"
        "- No real firewall, WAF, EDR, account, password reset, monitoring deployment, or enforcement action was executed.\n"
        "- No account takeover, execution success, containment completion, or live remediation outcome is asserted.\n"
    )


def _safe_output_dir(output_dir: str | Path | None) -> Path:
    directory = Path(output_dir) if output_dir is not None else DEFAULT_CASE_DRAFT_DIR
    if any(part.casefold() in {"knowledge", "chroma_db"} for part in directory.parts):
        raise ValueError("case drafts must not be written under knowledge/** or chroma_db/**")
    return directory


def _draft_filename(pending: PendingCaseDraftRequest) -> str:
    decision = str(pending.safe_context.get("decision") or "decision").casefold()
    risk = str(pending.safe_context.get("risk_level") or "risk").casefold()
    return _safe_slug(f"{pending.source_context_type}-{risk}-{decision}-{pending.fingerprint}") + ".md"


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-.").lower()
    return slug or "case-draft"


def _title_from_context(
    prefix: str,
    parts: list[str],
    decision: str,
    user_text: str,
    warnings: list[str],
) -> str:
    usable_parts = [_sanitize_text(part, warnings).strip() for part in parts if str(part or "").strip()]
    topic = " / ".join(usable_parts[:2]) if usable_parts else "current case"
    requested_title = _requested_title(user_text, warnings)
    title = requested_title or f"{prefix} - {topic} - {decision}"
    return _sanitize_text(title, warnings)[:120]


def _requested_title(user_text: str, warnings: list[str]) -> str | None:
    match = re.search(r"(?i)(?:\btitle\s*[:=]|標題\s*[：:])\s*(.+)$", str(user_text or ""))
    if match:
        title = _sanitize_text(match.group(1).strip(), warnings)
        return title[:120] if title else None
    return None

def _extract_source_log_path(rendered_summary: str) -> str | None:
    match = re.search(r"(?im)^File:\s*(.+?)\s*$", str(rendered_summary or ""))
    if not match:
        return None
    return match.group(1).strip() or None


def _context_fingerprint(source_context_type: ContextType, safe_context: dict[str, Any]) -> str:
    payload = json.dumps(
        {"source_context_type": source_context_type, "safe_context": safe_context},
        default=str,
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _sanitize_text(value: Any, warnings: list[str]) -> str:
    text = str(value or "")
    sanitized = text
    for pattern in _SECRET_PATTERNS:
        if pattern.search(sanitized):
            warnings.append(SECRET_WARNING)
            sanitized = pattern.sub(_redaction_for_match, sanitized)
    warnings.extend(_pii_warnings(sanitized))
    return sanitized


def _redaction_for_match(match: re.Match[str]) -> str:
    text = match.group(0)
    assignment = re.match(r"(?i)\b([A-Za-z0-9_-]+)\s*[:=]", text)
    if assignment:
        return f"{assignment.group(1)}=<redacted_secret>"
    if text.casefold().startswith("bearer"):
        return "Bearer <redacted_secret>"
    return "<redacted_secret>"


def _scan_warnings(value: str) -> list[str]:
    warnings: list[str] = []
    _sanitize_text(value, warnings)
    return _dedupe(warnings)


def _pii_warnings(value: str) -> list[str]:
    return [PII_WARNING] if any(pattern.search(str(value or "")) for pattern in _PII_PATTERNS) else []


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


def _utc_iso(now: datetime | None) -> str:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
