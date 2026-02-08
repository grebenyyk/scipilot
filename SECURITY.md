# Security Policy

## Tool Descriptors Execute Shell Commands

**⚠️ CRITICAL**: Tool YAML files execute with full shell privileges. This is by design - SciPilot wraps command-line scientific tools that require shell access.

### What This Means

- Tool descriptors in `tools/` directory contain shell commands
- Input values are substituted directly into these commands
- Malicious or poorly written descriptors can execute arbitrary code

### Protecting Yourself

1. **Only load trusted descriptors** - Review any YAML file before placing it in `tools/`
2. **Don't expose MCP server publicly** - Run only on localhost or trusted networks
3. **Check descriptor sources** - Verify descriptors from GitHub repos, gists, etc.

## Reporting Security Issues

If you discover a security vulnerability, please report it privately:

1. Open a [security advisory](https://github.com/grebenyyk/scipilot/security/advisories/new) on GitHub

Do not open public issues for security bugs.

## Built-in Protections

- YAML files are limited to 1MB (protection against YAML bombs)
- `yaml.safe_load()` prevents arbitrary object deserialization
- Tool descriptors are loaded only from the configured `tools/` directory

## Known Limitations

- No sandboxing by default (scientific tools need full system access)
- No input sanitization (tool authors control their command templates)
- No network isolation

If you need to run untrusted descriptors, consider:
- Running SciPilot in a container/VM
- Using a sandboxed environment (firejail, bubblewrap)
- Reviewing all descriptors manually before loading
