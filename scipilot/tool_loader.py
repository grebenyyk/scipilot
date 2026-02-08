"""Load and manage tool descriptors from YAML files."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Union

import yaml

from .models import ToolDescriptor


MAX_YAML_SIZE = 1024 * 1024  # 1MB - protect against YAML bombs


class ToolRegistry:
    """Registry of loaded tool descriptors."""

    def __init__(self, tools_dir: Union[Path, str]):
        self.tools_dir = Path(tools_dir)
        self._tools: dict[str, ToolDescriptor] = {}

    def load_all(self) -> dict[str, ToolDescriptor]:
        """Load all YAML files from tools directory."""
        self._tools = {}

        if not self.tools_dir.exists():
            print(f"Warning: Tools directory not found: {self.tools_dir}")
            return self._tools

        for yaml_file in self.tools_dir.glob("*.yaml"):
            try:
                tool = self._load_file(yaml_file)
                self._tools[tool.name] = tool
                print(f"Loaded tool: {tool.name}")
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")

        return self._tools

    def _load_file(self, path: Path) -> ToolDescriptor:
        """Parse single YAML file."""
        if path.stat().st_size > MAX_YAML_SIZE:
            raise ValueError(f"YAML file too large ({path.stat().st_size} bytes): {path}")
        with open(path) as f:
            data: Any = yaml.safe_load(f)
        return ToolDescriptor(**data)

    def get(self, name: str) -> Optional[ToolDescriptor]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDescriptor]:
        """List all loaded tools."""
        return list(self._tools.values())

    def list_operations(self) -> list[tuple[str, str]]:
        """List (tool_name, operation_name) pairs."""
        result = []
        for tool in self._tools.values():
            for op in tool.operations:
                result.append((tool.name, op.name))
        return result
