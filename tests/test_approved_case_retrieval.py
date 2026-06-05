from pathlib import Path

from modules.controller.approved_case_retrieval import (
    AUTH_COMPROMISE_BOUNDARY,
    SIMILAR_CASE_BOUNDARY,
    ApprovedCaseSeed,
    format_similar_case_output,
    load_approved_case_seeds,
    retrieve_approved_similar_cases,
)
from modules.event_followup import ActiveEventContext
from modules.incident_followup import build_active_auth_incident_context
from modules.types import EvidenceBundle, EvidenceItem, Finding, Incident


def _event_context(
    *,
    attack_types: tuple[str, ...] = ("Command Injection",),
    rule_ids: tuple[str, ...] = ("CMD-001",),
) -> ActiveEventContext:
    return ActiveEventContext(
        original_input="test; rm -rf /tmp/test",
        attack_types=attack_types,
        matched_signatures={"Command Injection": (";", "rm ")},
        rule_ids=rule_ids,
        rule_sources=("detections/blue_team/command_injection_basic.yml",),
        risk_level="HIGH",
        decision="BLOCK",
        simulation_notice="Simulated BLOCK only.",
        rendered_report="Mode 1 report",
    )


def _auth_context():
    incident = Incident(
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
    return build_active_auth_incident_context(incident)


def test_loads_only_approved_seed_files_from_default_corpus() -> None:
    seeds = load_approved_case_seeds()

    assert [seed.case_id for seed in seeds] == [
        "CASE-SEED-001",
        "CASE-SEED-002",
        "CASE-SEED-003",
    ]
    assert all(seed.review_status == "approved_for_similarity_demo" for seed in seeds)
    assert all(seed.approved_for_retrieval is True for seed in seeds)


def test_invalid_unapproved_and_runtime_draft_seed_files_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "unapproved.yml").write_text(
        """
schema_version: v2.5-approved-case1
case_id: CASE-SEED-X
title: Unapproved
review_status: draft
approved_for_retrieval: false
case_type: payload_event
risk_level: HIGH
decision: BLOCK
simulated_decision: true
summary: draft
analyst_conclusion: draft
outcome: draft
source_provenance: manually_curated_seed
current_event_authority: advisory_only_no_override
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "invalid.yml").write_text("not: [valid", encoding="utf-8")

    seeds = load_approved_case_seeds(tmp_path)

    assert seeds == []


def test_command_injection_active_event_returns_case_seed_001_as_top_match() -> None:
    result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())

    assert result.matches[0].seed.case_id == "CASE-SEED-001"
    assert "matched attack_types: Command Injection" in result.matches[0].reasons
    assert "matched rule_ids: CMD-001" in result.matches[0].reasons


def test_authentication_incident_returns_case_seed_002_as_top_match() -> None:
    result = retrieve_approved_similar_cases(_auth_context(), load_approved_case_seeds())

    assert result.matches[0].seed.case_id == "CASE-SEED-002"
    assert "matched finding_types: possible_account_compromise" in result.matches[0].reasons
    assert "matched evidence_types: auth_failure_sequence, success_after_failures" in result.matches[0].reasons


def test_risk_and_decision_only_matches_are_excluded() -> None:
    event_result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())
    auth_result = retrieve_approved_similar_cases(_auth_context(), load_approved_case_seeds())

    assert [match.seed.case_id for match in event_result.matches] == ["CASE-SEED-001"]
    assert [match.seed.case_id for match in auth_result.matches] == ["CASE-SEED-002"]


def test_sql_injection_seed_exists_as_comparison_candidate() -> None:
    seeds = load_approved_case_seeds()
    sql_seed = next(seed for seed in seeds if seed.case_id == "CASE-SEED-003")

    assert sql_seed.attack_types == ["SQL Injection"]
    assert sql_seed.rule_ids == ["SQLI-001"]
    assert sql_seed.evidence_types == ["sql_injection_payload"]


def test_output_includes_reasons_differences_and_boundaries() -> None:
    result = retrieve_approved_similar_cases(_auth_context(), load_approved_case_seeds())

    output = format_similar_case_output(result)

    assert "CASE-SEED-002" in output
    assert "Similarity reasons:" in output
    assert "Key differences / missing evidence to check:" in output
    assert SIMILAR_CASE_BOUNDARY in output
    assert AUTH_COMPROMISE_BOUNDARY in output
    assert "do not override" in output
    assert "do not prove account compromise" in output


def test_approved_case_seed_model_rejects_non_advisory_seed() -> None:
    raw = load_approved_case_seeds()[0].model_dump()
    raw["current_event_authority"] = "can_override"

    try:
        ApprovedCaseSeed.model_validate(raw)
    except ValueError as exc:
        assert "advisory only" in str(exc)
    else:
        raise AssertionError("non-advisory approved case seed was accepted")


def test_approved_case_retrieval_has_no_heavy_runtime_dependencies() -> None:
    source = Path("modules/controller/approved_case_retrieval.py").read_text(encoding="utf-8")

    forbidden = [
        "chromadb",
        "ollama",
        "langchain",
        "ingest_knowledge",
        "workbench/case_drafts",
        "modules.graph",
        "modules.rag",
    ]
    assert all(item not in source for item in forbidden)
