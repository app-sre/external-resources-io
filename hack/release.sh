#!/usr/bin/env bash
BASEPATH=/opt/app-root/src

git config --global --add safe.directory $BASEPATH

pip install --upgrade pip
pip install -r $BASEPATH/requirements.txt
poetry self add "poetry-dynamic-versioning[plugin]"
poetry build
poetry publish
