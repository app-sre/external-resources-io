FROM registry.access.redhat.com/ubi9/python-311@sha256:47107ded2aac95702535be963e2718e58d45bcecb3d4e582bd58bd35f6fc6bc3 AS base
COPY --from=ghcr.io/astral-sh/uv:0.5.23@sha256:f557ee6c33abbdb0a43e93442781531ad2e71fe2e3c53ca2b0731a76e492f643 /uv /bin/uv
COPY LICENSE /licenses/

ENV \
    # use venv from ubi image
    UV_PROJECT_ENVIRONMENT=$APP_ROOT \
    # disable uv cache. it doesn't make sense in a container
    UV_NO_CACHE=true

COPY pyproject.toml uv.lock README.md Makefile ./
# Test lock file is up to date
RUN uv lock --locked

COPY tests ./tests
COPY external_resources_io ./external_resources_io
RUN uv sync --frozen


#
# Test image
#
FROM base AS test
RUN make test


#
# PyPI publish image
#
FROM test AS pypi
# Secrets are owned by root and are not readable by others :(
USER root
RUN --mount=type=secret,id=app-sre-pypi-credentials/token make -s pypi
