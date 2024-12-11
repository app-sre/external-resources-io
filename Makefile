.PHONY: format
format:
	uv run ruff check
	uv run ruff format

.PHONY: test
test:
	uv run --frozen ruff check --no-fix
	uv run --frozen ruff format --check
	uv run --frozen mypy
	uv run --frozen pytest --cov=external_resources_io --cov-report=term-missing --cov-report xml

.PHONY: dev-venv
dev-venv:
	uv sync --python 3.11

# do not print pypi commands to avoid the token leaking to the logs
.SILENT: pypi
.PHONY: pypi
pypi:
	uv build --sdist --wheel
	UV_PUBLISH_TOKEN=$(shell cat /run/secrets/app-sre-pypi-credentials/token) \
		uv publish
