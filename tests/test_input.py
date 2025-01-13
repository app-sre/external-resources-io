import tempfile
from typing import Any

import pytest
from pydantic import BaseModel

from external_resources_io.input import (
    AppInterfaceProvision,
    TerraformProvisionOptions,
    create_backend_tf_file,
    create_tf_vars_json,
    parse_model,
)


class Data(BaseModel):
    identifier: str
    assume_role: dict[str, str | list[str] | None]
    inline_policy: str
    output_resource_name: str
    region: str


@pytest.fixture
def ai_data() -> dict[str, Any]:
    return {
        "data": {
            "identifier": "test-external-resources-iam-role",
            "assume_role": {
                "aws": "null",
                "service": ["ec2.amazonaws.com"],
                "federated": "null",
            },
            "inline_policy": '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["ec2:DescribeVpcs"],"Resource":["*"]}]}',
            "output_resource_name": "test-external-resources",
            "region": "us-east-1",
        },
        "provision": {
            "provision_provider": "aws",
            "provisioner": "ter-int-dev",
            "provider": "aws-iam-role",
            "identifier": "test-external-resources-iam-role",
            "target_cluster": "app-sre-stage-01",
            "target_namespace": "test-jpiriz",
            "target_secret_name": "test-external-resources",
            "module_provision_data": {
                "tf_state_bucket": "test-external-resources-state",
                "tf_state_region": "us-east-1",
                "tf_state_dynamodb_table": "test-external-resources-lock",
                "tf_state_key": "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state",
            },
        },
    }


@pytest.fixture
def provision_data(ai_data: dict[str, Any]) -> AppInterfaceProvision:
    return parse_model(AppInterfaceProvision, ai_data["provision"])


@pytest.fixture
def data(ai_data: dict[str, Any]) -> Data:
    return parse_model(Data, ai_data["data"])


def test_parse_provision(provision_data: AppInterfaceProvision) -> None:
    assert isinstance(provision_data, AppInterfaceProvision)
    assert isinstance(provision_data.module_provision_data, TerraformProvisionOptions)
    assert provision_data.module_provision_data.tf_state_region == "us-east-1"


def test_tf_vars_json(data: Data) -> None:
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        create_tf_vars_json(data, temp_file.name)
        assert temp_file.read().decode("utf-8") == (
            '{"identifier":"test-external-resources-iam-role","assume_role":{"aws":"null","service":["ec2.amazonaws.com"],"federated":"null"},"inline_policy":"{\\"Version\\":\\"2012-10-17\\",\\"Statement\\":[{\\"Effect\\":\\"Allow\\",\\"Action\\":[\\"ec2:DescribeVpcs\\"],\\"Resource\\":[\\"*\\"]}]}","output_resource_name":"test-external-resources","region":"us-east-1"}'
        )


def test_create_backaned_tf_file(provision_data: AppInterfaceProvision) -> None:
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        create_backend_tf_file(provision_data, temp_file.name)
        assert temp_file.read().decode("utf-8") == (
            '\nterraform {\n  backend "s3" {\n    bucket = "test-external-resources-state"\n    key    = "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"\n    region = "us-east-1"\n    dynamodb_table = "test-external-resources-lock"\n    profile = "external-resources-state"\n  }\n}\n'
        )
