#!/usr/bin/env bash
poetry env use /opt/app-root/bin/python
poetry run python -m pytest -v
