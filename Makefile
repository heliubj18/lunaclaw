.PHONY: install dev test lint format run

install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev,rag]"

test:
	pytest -v

lint:
	ruff check lunaclaw/ tests/

format:
	ruff format lunaclaw/ tests/

run:
	lunaclaw
