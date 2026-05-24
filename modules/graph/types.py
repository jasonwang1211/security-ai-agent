from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class GraphNodeKind(str, Enum):
    INCIDENT = "INCIDENT"
    EVIDENCE = "EVIDENCE"
    FINDING = "FINDING"
    DETECTION_RULE = "DETECTION_RULE"
    ATTACK_TYPE = "ATTACK_TYPE"
    KNOWLEDGE_DOC = "KNOWLEDGE_DOC"
    RISK_LEVEL = "RISK_LEVEL"
    DECISION = "DECISION"

    # Deferred vocabulary only. No v2.0 behavior is attached to these values.
    MITRE_TECHNIQUE = "MITRE_TECHNIQUE"
    SECURITY_CONTROL = "SECURITY_CONTROL"
    RESPONSE_PLAYBOOK = "RESPONSE_PLAYBOOK"


class GraphEdgeKind(str, Enum):
    HAS_EVIDENCE = "HAS_EVIDENCE"
    HAS_FINDING = "HAS_FINDING"
    SUPPORTED_BY = "SUPPORTED_BY"
    MAPS_TO_RULE = "MAPS_TO_RULE"
    DETECTS = "DETECTS"
    RELATED_TO_ATTACK = "RELATED_TO_ATTACK"
    HAS_RISK_LEVEL = "HAS_RISK_LEVEL"
    HAS_DECISION = "HAS_DECISION"
    REFERENCES_DOC = "REFERENCES_DOC"
    RELATED_TO = "RELATED_TO"

    # Deferred vocabulary only. No v2.0 behavior is attached to these values.
    MAPS_TO_MITRE = "MAPS_TO_MITRE"
    MITIGATED_BY = "MITIGATED_BY"
    HAS_PLAYBOOK = "HAS_PLAYBOOK"


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class GraphSourceRef(BaseModel):
    source_type: str
    source_id: str
    field_path: str | None = None
    reason: str | None = None

    @field_validator("source_type", "source_id")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "required text")

    @field_validator("field_path", "reason")
    @classmethod
    def optional_text_must_not_be_empty(cls, value: str | None) -> str | None:
        if value is not None:
            return _require_non_blank(value, "optional text")
        return value


class GraphNode(BaseModel):
    id: str
    kind: GraphNodeKind
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    sources: list[GraphSourceRef] = Field(default_factory=list)

    @field_validator("id", "label")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "required text")


class GraphEdge(BaseModel):
    id: str
    kind: GraphEdgeKind
    source_node_id: str
    target_node_id: str
    label: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    sources: list[GraphSourceRef] = Field(default_factory=list)

    @field_validator("id", "source_node_id", "target_node_id")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "required text")

    @field_validator("label")
    @classmethod
    def optional_text_must_not_be_empty(cls, value: str | None) -> str | None:
        if value is not None:
            return _require_non_blank(value, "optional text")
        return value


class GraphSnapshot(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
