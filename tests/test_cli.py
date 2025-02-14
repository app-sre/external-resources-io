# ruff: noqa: PLC2701
import json
from pathlib import Path

import pytest
from pydantic import BaseModel
from typer.testing import CliRunner

from external_resources_io.cli import (
    _get_ai_input,
    _get_app_interface_class,
    _get_app_interface_data_class,
    tf_app,
)
from external_resources_io.input import AppInterfaceProvision


class Data(BaseModel):
    name: str


class AppInterfaceInput(BaseModel):
    """Test model for generation"""

    data: Data
    provision: AppInterfaceProvision


@pytest.fixture
def ai_model() -> type[BaseModel]:
    return AppInterfaceInput


@pytest.fixture
def app_interface_input_class(ai_model: type[BaseModel]) -> str:
    return ai_model.__module__ + "." + ai_model.__name__


@pytest.fixture
def input_file(tmp_path: Path) -> Path:
    input_file = tmp_path / "input.json"
    input_file.write_text(
        json.dumps({
            "data": {"name": "example-01"},
            "provision": {
                "provision_provider": "aws",
                "provisioner": "aws-account-01",
                "provider": "elasticache",
                "identifier": "elasticache-example-01",
                "target_cluster": "cluster-01",
                "target_namespace": "elasticache-01",
                "target_secret_name": "elasticache-example-01",
                "module_provision_data": {
                    "tf_state_bucket": "dev",
                    "tf_state_region": "us-east-1",
                    "tf_state_dynamodb_table": "terraform-lock",
                    "tf_state_key": "terraform.tfstate",
                },
            },
        })
    )
    return input_file


@pytest.fixture
def output_file(tmp_path: Path) -> Path:
    return tmp_path / "output.tf"


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


def test_get_app_interface_class(
    ai_model: type[BaseModel], app_interface_input_class: str
) -> None:
    assert _get_app_interface_class(app_interface_input_class) == ai_model


def test_get_app_interface_data_class(app_interface_input_class: str) -> None:
    assert _get_app_interface_data_class(app_interface_input_class) == Data


def test_get_ai_input(
    ai_model: type[BaseModel], app_interface_input_class: str, input_file: Path
) -> None:
    ai_input = _get_ai_input(app_interface_input_class, input_file)
    assert isinstance(ai_input, ai_model)


def test_generate_variables_tf(
    cli_runner: CliRunner, app_interface_input_class: str, output_file: Path
) -> None:
    cli_runner.invoke(
        tf_app,
        [
            "generate-variables-tf",
            app_interface_input_class,
            "--output",
            str(output_file),
        ],
    )
    assert output_file.exists()


def test_generate_variables_tf_json(
    cli_runner: CliRunner, app_interface_input_class: str, output_file: Path
) -> None:
    cli_runner.invoke(
        tf_app,
        [
            "generate-variables-tf-json",
            app_interface_input_class,
            "--output",
            str(output_file),
        ],
    )
    assert output_file.exists()


def test_generate_backend_tf(
    cli_runner: CliRunner,
    app_interface_input_class: str,
    input_file: Path,
    output_file: Path,
) -> None:
    cli_runner.invoke(
        tf_app,
        [
            "generate-backend-tf",
            app_interface_input_class,
            str(input_file),
            "--output",
            str(output_file),
        ],
    )
    assert output_file.exists()


def test_generate_tf_vars_json(
    cli_runner: CliRunner,
    app_interface_input_class: str,
    input_file: Path,
    output_file: Path,
) -> None:
    cli_runner.invoke(
        tf_app,
        [
            "generate-tf-vars-json",
            app_interface_input_class,
            str(input_file),
            "--output",
            str(output_file),
        ],
    )
    assert output_file.exists()
