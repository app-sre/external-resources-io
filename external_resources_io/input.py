import base64
import json
import os
from collections.abc import Mapping
from typing import Any, TypeVar

from pydantic import BaseModel


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
    target_secret_name: str | None
    module_provision_data: TerraformProvisionOptions


T = TypeVar("T", bound=BaseModel)


def parse_model(model_class: type[T], data: Mapping[str, Any]) -> T:
    input = model_class.model_validate(data)
    return input


def read_input_from_file(file_path: str = "/inputs/input.json") -> dict[str, Any]:
    with open(file_path, encoding="utf-8") as f:
        return json.loads(f.read())


def read_input_from_env_var(var: str = "INPUT") -> dict[str, Any]:
    b64data = os.environ[var]
    str_input = base64.b64decode(b64data.encode("utf-8")).decode("utf-8")
    return json.loads(str_input)
