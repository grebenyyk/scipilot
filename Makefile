.PHONY: install test run clean format lint

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

run:
	python -m scipilot.server --tools-dir ./examples

format:
	ruff format .

lint:
	ruff check . --fix
	mypy scipilot/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	rm -rf runs/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# For Claude Desktop MCP setup
install-claude:
	@echo "Add this to your Claude Desktop config (~/Library/Application Support/Claude/claude_desktop_config.json):"
	@echo ''
	@cat claude_desktop_config.json
