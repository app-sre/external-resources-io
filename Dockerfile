FROM registry.access.redhat.com/ubi9/python-311@sha256:d0b35f779ca0ae87deaf17cd1923461904f52d3ef249a53dbd487e02bdabdde6 AS base
COPY --from=ghcr.io/astral-sh/uv:0.9.7@sha256:ba4857bf2a068e9bc0e64eed8563b065908a4cd6bfb66b531a9c424c8e25e142 /uv /bin/uv
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
RUN make dev-venv


#
# Test image
#
FROM base AS test

# Install Terraform for testing
RUN curl -sfL https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip \
    -o terraform.zip && \
    unzip terraform.zip && \
    mkdir -p $HOME/bin && \
    mv terraform $HOME/bin/terraform && \
    rm terraform.zip

ENV PATH=$HOME/bin:$PATH
RUN make test


#
# PyPI publish image
#
FROM test AS pypi
# Secrets are owned by root and are not readable by others :(
USER root
RUN --mount=type=secret,id=app-sre-pypi-credentials/token make -s pypi
