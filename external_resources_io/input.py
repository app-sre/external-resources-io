import base64
import json
import os
from collections.abc import Mapping
from pathlib import Path
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
    return model_class.model_validate(data)


def read_input_from_file(
    file_path: str = os.environ.get("ER_INPUT_FILE", "/inputs/input.json"),
) -> dict[str, Any]:
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def read_input_from_env_var(var: str = "INPUT") -> dict[str, Any]:
    b64data = os.environ[var]
    str_input = base64.b64decode(b64data.encode("utf-8")).decode("utf-8")
    return json.loads(str_input)


def get_ai_provision_data() -> AppInterfaceProvision:
    """Get the AppInterfaceProvision from the input data file."""
    ai_input = read_input_from_file()
    return parse_model(AppInterfaceProvision, ai_input["provision"])


def create_tf_vars_json(
    input_data: T,
    vars_file: str = os.environ.get("TF_VARS_FILE", "./module/tfvars.json"),
) -> None:
    """Helper method to create teraform vars files. Used in terraform based ERv2 modules."""
    Path(vars_file).write_text(
        input_data.model_dump_json(
            exclude_none=True,
        ),
        encoding="utf-8",
    )


def create_backend_tf_file(
    provision_data: AppInterfaceProvision,
    backend_file: str = os.environ.get("BACKEND_TF_FILE", "./module/backend.tf"),
) -> None:
    """Helper method to create teraform backend configuration. Used in terraform based ERv2 modules."""
    Path(backend_file).write_text(
        f"""
terraform {{
  backend "s3" {{
    bucket = "{provision_data.module_provision_data.tf_state_bucket}"
    key    = "{provision_data.module_provision_data.tf_state_key}"
    region = "{provision_data.module_provision_data.tf_state_region}"
    dynamodb_table = "{provision_data.module_provision_data.tf_state_dynamodb_table}"
    profile = "external-resources-state"
  }}
}}
""",
        encoding="utf-8",
    )
