import json
from pathlib import Path
from typing import Any

import pytest

from external_resources_io.input import (
    AppInterfaceProvision,
    TerraformProvisionOptions,
    read_input_from_file,
)


def test_parse_provision(provision_data: AppInterfaceProvision) -> None:
    assert isinstance(provision_data, AppInterfaceProvision)
    assert isinstance(provision_data.module_provision_data, TerraformProvisionOptions)
    assert provision_data.module_provision_data.tf_state_region == "us-east-1"


def test_read_input_from_file_env_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, ai_data: dict[str, Any]
) -> None:
    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(ai_data))
    monkeypatch.setenv("ER_INPUT_FILE", str(input_json.absolute()))

    input_data = read_input_from_file()
    assert input_data == ai_data


def test_read_input_from_file(tmp_path: Path, ai_data: dict[str, Any]) -> None:
    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(ai_data))

    input_data = read_input_from_file(file_path=str(input_json.absolute()))
    assert input_data == ai_data
