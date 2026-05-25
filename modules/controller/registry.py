"""Explicit typed tool registry for controller helpers.

This registry stores provided ToolSpec objects only; it does not perform dynamic
tool discovery or runtime auto-registration.
"""

from collections.abc import Iterable

from modules.controller.types import InputKind, ToolSpec


class ToolRegistry:
    """In-memory registry keyed by explicit tool names."""

    def __init__(self, tools: Iterable[ToolSpec] | None = None) -> None:
        self._tools: dict[str, ToolSpec] = {}
        if tools is not None:
            for tool in tools:
                self.register(tool)

    def register(self, tool: ToolSpec) -> None:
        """Register one ToolSpec, rejecting duplicates and non-spec objects."""

        if not isinstance(tool, ToolSpec):
            raise TypeError("tool must be a ToolSpec")
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        """Return a registered ToolSpec by name."""

        return self._tools[name]

    def has(self, name: str) -> bool:
        """Return whether a tool name is registered."""

        return name in self._tools

    def list_tools(self) -> list[ToolSpec]:
        """Return registered ToolSpec objects in insertion order."""

        return list(self._tools.values())

    def list_names(self) -> list[str]:
        """Return registered tool names in insertion order."""

        return list(self._tools.keys())

    def find_by_input_kind(self, input_kind: InputKind) -> list[ToolSpec]:
        """Return registered tools that accept the requested input kind."""

        return [tool for tool in self._tools.values() if input_kind in tool.allowed_input_kinds]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools


def build_empty_registry() -> ToolRegistry:
    """Create an empty explicit ToolRegistry."""

    return ToolRegistry()
