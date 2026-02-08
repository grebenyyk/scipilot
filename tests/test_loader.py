"""Tests for scipilot."""

import pytest
from pathlib import Path

from scipilot.models import InputSpec, Operation, ToolDescriptor, ToolMetadata
from scipilot.tool_loader import ToolRegistry


def test_load_example_tool():
    """Test loading example RASPA descriptor."""
    registry = ToolRegistry(Path("./examples"))
    tools = registry.load_all()

    assert "raspa" in registry._tools
    raspa = registry.get("raspa")
    assert raspa.tool.name == "raspa"
    assert len(raspa.operations) >= 1

    # Check operation exists
    op_names = [op.name for op in raspa.operations]
    assert "run_helium_void_fraction" in op_names


def test_operation_inputs():
    """Test input spec parsing."""
    op = Operation(
        name="test",
        description="Test operation",
        command_template="cmd {input1} {input2}",
        inputs=[
            InputSpec(name="input1", type="string", required=True),
            InputSpec(name="input2", type="float", required=False, default=1.0),
        ],
    )

    assert len(op.inputs) == 2
    assert op.inputs[0].required is True
    assert op.inputs[1].default == 1.0
