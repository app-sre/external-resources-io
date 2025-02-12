import tempfile
from pathlib import Path

from pydantic import BaseModel

from external_resources_io.input import AppInterfaceProvision
from external_resources_io.terraform.generators import (
    create_backend_tf_file,
    create_tf_vars_json,
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


def test_create_backaned_tf_file(provision_data: AppInterfaceProvision) -> None:
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        create_backend_tf_file(provision_data, temp_file.name)
        assert temp_file.read().decode("utf-8") == (
            '\nterraform {\n  backend "s3" {\n    bucket = "test-external-resources-state"\n    key    = "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"\n    region = "us-east-1"\n    dynamodb_table = "test-external-resources-lock"\n    profile = "external-resources-state"\n  }\n}\n'
        )


def test_create_backaned_tf_file_env_var(
    tmp_path: Path, provision_data: AppInterfaceProvision
) -> None:
    temp_file = tmp_path / "temp.tf"
    create_backend_tf_file(provision_data, str(temp_file.absolute()))
    assert temp_file.read_text() == (
        '\nterraform {\n  backend "s3" {\n    bucket = "test-external-resources-state"\n    key    = "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"\n    region = "us-east-1"\n    dynamodb_table = "test-external-resources-lock"\n    profile = "external-resources-state"\n  }\n}\n'
    )
