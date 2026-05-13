from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Severity = Literal["LOW", "MEDIUM", "HIGH"]
MatchMode = Literal["substring"]


class DetectionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    attack_type: str
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    patterns: list[str]
    match_mode: MatchMode = "substring"
    case_sensitive: bool = False
    mitre_techniques: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    notes: str = ""
    enabled: bool = True
    source_path: str | None = None

    @field_validator("id", "title", "attack_type")
    @classmethod
    def required_strings_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must not be empty")
        return value

    @field_validator("patterns")
    @classmethod
    def patterns_must_be_non_empty_strings(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("patterns must not be empty")

        deduped_patterns: list[str] = []
        seen_patterns: set[str] = set()
        for pattern in value:
            if not pattern.strip():
                raise ValueError("patterns must not contain empty strings")
            if pattern not in seen_patterns:
                seen_patterns.add(pattern)
                deduped_patterns.append(pattern)

        return deduped_patterns

    @field_validator("mitre_techniques", "references")
    @classmethod
    def optional_lists_must_not_contain_empty_strings(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("list fields must not contain empty strings")
        return value

    def matches(self, text: str) -> list[str]:
        if not self.enabled:
            return []

        haystack = text if self.case_sensitive else text.lower()
        matched_patterns: list[str] = []

        for pattern in self.patterns:
            needle = pattern if self.case_sensitive else pattern.lower()
            if needle in haystack:
                matched_patterns.append(pattern)

        return matched_patterns
