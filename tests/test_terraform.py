import tempfile
from pathlib import Path

from pydantic import BaseModel

from external_resources_io.input import AppInterfaceProvision
from external_resources_io.terraform.generators import (
    create_backend_tf_file,
    create_tf_vars_json,
    terraform_fmt,
)


def test_tf_vars_json(data: BaseModel) -> None:
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        create_tf_vars_json(data, temp_file.name)
        assert temp_file.read().decode("utf-8") == (
            '{"identifier":"test-external-resources-iam-role","assume_role":{"aws":"null","service":["ec2.amazonaws.com"],"federated":"null"},"inline_policy":"{\\"Version\\":\\"2012-10-17\\",\\"Statement\\":[{\\"Effect\\":\\"Allow\\",\\"Action\\":[\\"ec2:DescribeVpcs\\"],\\"Resource\\":[\\"*\\"]}]}","output_resource_name":"test-external-resources","region":"us-east-1"}'
        )


def test_create_tf_vars_json_env_var(tmp_path: Path, data: BaseModel) -> None:
    temp_file = tmp_path / "temp.tf"
    create_tf_vars_json(data, str(temp_file.absolute()))
    assert temp_file.read_text() == (
        '{"identifier":"test-external-resources-iam-role","assume_role":{"aws":"null","service":["ec2.amazonaws.com"],"federated":"null"},"inline_policy":"{\\"Version\\":\\"2012-10-17\\",\\"Statement\\":[{\\"Effect\\":\\"Allow\\",\\"Action\\":[\\"ec2:DescribeVpcs\\"],\\"Resource\\":[\\"*\\"]}]}","output_resource_name":"test-external-resources","region":"us-east-1"}'
    )


def test_create_backend_tf_file(provision_data: AppInterfaceProvision) -> None:
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        create_backend_tf_file(provision_data, temp_file.name)
        assert temp_file.read().decode("utf-8") == terraform_fmt(
            """
            terraform {
              backend "s3" {
                bucket = "test-external-resources-state"
                key    = "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"
                region = "us-east-1"
                dynamodb_table = "test-external-resources-lock"
                profile = "external-resources-state"
              }
            }"""
        )


def test_create_backend_tf_file_env_var(
    tmp_path: Path, provision_data: AppInterfaceProvision
) -> None:
    temp_file = tmp_path / "temp.tf"
    create_backend_tf_file(provision_data, str(temp_file.absolute()))
    assert temp_file.read_text() == terraform_fmt(
        """
        terraform {
          backend "s3" {
            bucket = "test-external-resources-state"
            key    = "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"
            region = "us-east-1"
            dynamodb_table = "test-external-resources-lock"
            profile = "external-resources-state"
          }
        }"""
    )
