from pydantic import BaseModel
from typing import Optional
import json
import base64
from typing import TypeVar, Type, Any
from collections.abc import Mapping
import os

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
