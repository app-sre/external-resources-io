#!/usr/bin/env bash
BASEPATH=/opt/app-root/src
git config --global --add safe.directory $BASEPATH

poetry env use /opt/app-root/bin/python
poetry config pypi-token.pypi $TWINE_PASSWORD
poetry self add "poetry-dynamic-versioning[plugin]"
poetry build
poetry publish --skip-existing
