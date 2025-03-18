FROM registry.access.redhat.com/ubi9/python-311@sha256:ae3c5e4857482fed9a04a9373eb5e852e52db4d32851a69ef1fc3ad2d48b256a AS base
COPY --from=ghcr.io/astral-sh/uv:0.6.8@sha256:cb641b1979723dc5ab87d61f079000009edc107d30ae7cbb6e7419fdac044e9f /uv /bin/uv
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
