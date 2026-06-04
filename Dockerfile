FROM registry.access.redhat.com/ubi10/python-314-minimal@sha256:01ed8ebbd639975c17850afb188757e819c538c5d907ccf7d36fb8634eccca69 AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.19@sha256:b46b03ddfcfbf8f547af7e9eaefdf8a39c8cebcba7c98858d3162bd28cf536f6 /uv /bin/uv
COPY LICENSE /licenses/

ENV \
    # use venv from ubi image
    UV_PROJECT_ENVIRONMENT=$APP_ROOT \
    # disable uv cache. it doesn't make sense in a container
    UV_NO_CACHE=true

USER 0
# Install dependencies
RUN INSTALL_PKGS="make unzip" && \
    microdnf -y --nodocs --setopt=install_weak_deps=0 install $INSTALL_PKGS && \
    microdnf clean all && \
    rm -rf /var/cache/yum
USER 1001

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
ENV TF_VERSION="1.13.4"
ARG TARGETARCH
RUN curl -sfL https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_${TARGETARCH}.zip \
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
