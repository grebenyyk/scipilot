"""Execute tools and parse outputs."""

from __future__ import annotations
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from .models import EnvironmentConfig, Operation, OutputSpec, ToolDescriptor


class ExecutionResult:
    """Result of a tool execution."""

    def __init__(
        self,
        success: bool,
        stdout: str = "",
        stderr: str = "",
        return_code: int = 0,
        outputs: Optional[dict[str, Any]] = None,
        run_id: str = "",
    ):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.outputs = outputs or {}
        self.run_id = run_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "return_code": self.return_code,
            "outputs": self.outputs,
            "run_id": self.run_id,
            "stderr_preview": self.stderr[:500] if self.stderr else None,
        }


class ToolExecutor:
    """Execute tools based on descriptors."""

    def __init__(self, base_working_dir: Union[Path, str] = "./runs"):
        self.base_working_dir = Path(base_working_dir)
        self.base_working_dir.mkdir(parents=True, exist_ok=True)

    def execute(
        self, tool: ToolDescriptor, operation: Operation, inputs: dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single operation."""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        working_dir = self.base_working_dir / f"{tool.name}_{operation.name}_{run_id}"
        working_dir.mkdir(parents=True, exist_ok=True)

        # Build command
        command = self._build_command(tool, operation, inputs, working_dir, run_id)

        # Execute
        try:
            # SECURITY: shell=True with command built from tool YAML + user inputs.
            # Tool descriptors are trusted code. Only load descriptors you wrote/reviewed.
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=operation.timeout,
            )

            # Parse outputs
            outputs = self._parse_outputs(operation, working_dir, result.stdout, result.stderr)

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                outputs=outputs,
                run_id=str(working_dir),
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stderr=f"Timeout after {operation.timeout} seconds",
                return_code=-1,
                run_id=str(working_dir),
            )
        except Exception as e:
            return ExecutionResult(
                success=False, stderr=str(e), return_code=-1, run_id=str(working_dir)
            )

    def _build_command(
        self,
        tool: ToolDescriptor,
        operation: Operation,
        inputs: dict[str, Any],
        working_dir: Path,
        run_id: str,
    ) -> str:
        """Build command from template and inputs."""
        # Prepare template variables
        template_vars = {
            "working_dir": str(working_dir),
            "run_id": run_id,
        }

        # Add binary from tool metadata
        template_vars["binary"] = tool.tool.binary

        # Add inputs with their arg_templates
        for input_spec in operation.inputs:
            value = inputs.get(input_spec.name)
            if value is None:
                value = input_spec.default

            if value is not None:
                # Format according to arg_template
                formatted = input_spec.arg_template.format(value=value)
                template_vars[input_spec.name] = formatted
            else:
                template_vars[input_spec.name] = ""

        # Build base command
        command = operation.command_template.format(**template_vars)

        # Wrap with environment if configured
        if tool.tool.environment:
            command = self._wrap_with_environment(command, tool.tool.environment)

        return command

    def _wrap_with_environment(self, command: str, env: EnvironmentConfig) -> str:
        """Wrap command with conda/venv activation."""
        if env.python_path:
            # Use direct python path (simplest)
            # Replace 'python' or binary with full path
            return command.replace("python", env.python_path, 1)

        if env.type == "conda":
            if env.activate_script:
                # Source conda.sh then activate in bash so conda functions are available.
                return (
                    "bash -lc '"
                    f'source "{env.activate_script}" && '
                    f"conda activate {env.env_name} && "
                    f"{command}"
                    "'"
                )
            else:
                # Use conda run (cleaner, no shell state issues)
                return f"conda run -n {env.env_name} --no-capture-output {command}"

        elif env.type == "venv":
            # Activate venv
            activate_path = f"{env.env_name}/bin/activate"
            return f'source "{activate_path}" && {command}'

        elif env.type == "pyenv":
            return f"PYENV_VERSION={env.env_name} {command}"

        return command

    def _parse_outputs(
        self, operation: Operation, working_dir: Path, stdout: str, stderr: str
    ) -> dict[str, Any]:
        """Extract outputs according to specs."""
        outputs = {}

        for spec in operation.outputs:
            try:
                value = self._extract_output(spec, working_dir, stdout, stderr)
                outputs[spec.name] = value
            except Exception as e:
                outputs[spec.name] = f"<extraction error: {e}>"

        return outputs

    def _extract_output(self, spec: OutputSpec, working_dir: Path, stdout: str, stderr: str) -> Any:
        """Extract single output value."""
        # Resolve path (may contain wildcards)
        path_pattern = spec.path.format(working_dir=str(working_dir))

        if "*" in path_pattern:
            import glob

            files = glob.glob(path_pattern)
            if not files:
                return None
            content_path = Path(files[0])
        else:
            content_path = Path(path_pattern)

        # Read content
        if content_path.exists():
            content = content_path.read_text()
        else:
            # Try stdout if file not found
            content = stdout

        # Extract based on type
        if spec.type == "text":
            return content[:10000]  # Limit size

        elif spec.type == "float" and spec.extract_pattern:
            match = re.search(spec.extract_pattern, content)
            if match:
                return float(match.group(1))
            return None

        elif spec.type == "integer" and spec.extract_pattern:
            match = re.search(spec.extract_pattern, content)
            if match:
                return int(match.group(1))
            return None

        elif spec.type == "json":
            import json

            try:
                data = json.loads(content)
                if spec.json_path:
                    # Navigate path like "results.energy"
                    parts = spec.json_path.split(".")
                    for part in parts:
                        data = data.get(part, {})
                    return data
                return data
            except json.JSONDecodeError:
                return None

        return content
