"""Lazy RAG provider used to keep startup paths lightweight.

The provider intentionally does not import ``modules.rag_qa`` at module import
time. The real RAG runtime is imported and constructed only when a RAG-facing
method is first called.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class LazyRAGQA:
    """Proxy for ``RAGQA`` that defers heavy RAG imports and initialization."""

    def __init__(self, factory: Callable[[], Any] | None = None) -> None:
        self._factory = factory
        self._instance: Any | None = None

    @property
    def is_initialized(self) -> bool:
        return self._instance is not None

    def _get_instance(self) -> Any:
        if self._instance is None:
            if self._factory is None:
                from modules.rag_qa import RAGQA

                self._instance = RAGQA()
            else:
                self._instance = self._factory()
        return self._instance

    def is_ready(self) -> bool:
        return bool(self._get_instance().is_ready())

    def is_security(self, query: str) -> bool:
        return bool(self._get_instance().is_security(query))

    def retrieve_context(self, query: str) -> Any:
        return self._get_instance().retrieve_context(query)

    def generate_answer(self, query: str, context: str, *args: Any, **kwargs: Any) -> Any:
        return self._get_instance().generate_answer(query, context, *args, **kwargs)

    def answer_question(self, query: str, *args: Any, **kwargs: Any) -> str | None:
        return self._get_instance().answer_question(query, *args, **kwargs)

    def explain_point(self, target: str) -> Any:
        return self._get_instance().explain_point(target)

    def handle_natural_followup(self, focus: str, question: str) -> Any:
        return self._get_instance().handle_natural_followup(focus, question)
