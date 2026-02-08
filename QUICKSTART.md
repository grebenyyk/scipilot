# Quick Start

Requires Python 3.13+.

## 1. Install

```bash
git clone https://github.com/grebenyyk/scipilot
cd scipilot
make install
```

## 2. Add Your Tools

Copy example and customize:
```bash
cp examples/raspa.yaml tools/my_tool.yaml
# Edit tools/my_tool.yaml with your actual binary paths
```

## 3. Run Server

### Option A: Standalone (testing)
```bash
make run
```

### Option B: Claude Desktop
```bash
make install-claude  # Shows config to add
```
Or manually add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "scipilot": {
      "command": "python",
      "args": ["-m", "scipilot.server", "--tools-dir", "./tools"],
      "cwd": "/absolute/path/to/scipilot"
    }
  }
}
```
Use absolute paths for `cwd` and `--tools-dir` if you launch from outside the project directory.

### Option C: VS Code (Copilot Chat / MCP)
Create `.vscode/mcp.json` in your workspace:
```json
{
  "servers": {
    "scipilot": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "scipilot.server", "--tools-dir", "./tools"]
    }
  }
}
```
Or use the provided `.vscode/mcp.json` and update paths to match your install location.

## 4. Test

```bash
make test
```

## Project Structure

```
scipilot/
├── scipilot/              # Source code
│   ├── __init__.py
│   ├── models.py          # Pydantic models for descriptors
│   ├── tool_loader.py     # Load YAML descriptors
│   ├── executor.py        # Run tools, parse outputs
│   └── server.py          # MCP server entry point
├── tests/                 # Unit tests
├── examples/              # Example tool descriptors
├── tools/                 # Your descriptors (gitignored)
├── README.md
├── pyproject.toml
└── Makefile
```

## Creating a Tool Descriptor

See `examples/raspa.yaml` for a complete example.

Minimal example:
```yaml
tool:
  name: mytool
  description: "My scientific tool"
  binary: "/path/to/mytool"

operations:
  - name: analyze
    description: "Run analysis"
    inputs:
      - name: input_file
        type: file
        required: true
        arg_template: "--input {value}"
    outputs:
      - name: result
        path: "{working_dir}/output.txt"
        type: text
    command_template: "{binary} {input_file} > {working_dir}/output.txt"
```

### Using Conda/Virtual Environments

If your tool runs in a specific conda environment:

```yaml
tool:
  name: pdfmc
  binary: "python -m pdfmc"
  environment:
    type: conda
    env_name: pdfenv  # Uses: conda run -n pdfenv python -m pdfmc ...
```

Or with explicit activation script:
```yaml
  environment:
    type: conda
    env_name: myenv
    activate_script: "/Users/you/opt/anaconda3/etc/profile.d/conda.sh"
```

Or direct python path (fastest):
```yaml
  environment:
    python_path: "/Users/you/opt/anaconda3/envs/pdfenv/bin/python"
```

Also supports `venv` and `pyenv` types.

## How It Works

1. **Load**: Server reads all YAML files from `tools/` directory
2. **Expose**: Each operation becomes an MCP tool (`toolname_operationname`)
3. **Execute**: LLM calls tool with parameters → MCP builds CLI command → runs subprocess
4. **Parse**: Output files parsed via regex/JSON paths → structured results returned to LLM

## Next Steps

- Customize `examples/raspa.yaml` for your tool
- Add more tools to `tools/` directory
- Extend executor with parallel execution, better error handling
