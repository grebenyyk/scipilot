"""Pydantic models for tool descriptors."""

from __future__ import annotations
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class EnvironmentConfig(BaseModel):
    """Conda or virtual environment configuration."""

    type: Literal["conda", "venv", "pyenv"] = Field(default="conda", description="Environment type")
    env_name: str = Field(description="Name of the conda env or path to venv")
    activate_script: Optional[str] = Field(
        default=None, description="Path to conda.sh (for conda) or activate script"
    )
    python_path: Optional[str] = Field(
        default=None, description="Direct path to python binary (alternative to activation)"
    )


class ToolMetadata(BaseModel):
    """Tool identification and metadata."""

    name: str = Field(description="Unique tool identifier")
    version: Optional[str] = Field(default=None, description="Tool version")
    description: str = Field(description="Human-readable description")
    binary: str = Field(description="Command to invoke (can include path)")
    working_directory: str = Field(
        default="./runs", description="Base directory for tool execution"
    )
    environment: Optional[EnvironmentConfig] = Field(
        default=None, description="Optional conda/venv environment configuration"
    )


class InputSpec(BaseModel):
    """Specification for one input parameter."""

    name: str
    type: Literal["string", "integer", "float", "boolean", "file", "choice", "array"]
    required: bool = True
    description: str = ""

    # For file type
    extensions: Optional[List[str]] = None

    # For choice type
    options: Optional[List[str]] = None

    # For numeric types
    min: Optional[float] = None
    max: Optional[float] = None
    unit: Optional[str] = None

    # Default value
    default: Optional[Any] = None

    # How to format in command line
    arg_template: str = Field(
        default="{value}", description="Template for CLI argument, e.g., '--temp {value}'"
    )


class OutputSpec(BaseModel):
    """Specification for output extraction."""

    name: str
    path: str = Field(description="Path pattern, can use {placeholders}")
    type: Literal["text", "json", "csv", "float", "integer", "boolean", "image"]
    description: str = ""

    # For regex extraction
    extract_pattern: Optional[str] = None

    # For JSON extraction
    json_path: Optional[str] = None  # e.g., "results.energy"


class Operation(BaseModel):
    """One callable operation for this tool."""

    name: str
    description: str
    inputs: list[InputSpec] = Field(default_factory=list)
    outputs: list[OutputSpec] = Field(default_factory=list)

    # Command construction
    command_template: str = Field(
        description="Template for command line, uses {input_name} placeholders"
    )

    # Execution mode
    execution_mode: Literal["serial", "parallel"] = "serial"

    # Timeout in seconds
    timeout: int = 3600


class ToolDescriptor(BaseModel):
    """Complete tool description from YAML."""

    tool: ToolMetadata
    operations: list[Operation]

    @property
    def name(self) -> str:
        return self.tool.name
