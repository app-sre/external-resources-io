CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)

.PHONY: test
test:
	$(CONTAINER_ENGINE) build --progress plain -f Dockerfile .

.PHONY: dev-venv
dev-venv:
	uv sync --python 3.11

.PHONY: unittests
unittests:
	uv run ruff check --no-fix
	uv run ruff format --check
	uv run mypy
	uv run pytest --cov=reconcile --cov-report=term-missing --cov-report xml
