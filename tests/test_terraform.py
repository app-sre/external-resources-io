import subprocess
from pathlib import Path

import pytest
from pydantic import BaseModel

from external_resources_io.config import get_env_var_name
from external_resources_io.input import AppInterfaceProvision
from external_resources_io.terraform.generators import (
    create_backend_tf_file,
    create_tf_vars_json,
    terraform_fmt,
)


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    return tmp_path / "temp.tf"


def test_tf_vars_json(data: BaseModel, temp_file: Path) -> None:
    create_tf_vars_json(data, temp_file)
    assert temp_file.read_text() == (
        '{"identifier":"test-external-resources-iam-role","assume_role":{"aws":"null","service":["ec2.amazonaws.com"],"federated":"null"},"inline_policy":"{\\"Version\\":\\"2012-10-17\\",\\"Statement\\":[{\\"Effect\\":\\"Allow\\",\\"Action\\":[\\"ec2:DescribeVpcs\\"],\\"Resource\\":[\\"*\\"]}]}","output_resource_name":"test-external-resources","region":"us-east-1"}'
    )


def test_tf_vars_json_output_env_var(
    data: BaseModel, temp_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(get_env_var_name("tf_vars_file"), str(temp_file))
    create_tf_vars_json(data)
    assert temp_file.exists()


def test_create_backend_tf_file(
    provision_data: AppInterfaceProvision, temp_file: Path
) -> None:
    create_backend_tf_file(provision_data, temp_file)
    expected_text = """\
terraform {
  backend "s3" {
    bucket         = "test-external-resources-state"
    key            = "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"
    region         = "us-east-1"
    dynamodb_table = "test-external-resources-lock"
    profile        = "external-resources-state"
  }
}
"""
    assert temp_file.read_text() == expected_text == terraform_fmt(expected_text)
    subprocess.run(["terraform", f"-chdir={temp_file.parent}", "validate"], check=True)


def test_create_backend_tf_file_output_env_var(
    provision_data: AppInterfaceProvision,
    temp_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(get_env_var_name("backend_tf_file"), str(temp_file))
    create_backend_tf_file(provision_data)
    assert temp_file.exists()
