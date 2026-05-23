from collections.abc import Callable, Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from modules.controller.registry import ToolRegistry
from modules.controller.skill_catalog import (
    INCIDENT_JSON_EXPORT,
    LOG_FILE_INGEST,
    PAYLOAD_TRIAGE,
    RAG_SECURITY_QA,
    RAW_LOG_TRANSLATE,
    REPORT_FOLLOWUP,
)
from modules.controller.types import (
    ControllerOutput,
    InputKind,
    RouterDecision,
    ToolExecutionResult,
    ToolSpec,
)

ToolHandler = Callable[[BaseModel], ToolExecutionResult]


def build_default_route_map() -> dict[str, str]:
    return {
        PAYLOAD_TRIAGE: PAYLOAD_TRIAGE,
        RAW_LOG_TRANSLATE: RAW_LOG_TRANSLATE,
        LOG_FILE_INGEST: LOG_FILE_INGEST,
        RAG_SECURITY_QA: RAG_SECURITY_QA,
        REPORT_FOLLOWUP: REPORT_FOLLOWUP,
        INCIDENT_JSON_EXPORT: INCIDENT_JSON_EXPORT,
        "mode_1": PAYLOAD_TRIAGE,
        "mode_2": LOG_FILE_INGEST,
        "mode_3": RAG_SECURITY_QA,
        "mode_4": REPORT_FOLLOWUP,
    }


class ControllerAgent:
    def __init__(
        self,
        registry: ToolRegistry,
        handlers: Mapping[str, ToolHandler],
        route_map: Mapping[str, str] | None = None,
    ) -> None:
        self._registry = registry
        self._handlers = dict(handlers)
        self._route_map = dict(route_map) if route_map is not None else build_default_route_map()

    def available_tools(self) -> list[str]:
        return self._registry.list_names()

    def can_handle(self, tool_name: str) -> bool:
        return self._registry.has(tool_name) and tool_name in self._handlers

    def dispatch_tool(
        self,
        tool_name: str,
        payload: dict[str, Any] | BaseModel,
    ) -> ControllerOutput:
        if not self._registry.has(tool_name):
            return self._error_output(
                message=f"Unknown tool: {tool_name}",
                selected_tool=None,
                route=self._unknown_route("No registered tool matched the requested name."),
            )

        tool = self._registry.get(tool_name)
        route = self._tool_route(tool)

        handler = self._handlers.get(tool_name)
        if handler is None:
            return self._error_output(
                message=f"No handler registered for tool: {tool_name}",
                selected_tool=tool_name,
                route=route,
            )

        try:
            validated_input = tool.input_model.model_validate(payload)
        except ValidationError as exc:
            return self._error_output(
                message="Tool input validation failed.",
                selected_tool=tool_name,
                route=route,
                details={"validation_error": str(exc)},
            )

        try:
            result = handler(validated_input)
        except Exception as exc:
            return self._error_output(
                message=str(exc),
                selected_tool=tool_name,
                route=route,
                warnings=[f"{tool_name} handler failed"],
            )

        try:
            validated_result = tool.output_model.model_validate(result)
        except ValidationError as exc:
            return self._error_output(
                message="Tool output validation failed.",
                selected_tool=tool_name,
                route=route,
                details={"validation_error": str(exc)},
            )

        if not isinstance(validated_result, ToolExecutionResult):
            return self._error_output(
                message="Tool output model must validate to ToolExecutionResult.",
                selected_tool=tool_name,
                route=route,
            )

        return ControllerOutput(
            status=validated_result.status,
            selected_tool=tool_name,
            response_text=self._response_text(validated_result),
            structured_result=validated_result.model_dump(),
            route=route,
            warnings=validated_result.warnings,
        )

    def dispatch_route(
        self,
        route: str,
        payload: dict[str, Any] | BaseModel,
    ) -> ControllerOutput:
        tool_name = self._route_map.get(route)
        if tool_name is None:
            return ControllerOutput(
                status="clarification_required",
                selected_tool=None,
                response_text=f"Unknown route: {route}",
                structured_result={"error_message": f"Unknown route: {route}"},
                route=self._unknown_route("No deterministic route matched the requested route."),
                warnings=[f"Unknown route: {route}"],
            )

        return self.dispatch_tool(tool_name, payload)

    @staticmethod
    def _first_input_kind(tool: ToolSpec) -> InputKind:
        return tool.allowed_input_kinds[0] if tool.allowed_input_kinds else "unknown"

    def _tool_route(self, tool: ToolSpec) -> RouterDecision:
        return RouterDecision(
            input_kind=self._first_input_kind(tool),
            selected_tool=tool.name,
            confidence="HIGH",
            reason="deterministic route/tool dispatch",
            requires_clarification=False,
        )

    @staticmethod
    def _unknown_route(reason: str) -> RouterDecision:
        return RouterDecision(
            input_kind="unknown",
            selected_tool=None,
            confidence="LOW",
            reason=reason,
            requires_clarification=True,
        )

    @staticmethod
    def _response_text(result: ToolExecutionResult) -> str:
        text = result.output.get("text")
        if isinstance(text, str) and text.strip():
            return text
        if result.error_message:
            return result.error_message
        return "Tool execution completed."

    @staticmethod
    def _error_output(
        message: str,
        selected_tool: str | None,
        route: RouterDecision,
        warnings: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> ControllerOutput:
        structured_result = {"error_message": message}
        if details is not None:
            structured_result.update(details)
        return ControllerOutput(
            status="error",
            selected_tool=selected_tool,
            response_text=message,
            structured_result=structured_result,
            route=route,
            warnings=warnings or [message],
        )
