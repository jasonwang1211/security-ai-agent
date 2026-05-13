from collections.abc import Iterable

from modules.controller_types import InputKind, ToolSpec


class ToolRegistry:
    def __init__(self, tools: Iterable[ToolSpec] | None = None) -> None:
        self._tools: dict[str, ToolSpec] = {}
        if tools is not None:
            for tool in tools:
                self.register(tool)

    def register(self, tool: ToolSpec) -> None:
        if not isinstance(tool, ToolSpec):
            raise TypeError("tool must be a ToolSpec")
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def find_by_input_kind(self, input_kind: InputKind) -> list[ToolSpec]:
        return [tool for tool in self._tools.values() if input_kind in tool.allowed_input_kinds]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools


def build_empty_registry() -> ToolRegistry:
    return ToolRegistry()
