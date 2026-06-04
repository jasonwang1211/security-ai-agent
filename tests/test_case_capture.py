from datetime import datetime, timezone
from pathlib import Path

import yaml

from modules.controller.case_capture import (
    DUPLICATE_WARNING,
    PII_WARNING,
    SECRET_WARNING,
    build_pending_case_draft_request,
    write_case_draft,
)
from modules.event_followup import ActiveEventContext
from modules.incident_followup import build_active_auth_incident_context
from modules.types import EvidenceBundle, EvidenceItem, Finding, Incident


NOW = datetime(2026, 6, 5, 4, 40, tzinfo=timezone.utc)


def _event_context(payload: str = "cmd=whoami; password=supersecret src=10.0.0.7") -> ActiveEventContext:
    return ActiveEventContext(
        original_input=payload,
        attack_types=("Command Injection",),
        matched_signatures={"Command Injection": (";", "whoami")},
        rule_ids=("CMD-001",),
        rule_sources=("detections/blue_team/command_injection.yml",),
        risk_level="HIGH",
        decision="BLOCK",
        simulation_notice="Simulated BLOCK only.",
        rendered_report="Mode 1 report",
    )


def _incident() -> Incident:
    return Incident(
        id="INC-20260605-001",
        title="Possible Account Compromise",
        status="ALERT",
        risk_level="HIGH",
        decision="MONITOR",
        attack_type="Possible Account Compromise",
        findings=[
            Finding(
                id="F-001",
                finding_type="possible_account_compromise",
                title="Successful login after failures",
                status="ALERT",
                risk_level="HIGH",
                decision="MONITOR",
                evidence_ids=["EV-001", "EV-003"],
            )
        ],
        evidence_bundle=EvidenceBundle(
            incident_id="INC-20260605-001",
            items=[
                EvidenceItem(
                    id="EV-001",
                    type="auth_failure_sequence",
                    description="Repeated failed login attempts",
                    value={"source_ip": "10.0.0.5", "user": "admin"},
                ),
                EvidenceItem(
                    id="EV-003",
                    type="success_after_failures",
                    description="Successful login after failures",
                    value={"source_ip": "10.0.0.5", "user": "admin"},
                ),
            ],
        ),
    )


def _frontmatter(markdown: str) -> dict:
    frontmatter = markdown.split("---", 2)[1]
    return yaml.safe_load(frontmatter)


def test_event_pending_snapshot_redacts_secrets_and_warns_about_pii() -> None:
    state = {"active_context_kind": "event", "active_event_context": _event_context()}

    pending = build_pending_case_draft_request(state, "draft this case", now=NOW)

    assert pending is not None
    assert pending.source_context_type == "active_event"
    assert pending.safe_context["decision"] == "BLOCK"
    assert pending.safe_context["rule_ids"] == ["CMD-001"]
    assert "supersecret" not in pending.safe_context["payload_evidence"]
    assert "<redacted_secret>" in pending.safe_context["payload_evidence"]
    assert SECRET_WARNING in pending.safety_warnings
    assert PII_WARNING in pending.safety_warnings


def test_approved_event_draft_writes_required_metadata_and_boundaries(tmp_path: Path) -> None:
    state = {"active_context_kind": "event", "active_event_context": _event_context()}
    pending = build_pending_case_draft_request(state, "draft this case", now=NOW)
    assert pending is not None

    result = write_case_draft(pending, output_dir=tmp_path, now=NOW)

    assert result.created is True
    assert result.draft_path is not None
    draft_path = Path(result.draft_path)
    assert draft_path.is_file()
    markdown = draft_path.read_text(encoding="utf-8")
    metadata = _frontmatter(markdown)
    assert metadata["schema_version"] == "v2.5-case-draft1"
    assert metadata["draft_type"] == "incident_case_capture"
    assert metadata["review_status"] == "draft_pending_human_review"
    assert metadata["safety_reviewed"] is False
    assert metadata["ingest_status"] == "not_ingested"
    assert metadata["promotion_allowed"] is False
    assert metadata["source_skill"] == "DraftCaseCaptureSkill"
    assert metadata["source_context_type"] == "active_event"
    assert metadata["risk_level"] == "HIGH"
    assert metadata["decision"] == "BLOCK"
    assert "CMD-001" in markdown
    assert "supersecret" not in markdown
    assert "No real firewall" in markdown
    assert "confirmed compromise" not in markdown.casefold()


