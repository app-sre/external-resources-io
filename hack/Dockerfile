FROM registry.access.redhat.com/ubi9/python-311:latest

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
