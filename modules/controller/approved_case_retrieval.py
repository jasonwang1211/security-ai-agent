"""Read-only approved similar-case retrieval over curated seed files.

This module is deterministic and file-backed. It does not call Chroma,
embeddings, LLMs, graph traversal, ingest, or generated case-draft paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from modules.controller.report_language import label_separator, normalize_report_language
from modules.event_followup import ActiveEventContext
from modules.incident_followup import ActiveAuthIncidentContext

APPROVED_CASE_SEED_DIR = Path("data/approved_case_seeds")
APPROVED_CASE_SCHEMA_VERSION = "v2.5-approved-case1"
APPROVED_CASE_REVIEW_STATUS = "approved_for_similarity_demo"
SIMILAR_CASE_BOUNDARY = (
    "Historical approved cases are advisory references only. They do not override "
    "the current event's deterministic Risk Level or Decision, and they do not "
    "prove compromise or successful execution in the current event."
)
AUTH_COMPROMISE_BOUNDARY = (
    "Repeated login failures followed by success are suspicious but do not prove "
    "account compromise by themselves."
)

# --- Language-aware fixed labels / advisory prose (presentation text only) ---
# English wording is byte-identical to the prior output; the default language is
# English so non-UI callers and existing tests keep the exact prior wording.
# Dynamic / domain values (case IDs, attack types, rule IDs, evidence types,
# risk/decision values, scores, source paths, payload text) are inserted by the
# caller and are never translated here. This does not change similarity scoring
# or matching -- only how the already-computed result is rendered.
_SIMILAR_CASE_TITLE = {
    "en": "[Approved Similar Cases]",
    "zh-TW": "[核准相似案例]",
    "bilingual": "[核准相似案例 / Approved Similar Cases]",
}
_GRAPH_EXPLANATION_HEADING = {
    "en": "Graph-Grounded Relationship Explanation:",
    "zh-TW": "圖形關係說明：",
    "bilingual": "圖形關係說明 / Graph-Grounded Relationship Explanation：",
}
_NO_MATCHES_LINE = {
    "en": "No approved similar cases matched the current structured facts.",
    "zh-TW": "沒有核准相似案例符合目前的結構化事實。",
    "bilingual": (
        "沒有核准相似案例符合目前的結構化事實。 / "
        "No approved similar cases matched the current structured facts."
    ),
}
_SIMILAR_CASE_BOUNDARY_BY_LANGUAGE = {
    "en": SIMILAR_CASE_BOUNDARY,
    "zh-TW": (
        "歷史核准案例僅供參考，不會覆蓋目前事件的確定性 Risk Level 或 Decision，"
        "也不代表目前事件已成功執行或已造成入侵。"
    ),
    "bilingual": (
        "歷史核准案例僅供參考，不會覆蓋目前事件的確定性 Risk Level 或 Decision，"
        "也不代表目前事件已成功執行或已造成入侵。 / " + SIMILAR_CASE_BOUNDARY
    ),
}
_AUTH_COMPROMISE_BOUNDARY_BY_LANGUAGE = {
    "en": AUTH_COMPROMISE_BOUNDARY,
    "zh-TW": "連續登入失敗後成功登入雖然可疑，但本身並不能證明帳號已遭入侵。",
    "bilingual": (
        "連續登入失敗後成功登入雖然可疑，但本身並不能證明帳號已遭入侵。 / "
        + AUTH_COMPROMISE_BOUNDARY
    ),
}
# Field labels (text only, no separator). Bilingual is composed as "<zh> / <en>".
_SIMILAR_CASE_LABELS: dict[str, dict[str, str]] = {
    "context_kind": {"en": "Current context kind", "zh-TW": "目前脈絡類型"},
    "current_risk": {"en": "Current Risk Level", "zh-TW": "目前風險等級"},
    "current_decision": {"en": "Current Decision", "zh-TW": "目前決策"},
    "score": {"en": "Score", "zh-TW": "分數"},
    "similarity_reasons": {"en": "Similarity reasons", "zh-TW": "相似原因"},
    "key_differences": {
        "en": "Key differences / missing evidence to check",
        "zh-TW": "需檢查的差異 / 缺少證據",
    },
    "analyst_conclusion": {"en": "Analyst conclusion", "zh-TW": "分析師結論"},
    "outcome_note": {"en": "Outcome note", "zh-TW": "結果說明"},
    "source": {"en": "Source", "zh-TW": "來源"},
    "boundary": {"en": "Boundary", "zh-TW": "邊界"},
}
# Relationship sentence pieces: English verb phrase + Chinese verb phrase per kind.
_RELATIONSHIP_PHRASES: dict[str, dict[str, str]] = {
    "attack_type": {"en": "shares attack type", "zh-TW": "共享攻擊類型"},
    "rule_id": {"en": "shares rule ID", "zh-TW": "共享規則 ID"},
    "finding_type": {"en": "shares finding type", "zh-TW": "共享發現類型"},
    "evidence_type": {"en": "shares evidence type", "zh-TW": "共享證據類型"},
    "decision": {"en": "shares simulated Decision", "zh-TW": "共享模擬決策"},
}


def _localized_choice(mapping: dict[str, str], language: str | None) -> str:
    lang = normalize_report_language(language)
    return mapping.get(lang) or mapping["en"]


def _similar_case_label(key: str, language: str | None) -> str:
    entry = _SIMILAR_CASE_LABELS[key]
    lang = normalize_report_language(language)
    english = entry["en"]
    if lang == "en":
        return english
    chinese = entry["zh-TW"]
    return chinese if lang == "zh-TW" else f"{chinese} / {english}"


def _relationship_sentence(
    kind: str,
    is_incident: bool,
    value: str,
    case_id: str,
    language: str | None,
) -> str:
    phrases = _RELATIONSHIP_PHRASES[kind]
    english = f"{'Current incident' if is_incident else 'Current context'} {phrases['en']} {value} with {case_id}."
    lang = normalize_report_language(language)
    if lang == "en":
        return english
    chinese = f"{'目前事件' if is_incident else '目前脈絡'}與 {case_id} {phrases['zh-TW']}：{value}。"
    return chinese if lang == "zh-TW" else f"{chinese} / {english}"


CaseType = Literal["payload_event", "auth_incident"]


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _clean_strings(values: list[str]) -> list[str]:
    return [str(value).strip() for value in values if str(value).strip()]


def _upper_strings(values: list[str]) -> list[str]:
    return [value.upper() for value in _clean_strings(values)]


class ApprovedCaseSeed(BaseModel):
    """Curated approved case seed used only for read-only similarity demo retrieval."""

    schema_version: str
    case_id: str
    title: str
    review_status: str
    approved_for_retrieval: bool
    case_type: CaseType
    attack_types: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    finding_types: list[str] = Field(default_factory=list)
    evidence_types: list[str] = Field(default_factory=list)
    risk_level: str
    decision: str
    simulated_decision: bool
    summary: str
    key_facts: list[str] = Field(default_factory=list)
    investigation_notes: list[str] = Field(default_factory=list)
    differences_to_check: list[str] = Field(default_factory=list)
    analyst_conclusion: str
    outcome: str
    source_provenance: str
    current_event_authority: str
    source_path: str | None = None

    @field_validator(
        "schema_version",
        "case_id",
        "title",
        "review_status",
        "risk_level",
        "decision",
        "summary",
        "analyst_conclusion",
        "outcome",
        "source_provenance",
        "current_event_authority",
    )
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "required text")

    @field_validator("attack_types", "finding_types", "evidence_types", "key_facts", "investigation_notes", "differences_to_check")
    @classmethod
    def list_fields_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return _clean_strings(value)

    @field_validator("rule_ids")
    @classmethod
    def rule_ids_should_be_uppercase(cls, value: list[str]) -> list[str]:
        return _upper_strings(value)

    @model_validator(mode="after")
    def approved_seed_contract(self) -> ApprovedCaseSeed:
        if self.schema_version != APPROVED_CASE_SCHEMA_VERSION:
            raise ValueError("unsupported approved case seed schema_version")
        if self.review_status != APPROVED_CASE_REVIEW_STATUS:
            raise ValueError("approved case seed is not approved for similarity demo")
        if not self.approved_for_retrieval:
            raise ValueError("approved case seed is not enabled for retrieval")
        if not self.simulated_decision:
            raise ValueError("approved case seed must preserve simulated_decision=true")
        if self.source_provenance != "manually_curated_seed":
            raise ValueError("approved case seed must be manually curated")
        if self.current_event_authority != "advisory_only_no_override":
            raise ValueError("approved case seed must be advisory only")
        return self


@dataclass(frozen=True)
class CurrentCaseFeatures:
    context_kind: str
    attack_types: tuple[str, ...]
    rule_ids: tuple[str, ...]
    finding_types: tuple[str, ...]
    evidence_types: tuple[str, ...]
    risk_level: str
    decision: str


@dataclass(frozen=True)
class SimilarCaseMatch:
    seed: ApprovedCaseSeed
    score: int
    reasons: tuple[str, ...]
    differences: tuple[str, ...]


@dataclass(frozen=True)
class CaseRelationshipExplanation:
    shared_relationships: tuple[str, ...]
    difference_relationships: tuple[str, ...]
    boundary: str


@dataclass(frozen=True)
class SimilarCaseResult:
    current: CurrentCaseFeatures
    matches: tuple[SimilarCaseMatch, ...]

    @property
    def has_matches(self) -> bool:
        return bool(self.matches)


def load_approved_case_seeds(directory: str | Path = APPROVED_CASE_SEED_DIR) -> list[ApprovedCaseSeed]:
    """Load valid approved case seeds from a tracked seed directory."""

    seed_dir = Path(directory)
    if not seed_dir.exists():
        return []

    seeds: list[ApprovedCaseSeed] = []
    for path in sorted(seed_dir.glob("*.yml")):
        if _is_forbidden_runtime_draft_path(path):
            continue
        seed = load_approved_case_seed(path)
        if seed is not None:
            seeds.append(seed)
    return seeds


def load_approved_case_seed(path: str | Path) -> ApprovedCaseSeed | None:
    """Load one approved case seed; invalid or unapproved files are ignored safely."""

    seed_path = Path(path)
    if _is_forbidden_runtime_draft_path(seed_path):
        return None

    try:
        raw = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None

    raw_values: dict[str, Any] = dict(raw)
    raw_values["source_path"] = seed_path.as_posix()
    try:
        return ApprovedCaseSeed.model_validate(raw_values)
    except ValueError:
        return None


def retrieve_approved_similar_cases(
    current_context: ActiveEventContext | ActiveAuthIncidentContext,
    seeds: list[ApprovedCaseSeed],
    *,
    limit: int = 3,
) -> SimilarCaseResult:
    """Return deterministic top similar approved cases for the supplied active context."""

    current = features_from_context(current_context)
    matches = [
        match
        for seed in seeds
        for match in [_score_seed(current, seed)]
        if match.score > 0
    ]
    matches.sort(key=lambda match: (-match.score, match.seed.case_id))
    return SimilarCaseResult(current=current, matches=tuple(matches[: max(limit, 0)]))


def features_from_context(
    current_context: ActiveEventContext | ActiveAuthIncidentContext,
) -> CurrentCaseFeatures:
    """Extract structured similarity fields from an active event or incident context."""

    if isinstance(current_context, ActiveEventContext):
        return CurrentCaseFeatures(
            context_kind="active_event",
            attack_types=tuple(_clean_strings(list(current_context.attack_types))),
            rule_ids=tuple(_upper_strings(list(current_context.rule_ids))),
            finding_types=(),
            evidence_types=tuple(_event_evidence_types(current_context)),
            risk_level=current_context.risk_level.upper(),
            decision=current_context.decision.upper(),
        )

    incident = current_context.incident
    return CurrentCaseFeatures(
        context_kind="active_auth_incident",
        attack_types=tuple(_clean_strings([incident.attack_type or incident.title])),
        rule_ids=tuple(_upper_strings(_incident_rule_ids(incident.metadata))),
        finding_types=tuple(_clean_strings([finding.finding_type for finding in incident.findings])),
        evidence_types=tuple(_clean_strings([item.type for item in incident.evidence_bundle.items])),
        risk_level=incident.risk_level.upper(),
        decision=incident.decision.upper(),
    )


def format_similar_case_output(
    result: SimilarCaseResult,
    language: str | None = None,
) -> str:
    """Render a deterministic analyst-facing similar-case summary.

    ``language`` localizes only fixed labels and fixed advisory/boundary prose.
    The default (English) keeps the prior wording for non-UI callers and tests.
    Dynamic values (case IDs, attack types, rule IDs, scores, paths) are never
    translated, and similarity scoring/matching is unaffected.
    """

    lang = normalize_report_language(language)
    sep = label_separator(lang)
    lines = [
        _localized_choice(_SIMILAR_CASE_TITLE, lang),
        f"{_similar_case_label('context_kind', lang)}{sep}{result.current.context_kind}",
        f"{_similar_case_label('current_risk', lang)}{sep}{result.current.risk_level}",
        f"{_similar_case_label('current_decision', lang)}{sep}{result.current.decision}",
        _localized_choice(_SIMILAR_CASE_BOUNDARY_BY_LANGUAGE, lang),
    ]
    if result.current.context_kind == "active_auth_incident":
        lines.append(_localized_choice(_AUTH_COMPROMISE_BOUNDARY_BY_LANGUAGE, lang))

    if not result.matches:
        lines.append(_localized_choice(_NO_MATCHES_LINE, lang))
        return "\n".join(lines)

    for index, match in enumerate(result.matches, start=1):
        seed = match.seed
        lines.extend(
            [
                "",
                f"{index}. {seed.case_id} - {seed.title}",
                f"   {_similar_case_label('score', lang)}{sep}{match.score}",
                f"   {_similar_case_label('similarity_reasons', lang)}{sep}{_join_or_none(match.reasons)}",
                f"   {_similar_case_label('key_differences', lang)}{sep}{_join_or_none(match.differences)}",
                f"   {_localized_choice(_GRAPH_EXPLANATION_HEADING, lang)}",
                *_format_relationship_explanation(result.current, match, lang),
                f"   {_similar_case_label('analyst_conclusion', lang)}{sep}{seed.analyst_conclusion}",
                f"   {_similar_case_label('outcome_note', lang)}{sep}{seed.outcome}",
                f"   {_similar_case_label('source', lang)}{sep}{seed.source_provenance} ({seed.source_path})",
            ]
        )

    return "\n".join(lines)


def build_case_relationship_explanation(
    current: CurrentCaseFeatures,
    match: SimilarCaseMatch,
    language: str | None = None,
) -> CaseRelationshipExplanation:
    """Build deterministic graph-style relationship lines from structured fields only.

    ``language`` localizes only the fixed sentence templates and boundary text;
    dynamic values are unchanged and structured-field selection is identical.
    """

    lang = normalize_report_language(language)
    seed = match.seed
    is_incident = current.context_kind == "active_auth_incident"
    shared: list[str] = []

    for value in _intersection(current.attack_types, seed.attack_types):
        shared.append(_relationship_sentence("attack_type", is_incident, value, seed.case_id, lang))
    for value in _intersection(current.rule_ids, seed.rule_ids):
        shared.append(_relationship_sentence("rule_id", is_incident, value, seed.case_id, lang))
    for value in _intersection(current.finding_types, seed.finding_types):
        shared.append(_relationship_sentence("finding_type", is_incident, value, seed.case_id, lang))
    for value in _intersection(current.evidence_types, seed.evidence_types):
        shared.append(_relationship_sentence("evidence_type", is_incident, value, seed.case_id, lang))
    if current.decision == seed.decision.upper():
        shared.append(_relationship_sentence("decision", is_incident, current.decision, seed.case_id, lang))

    return CaseRelationshipExplanation(
        shared_relationships=tuple(shared),
        difference_relationships=match.differences,
        boundary=_localized_choice(_SIMILAR_CASE_BOUNDARY_BY_LANGUAGE, lang),
    )


def _format_relationship_explanation(
    current: CurrentCaseFeatures,
    match: SimilarCaseMatch,
    language: str | None = None,
) -> list[str]:
    lang = normalize_report_language(language)
    sep = label_separator(lang)
    explanation = build_case_relationship_explanation(current, match, lang)
    lines = [f"      - {relationship}" for relationship in explanation.shared_relationships]
    lines.extend(f"      - {relationship}" for relationship in explanation.difference_relationships)
    lines.append(f"      - {_similar_case_label('boundary', lang)}{sep}{explanation.boundary}")
    return lines


def _score_seed(current: CurrentCaseFeatures, seed: ApprovedCaseSeed) -> SimilarCaseMatch:
    score = 0
    reasons: list[str] = []
    primary_match = False

    attack_matches = _intersection(current.attack_types, seed.attack_types)
    if attack_matches:
        primary_match = True
        score += 50 * len(attack_matches)
        reasons.append(f"matched attack_types: {', '.join(attack_matches)}")

    rule_matches = _intersection(current.rule_ids, seed.rule_ids)
    if rule_matches:
        primary_match = True
        score += 40 * len(rule_matches)
        reasons.append(f"matched rule_ids: {', '.join(rule_matches)}")

    finding_matches = _intersection(current.finding_types, seed.finding_types)
    if finding_matches:
        primary_match = True
        score += 30 * len(finding_matches)
        reasons.append(f"matched finding_types: {', '.join(finding_matches)}")

    evidence_matches = _intersection(current.evidence_types, seed.evidence_types)
    if evidence_matches:
        primary_match = True
        score += 25 * len(evidence_matches)
        reasons.append(f"matched evidence_types: {', '.join(evidence_matches)}")

    if not primary_match:
        score = 0
    else:
        if current.risk_level == seed.risk_level.upper():
            score += 5
            reasons.append(f"supporting risk_level match: {current.risk_level}")
        if current.decision == seed.decision.upper():
            score += 5
            reasons.append(f"supporting decision match: {current.decision}")

    return SimilarCaseMatch(
        seed=seed,
        score=score,
        reasons=tuple(reasons),
        differences=tuple(_differences(current, seed)),
    )


def _event_evidence_types(context: ActiveEventContext) -> list[str]:
    evidence_types = ["payload_event"]
    attack_types = {attack.casefold() for attack in context.attack_types}
    rule_ids = set(context.rule_ids)
    if "command injection" in attack_types or "CMD-001" in rule_ids:
        evidence_types.append("shell_metacharacter_payload")
    if "sql injection" in attack_types or "SQLI-001" in rule_ids:
        evidence_types.append("sql_injection_payload")
    if "xss" in attack_types or "XSS-001" in rule_ids:
        evidence_types.append("xss_payload")
    if "path traversal" in attack_types or "PATH-001" in rule_ids:
        evidence_types.append("path_traversal_payload")
    return list(dict.fromkeys(evidence_types))


def _incident_rule_ids(metadata: dict[str, Any]) -> list[str]:
    raw_rule_ids = metadata.get("rule_ids") or metadata.get("rule_id") or []
    if isinstance(raw_rule_ids, str):
        return [raw_rule_ids]
    if isinstance(raw_rule_ids, list):
        return [str(value) for value in raw_rule_ids]
    return []


def _differences(current: CurrentCaseFeatures, seed: ApprovedCaseSeed) -> list[str]:
    differences: list[str] = list(seed.differences_to_check)
    if not _intersection(current.attack_types, seed.attack_types):
        differences.append(
            f"Current attack_types ({_join_or_none(current.attack_types)}) differ from seed ({_join_or_none(seed.attack_types)})."
        )
    if current.risk_level != seed.risk_level.upper():
        differences.append(f"Current risk_level {current.risk_level} differs from seed {seed.risk_level}.")
    if current.decision != seed.decision.upper():
        differences.append(f"Current decision {current.decision} differs from seed {seed.decision}.")
    return list(dict.fromkeys(differences))


def _intersection(left: tuple[str, ...], right: list[str]) -> list[str]:
    normalized_right = {_normalize(value): value for value in right}
    matches: list[str] = []
    for value in left:
        normalized = _normalize(value)
        if normalized in normalized_right:
            matches.append(normalized_right[normalized])
    return matches


def _normalize(value: str) -> str:
    return " ".join(str(value or "").casefold().replace("_", " ").split())


def _join_or_none(values: tuple[str, ...] | list[str]) -> str:
    return ", ".join(values) if values else "None"


def _is_forbidden_runtime_draft_path(path: Path) -> bool:
    normalized_parts = {part.casefold() for part in path.parts}
    return "workbench" in normalized_parts and "case_drafts" in normalized_parts
