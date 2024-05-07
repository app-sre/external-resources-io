from pydantic import BaseModel
from typing import Optional
import json
import base64
from typing import TypeVar, Type, Any
from collections.abc import Mapping
import os

# EXAMPLE INPUT
# {
#   "data": {
#     "identifier": "test-external-resources-iam-role",
#     "assume_role": {
#       "aws": null,
#       "service": [
#         "ec2.amazonaws.com"
#       ],
#       "federated": null
#     },
#     "inline_policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"ec2:DescribeVpcs\"],\"Resource\":[\"*\"]}]}",
#     "output_resource_name": "test-external-resources",
#     "region": "us-east-1"
#   },
#   "provision": {
#     "provision_provider": "aws",
#     "provisioner": "ter-int-dev",
#     "provider": "aws-iam-role",
#     "identifier": "test-external-resources-iam-role",
#     "target_cluster": "app-sre-stage-01",
#     "target_namespace": "test-jpiriz",
#     "target_secret_name": "test-external-resources",
#     "module_provision_data": {
#       "tf_state_bucket": "test-external-resources-state",
#       "tf_state_region": "us-east-1",
#       "tf_state_dynamodb_table": "test-external-resources-lock",
#       "tf_state_key": "aws/ter-int-dev/aws-iam-role/test-external-resources-iam-role/terraform.state"
#     }
#   }
# }


class TerraformProvisionOptions(BaseModel):
    tf_state_bucket: str
    tf_state_region: str
    tf_state_dynamodb_table: str
    tf_state_key: str


class AppInterfaceProvision(BaseModel):
    provision_provider: str  # aws
    provisioner: str  # ter-int-dev
    provider: str  # aws-iam-role
    identifier: str
    target_cluster: str
    target_namespace: str
    target_secret_name: Optional[str]
    module_provision_data: TerraformProvisionOptions


T = TypeVar("T", bound=BaseModel)

def parse_model(model_class: Type[T], data: Mapping[str, Any]) -> T:
    input = model_class.model_validate(data)
    return input

def read_input_from_file(file_path: str = "/inputs/input.json") -> dict[str, Any]:
    with open(file_path, "r") as f:
        return json.loads(f.read())

def read_input_from_env_var(var: str = "INPUT") -> dict[str, Any]:
    b64data = os.environ[var]
    str_input = base64.b64decode(b64data.encode("utf-8")).decode("utf-8")
    return json.loads(str_input)

def check_container_env() -> None:
    if "INPUT" not in os.environ:
        raise Exception("INPUT env var not present")
