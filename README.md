# SciPilot

Natural language interface for scientific command-line tools via Model Context Protocol (MCP).

![scipilot](assets/scipilot.png)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io/)

SciPilot bridges the gap between natural language and scientific CLI tools. Define your tool once in YAML, then let LLMs handle the rest — parameters, file paths, output parsing, the works. Works for any command-line worth talking to.

## Quick Start

```bash
git clone https://github.com/grebenyyk/scipilot
cd scipilot
pip install -e .
scipilot --tools-dir ./tools
```

## Usage

1. Add tool descriptors to `tools/` (see `examples/raspa.yaml`)
2. Connect MCP client (Claude Desktop, VS Code, etc.)
3. Ask in natural language:
   - "Run a helium void fraction calculation on MIL-47 at 298 K"
   - "Compare results from yesterday's simulations"

## Tool Descriptor Format

You write a tool descriptor — a YAML file that tells SciPilot:

• What your tool expects (inputs, types, defaults)
• How to build the command (templates)
• Where to find the output (file paths, regex patterns)
SciPilot exposes these as MCP tools that any LLM can call.

```yaml
tool:
  name: mytool
  binary: mytool
  
operations:
  - name: run_simulation
    description: "Run a simulation"
    inputs:
      - name: input_file
        type: file
        required: true
    outputs:
      - name: result
        path: "output.txt"
        extract_pattern: "Result: ([0-9.]+)"
```

See `examples/` for complete tool descriptors.

## Project Structure

```
scipilot/
├── server.py          # MCP server entry point
├── tool_loader.py     # YAML parsing, tool discovery
├── executor.py        # Subprocess execution, output parsing
└── models.py          # Dataclasses for tool descriptors

tools/                 # Your tool descriptors (gitignored)
examples/              # Example descriptors
```

## Development

```bash
# Run tests
pytest

# Type checking
mypy scipilot/

# Format
ruff format .
```

> ⚠️ **Security Note**: Tool YAML files execute with full shell privileges. Only load tool descriptors you trust and have reviewed. User inputs are substituted directly into shell command templates.

## License

MIT
