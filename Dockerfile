FROM registry.access.redhat.com/ubi9/python-311:latest
COPY --from=ghcr.io/astral-sh/uv:0.5.7@sha256:23272999edd22e78195509ea3fe380e7632ab39a4c69a340bedaba7555abe20a /uv /bin/uv

COPY README.md requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    poetry install

COPY .git .git
COPY external_resources_io external_resources_io
COPY hack hack
COPY tests tests
# dynamic versioning writes to pyproject.toml
COPY --chmod=666 pyproject.toml ./