def test_approved_auth_incident_draft_preserves_available_ids_without_live_kb_write(tmp_path: Path) -> None:
    context = build_active_auth_incident_context(
        _incident(),
        rendered_summary="[Log Ingestion Summary]\n\nFile: demo_logs/scenario_a_mixed_auth.log\n",
    )
    state = {"active_context_kind": "incident", "active_incident_context": context}
    pending = build_pending_case_draft_request(state, "draft this incident case", now=NOW)
    assert pending is not None

    result = write_case_draft(pending, output_dir=tmp_path, now=NOW)

    markdown = Path(result.draft_path or "").read_text(encoding="utf-8")
    metadata = _frontmatter(markdown)
    assert metadata["source_context_type"] == "active_auth_incident"
    assert "INC-20260605-001" in markdown
    assert "EV-001" in markdown
    assert "EV-003" in markdown
    assert "F-001" in markdown
    assert "demo_logs/scenario_a_mixed_auth.log" in markdown
    assert "explicit_current_incident_graph_facts_only" in markdown
    assert "confirmed compromise" not in markdown.casefold()
    assert "knowledge/" not in str(result.draft_path)


def test_duplicate_draft_does_not_overwrite_existing_file(tmp_path: Path) -> None:
    state = {"active_context_kind": "event", "active_event_context": _event_context("<script>alert(1)</script>")}
    pending = build_pending_case_draft_request(state, "draft this case", now=NOW)
    assert pending is not None
    first = write_case_draft(pending, output_dir=tmp_path, now=NOW)
    draft_path = Path(first.draft_path or "")
    draft_path.write_text("already reviewed locally", encoding="utf-8")

    second = write_case_draft(pending, output_dir=tmp_path, now=NOW)

    assert second.created is False
    assert second.duplicate is True
    assert DUPLICATE_WARNING in second.warnings
    assert draft_path.read_text(encoding="utf-8") == "already reviewed locally"


def test_case_draft_rejects_live_knowledge_and_chroma_paths(tmp_path: Path) -> None:
    state = {"active_context_kind": "event", "active_event_context": _event_context()}
    pending = build_pending_case_draft_request(state, "draft this case", now=NOW)
    assert pending is not None

    for forbidden in [tmp_path / "knowledge" / "notes", tmp_path / "chroma_db"]:
        try:
            write_case_draft(pending, output_dir=forbidden, now=NOW)
        except ValueError as exc:
            assert "must not be written" in str(exc)
        else:
            raise AssertionError("forbidden draft output path was accepted")





def test_requested_title_secret_is_not_written_raw(tmp_path: Path) -> None:
    state = {"active_context_kind": "event", "active_event_context": _event_context("<script>alert(1)</script>")}
    pending = build_pending_case_draft_request(
        state,
        "save this case as a draft title: password=supersecret Review",
        now=NOW,
    )
    assert pending is not None

    result = write_case_draft(pending, output_dir=tmp_path, now=NOW)

    markdown = Path(result.draft_path or "").read_text(encoding="utf-8")
    assert "supersecret" not in pending.title
    assert "supersecret" not in markdown
    assert "password=<redacted_secret>" in markdown
    assert SECRET_WARNING in pending.safety_warnings


def test_source_log_path_secret_is_not_written_raw(tmp_path: Path) -> None:
    context = build_active_auth_incident_context(
        _incident(),
        rendered_summary="[Log Ingestion Summary]\n\nFile: demo_logs/password=supersecret.log\n",
    )
    state = {"active_context_kind": "incident", "active_incident_context": context}
    pending = build_pending_case_draft_request(state, "draft this incident case", now=NOW)
    assert pending is not None

    result = write_case_draft(pending, output_dir=tmp_path, now=NOW)

    markdown = Path(result.draft_path or "").read_text(encoding="utf-8")
    assert "supersecret" not in str(pending.safe_context.get("source_log_path"))
    assert "supersecret" not in markdown
    assert "password=<redacted_secret>" in markdown
    assert SECRET_WARNING in pending.safety_warnings

def test_case_capture_helper_has_no_ingest_or_chroma_runtime_imports() -> None:
    source = Path("modules/controller/case_capture.py").read_text(encoding="utf-8")

    assert "ingest_knowledge" not in source
    assert "chromadb" not in source.casefold()
    assert "langchain_chroma" not in source
