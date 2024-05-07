from external_resources_io.input import (
    parse_model,
    AppInterfaceProvision,
    TerraformProvisionOptions
)
from pytest import fixture
from typing import Any



@fixture
def data() -> dict[str, Any]:
    return {
  "data": {
    "identifier": "test-external-resources-iam-role",
    "assume_role": {
      "aws": "null",
      "service": [
        "ec2.amazonaws.com"
      ],
      "federated": "null",
    },
    "inline_policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"ec2:DescribeVpcs\"],\"Resource\":[\"*\"]}]}",
    "output_resource_name": "test-external-resources",
    "region": "us-east-1"
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
      "tf_state_key": "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"
    }
  }
}



def test_parse_provision(data: dict) -> None:
    o = parse_model(AppInterfaceProvision, data["provision"])
    assert isinstance(o, AppInterfaceProvision)
    assert isinstance(o.module_provision_data, TerraformProvisionOptions)
    assert o.module_provision_data.tf_state_region == "us-east-1"
