FROM registry.access.redhat.com/ubi10/python-314-minimal@sha256:0c5b5d198178280e65577e63251ee5ee49435e1a711bef4e4b5b471723e0ed3c AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.18@sha256:78bc42400d77b0678ba95765305c826652ed5431f399257271dda681d0318f03 /uv /bin/uv
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
