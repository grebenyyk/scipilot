"""MCP server entry point."""

from __future__ import annotations
import argparse
import inspect
from pathlib import Path
from typing import Any, Callable

from fastmcp import FastMCP

from .executor import ToolExecutor
from .models import ToolDescriptor, Operation
from .tool_loader import ToolRegistry


def create_tool_function(
    tool: ToolDescriptor,
    operation: Operation,
    executor: ToolExecutor,
) -> Callable[..., dict[str, Any]]:
    """Create a function with proper signature for FastMCP using inspect.Signature."""

    func_name = f"{tool.name}_{operation.name}"

    # Build docstring
    lines = [operation.description, "", f"Tool: {tool.name}", f"Operation: {operation.name}", ""]
    if operation.inputs:
        lines.append("Parameters:")
        for inp in operation.inputs:
            req_str = "required" if inp.required else f"optional, default={inp.default}"
            lines.append(f"    {inp.name} ({inp.type}, {req_str}): {inp.description}")
    docstring = "\n".join(lines)

    # Create the underlying implementation function
    def _impl(**kwargs: Any) -> dict[str, Any]:
        result = executor.execute(tool, operation, kwargs)
        return result.to_dict()

    if not operation.inputs:
        # No inputs - simple function
        def tool_func() -> dict[str, Any]:
            """No inputs."""
            return _impl()

        tool_func.__name__ = func_name
        tool_func.__doc__ = docstring
        return tool_func

    # Build inspect.Parameter objects for each input
    params = []
    for inp in operation.inputs:
        if inp.required:
            default = inspect.Parameter.empty
        elif inp.default is not None:
            default = inp.default
        else:
            default = None

        param = inspect.Parameter(
            name=inp.name,
            kind=inspect.Parameter.KEYWORD_ONLY
            if not inp.required
            else inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
        )
        params.append(param)

    sig = inspect.Signature(params)

    # Create a generic handler that routes to _impl
    def make_handler(input_names: list[str]) -> Callable[..., dict[str, Any]]:
        def handler(**kwargs: Any) -> dict[str, Any]:
            return _impl(**kwargs)

        return handler

    handler = make_handler([inp.name for inp in operation.inputs])
    setattr(handler, "__signature__", sig)
    handler.__name__ = func_name
    handler.__doc__ = docstring

    return handler


def create_server(tools_dir: Path) -> FastMCP:
    """Create and configure MCP server."""

    # Load tools
    registry = ToolRegistry(tools_dir)
    registry.load_all()

    # Create executor
    executor = ToolExecutor()

    # Create MCP server
    mcp = FastMCP("scipilot")

    # Add introspection tools
    @mcp.tool()
    def list_available_tools() -> list[dict[str, Any]]:
        """List all available tools and their operations."""
        result = []
        for tool in registry.list_tools():
            result.append(
                {
                    "name": tool.name,
                    "description": tool.tool.description,
                    "binary": tool.tool.binary,
                    "operations": [
                        {"name": op.name, "description": op.description} for op in tool.operations
                    ],
                }
            )
        return result

    @mcp.tool()
    def get_operation_details(tool_name: str, operation_name: str) -> dict[str, Any]:
        """Get detailed info about a specific operation (inputs, outputs, etc.)."""
        tool = registry.get(tool_name)
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}

        operation = next((op for op in tool.operations if op.name == operation_name), None)
        if not operation:
            return {"error": f"Operation not found: {operation_name}"}

        return {
            "tool": tool_name,
            "operation": operation_name,
            "description": operation.description,
            "inputs": [
                {
                    "name": inp.name,
                    "type": inp.type,
                    "required": inp.required,
                    "description": inp.description,
                    "default": inp.default,
                }
                for inp in operation.inputs
            ],
            "outputs": [
                {
                    "name": out.name,
                    "type": out.type,
                    "description": out.description,
                }
                for out in operation.outputs
            ],
        }

    # Dynamically add tools from registry
    for tool in registry.list_tools():
        for operation in tool.operations:
            tool_func = create_tool_function(tool, operation, executor)
            mcp.tool(name=tool_func.__name__)(tool_func)

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="SciPilot - MCP for Scientific CLI Tools")
    parser.add_argument(
        "--tools-dir",
        type=Path,
        default=Path("./tools"),
        help="Directory containing tool YAML descriptors",
    )
    parser.add_argument(
        "--transport", choices=["stdio", "sse"], default="stdio", help="MCP transport mode"
    )
    args = parser.parse_args()

    mcp = create_server(args.tools_dir)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
