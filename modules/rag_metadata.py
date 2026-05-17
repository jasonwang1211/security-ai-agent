from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _remove_blank_strings(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def _normalize_upper_values(values: list[str]) -> list[str]:
    return [value.upper() for value in _remove_blank_strings(values)]


class KnowledgeDocMetadata(BaseModel):
    doc_id: str
    doc_type: str
    applies_to: list[str] = Field(default_factory=list)
    related_tools: list[str] = Field(default_factory=list)
    attack_types: list[str] = Field(default_factory=list)
    severity: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    source_path: str | None = None

    @field_validator("doc_id")
    @classmethod
    def doc_id_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "doc_id")

    @field_validator("doc_type")
    @classmethod
    def doc_type_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "doc_type")

    @field_validator(
        "applies_to",
        "related_tools",
        "attack_types",
        "severity",
        "keywords",
    )
    @classmethod
    def list_fields_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return _remove_blank_strings(value)

    @field_validator("rule_ids", "mitre_techniques")
    @classmethod
    def id_fields_should_be_uppercase_without_blanks(cls, value: list[str]) -> list[str]:
        return _normalize_upper_values(value)

    @field_validator("source_path")
    @classmethod
    def source_path_must_not_be_empty(cls, value: str | None) -> str | None:
        if value is not None:
            return _require_non_blank(value, "source_path")
        return value


def split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return "", text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            frontmatter_text = "".join(lines[1:index])
            body_text = "".join(lines[index + 1 :])
            return frontmatter_text, body_text

    return "", text


def parse_frontmatter_metadata(
    text: str,
    source_path: str | None = None,
) -> KnowledgeDocMetadata | None:
    frontmatter_text, _body_text = split_frontmatter(text)
    if not frontmatter_text:
        return None

    try:
        raw_metadata = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        raise ValueError("invalid YAML frontmatter") from exc

    if not isinstance(raw_metadata, dict):
        raise ValueError("frontmatter must contain a YAML mapping")

    metadata_values: dict[str, Any] = dict(raw_metadata)
    if source_path is not None:
        metadata_values["source_path"] = source_path

    return KnowledgeDocMetadata.model_validate(metadata_values)


def load_knowledge_metadata(path: str | Path) -> KnowledgeDocMetadata | None:
    doc_path = Path(path)
    text = doc_path.read_text(encoding="utf-8")
    return parse_frontmatter_metadata(text, source_path=doc_path.as_posix())


def load_metadata_from_directory(directory: str | Path) -> list[KnowledgeDocMetadata]:
    metadata_directory = Path(directory)
    if not metadata_directory.exists():
        return []

    doc_paths = [metadata_directory] if metadata_directory.is_file() else _iter_markdown_files(metadata_directory)
    metadata_items: list[KnowledgeDocMetadata] = []

    for doc_path in doc_paths:
        metadata = load_knowledge_metadata(doc_path)
        if metadata is not None:
            metadata_items.append(metadata)

    return metadata_items


def _iter_markdown_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.rglob("*.md")
        if path.is_file()
    )
