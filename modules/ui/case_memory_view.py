"""Read-only display helpers for approved similar-case seed memory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

APPROVED_CASE_SEED_DIR = Path("data/approved_case_seeds")
APPROVED_REVIEW_STATUS = "approved_for_similarity_demo"

CASE_MEMORY_BOUNDARY_NOTES: tuple[str, ...] = (
    "Approved seeds are manually curated demo cases.",
    "They are advisory references only.",
    "They do not override the current event's Risk Level or Decision.",
    "They are not generated drafts from workbench/case_drafts.",
    "They are not automatically ingested into live knowledge.",
)

DEFAULT_CASE_MEMORY_LANGUAGE = "en"
_SUPPORTED_CASE_MEMORY_LANGUAGES = ("en", "zh-TW", "bilingual")

# Language-aware fixed boundary notes. English is byte-identical to the tuple
# above; bilingual is compact "<zh> / <en>". Only this fixed advisory text is
# localized -- seed data, paths, and matched values are never translated.
_CASE_MEMORY_BOUNDARY_NOTES_BY_LANGUAGE: dict[str, tuple[str, ...]] = {
    "en": CASE_MEMORY_BOUNDARY_NOTES,
    "zh-TW": (
        "核准種子是人工整理的展示案例。",
        "它們僅作為參考。",
        "它們不會覆蓋目前事件的 Risk Level 或 Decision。",
        "它們不是由 workbench/case_drafts 產生的草稿。",
        "它們不會被自動匯入即時知識庫。",
    ),
    "bilingual": (
        "核准種子是人工整理的展示案例。 / Approved seeds are manually curated demo cases.",
        "它們僅作為參考。 / They are advisory references only.",
        "它們不會覆蓋目前事件的 Risk Level 或 Decision。 / "
        "They do not override the current event's Risk Level or Decision.",
        "它們不是由 workbench/case_drafts 產生的草稿。 / "
        "They are not generated drafts from workbench/case_drafts.",
        "它們不會被自動匯入即時知識庫。 / They are not automatically ingested into live knowledge.",
    ),
}


def case_memory_boundary_notes(
    language: str = DEFAULT_CASE_MEMORY_LANGUAGE,
) -> tuple[str, ...]:
    """Return the language-aware case-memory boundary notes (English default)."""

    text = str(language or "").strip()
    if text not in _SUPPORTED_CASE_MEMORY_LANGUAGES:
        return CASE_MEMORY_BOUNDARY_NOTES
    return _CASE_MEMORY_BOUNDARY_NOTES_BY_LANGUAGE[text]


@dataclass(frozen=True)
class CaseMemorySeedDisplay:
    """Immutable UI display model for one approved case seed."""

    case_id: str
    title: str
    case_type: str
    review_status: str
    approved_for_retrieval: bool
    attack_types: tuple[str, ...]
    rule_ids: tuple[str, ...]
    finding_types: tuple[str, ...]
    evidence_types: tuple[str, ...]
    risk_level: str
    decision: str
    simulated_decision: bool
    summary: str
    key_facts: tuple[str, ...]
    investigation_notes: tuple[str, ...]
    differences_to_check: tuple[str, ...]
    analyst_conclusion: str
    outcome: str
    source_provenance: str
    current_event_authority: str
    source_path: str


@dataclass(frozen=True)
class CaseMemoryCorpusDisplay:
    """Display summary for the approved case seed corpus."""

    source_directory: str
    seeds: tuple[CaseMemorySeedDisplay, ...]
    boundary_notes: tuple[str, ...] = CASE_MEMORY_BOUNDARY_NOTES

    @property
    def approved_seed_count(self) -> int:
        return len(self.seeds)

    @property
    def approved_for_retrieval_count(self) -> int:
        return sum(1 for seed in self.seeds if seed.approved_for_retrieval)


def build_case_memory_display(
    seed_directory: str | Path = APPROVED_CASE_SEED_DIR,
    language: str = DEFAULT_CASE_MEMORY_LANGUAGE,
) -> CaseMemoryCorpusDisplay:
    """Load approved seed files into a read-only UI display model.

    ``language`` localizes only the fixed boundary notes; seed values are
    unchanged. The default ("en") preserves existing output for non-UI callers.
    """

    notes = case_memory_boundary_notes(language)
    directory = Path(seed_directory)
    if not directory.exists() or not directory.is_dir():
        return CaseMemoryCorpusDisplay(
            source_directory=directory.as_posix(), seeds=(), boundary_notes=notes
        )

    seeds = tuple(
        seed
        for path in sorted(directory.glob("*.yml"))
        for seed in [_load_seed_display(path)]
        if seed is not None
    )
    return CaseMemoryCorpusDisplay(
        source_directory=directory.as_posix(), seeds=seeds, boundary_notes=notes
    )


def case_memory_table_rows(
    seeds: tuple[CaseMemorySeedDisplay, ...],
) -> list[dict[str, str | bool]]:
    """Return compact table rows for the Streamlit read-only view."""

    return [
        {
            "case_id": seed.case_id,
            "title": seed.title,
            "case_type": seed.case_type,
            "risk_level": seed.risk_level,
            "decision": seed.decision,
            "approved_for_retrieval": seed.approved_for_retrieval,
        }
        for seed in seeds
    ]


def _load_seed_display(path: Path) -> CaseMemorySeedDisplay | None:
    if _is_forbidden_runtime_draft_path(path):
        return None

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(raw, dict):
        return None
    if raw.get("review_status") != APPROVED_REVIEW_STATUS:
        return None
    if raw.get("approved_for_retrieval") is not True:
        return None

    return CaseMemorySeedDisplay(
        case_id=_text(raw.get("case_id")),
        title=_text(raw.get("title")),
        case_type=_text(raw.get("case_type")),
        review_status=_text(raw.get("review_status")),
        approved_for_retrieval=bool(raw.get("approved_for_retrieval")),
        attack_types=_strings(raw.get("attack_types")),
        rule_ids=_strings(raw.get("rule_ids")),
        finding_types=_strings(raw.get("finding_types")),
        evidence_types=_strings(raw.get("evidence_types")),
        risk_level=_text(raw.get("risk_level")),
        decision=_text(raw.get("decision")),
        simulated_decision=bool(raw.get("simulated_decision")),
        summary=_text(raw.get("summary")),
        key_facts=_strings(raw.get("key_facts")),
        investigation_notes=_strings(raw.get("investigation_notes")),
        differences_to_check=_strings(raw.get("differences_to_check")),
        analyst_conclusion=_text(raw.get("analyst_conclusion")),
        outcome=_text(raw.get("outcome")),
        source_provenance=_text(raw.get("source_provenance")),
        current_event_authority=_text(raw.get("current_event_authority")),
        source_path=path.as_posix(),
    )


def _text(value: Any) -> str:
    return str(value or "").strip()


def _strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    return ()


def _is_forbidden_runtime_draft_path(path: Path) -> bool:
    normalized_parts = {part.casefold() for part in path.parts}
    return "workbench" in normalized_parts and "case_drafts" in normalized_parts
