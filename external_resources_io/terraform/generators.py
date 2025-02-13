# ruff: noqa: ANN401
import json
import os
from collections.abc import Sequence
from pathlib import Path
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from external_resources_io.input import AppInterfaceProvision


def create_tf_vars_json(
    input_data: BaseModel,
    vars_file: str | None = None,
) -> None:
    """Helper method to create teraform vars files. Used in terraform based ERv2 modules."""
    if not vars_file:
        vars_file = os.environ.get("TF_VARS_FILE", "./module/tfvars.json")
    Path(vars_file).write_text(
        input_data.model_dump_json(
            exclude_none=True,
        ),
        encoding="utf-8",
    )


def create_backend_tf_file(
    provision_data: AppInterfaceProvision,
    backend_file: str | None = None,
) -> None:
    """Helper method to create teraform backend configuration. Used in terraform based ERv2 modules."""
    if not backend_file:
        backend_file = os.environ.get("BACKEND_TF_FILE", "./module/backend.tf")
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


def create_variables_tf_file(
    model: type[BaseModel], variables_file: str | None = None
) -> None:
    """Generates Terraform variables json file."""
    if not variables_file:
        variables_file = os.environ.get(
            "VARIABLES_TF_JSON_FILE", "./module/variables.tf.json"
        )
    Path(variables_file).write_text(
        json.dumps(_generate_terraform_variables_from_model(model)),
        encoding="utf-8",
    )


def _generate_terraform_variables_from_model(model: type[BaseModel]) -> dict:
    """Generates Terraform variables json."""
    terraform_json: dict = {"variable": {}}
    terraform_variables = terraform_json["variable"]

    for field_name, field_info in model.model_fields.items():
        default = field_info.default if field_info.default is not None else None
        terraform_variables[field_name] = _generate_terraform_variable(
            python_type=field_info.annotation, default=default
        )

    return terraform_json


def _generate_terraform_variable(python_type: Any, default: Any = None) -> dict:
    """Generates a Terraform variable block."""
    variable_block: dict[str, str | None] = {"type": _get_terraform_type(python_type)}

    if default is not PydanticUndefined:
        variable_block["default"] = (
            default.model_dump()
            if default and isinstance(default, BaseModel)
            else default
        )
    return variable_block


def _convert_generic_types(origin: Any, args: Any) -> str:  # noqa: PLR0911
    """Convert generic types to Terraform types."""
    match origin:
        case t if t in {list, Sequence}:
            return f"list({_get_terraform_type(args[0])})" if args else "list(any)"

        case t if t is set:
            return f"set({_get_terraform_type(args[0])})" if args else "set(any)"

        case t if t is dict:
            return f"map({_get_terraform_type(args[1])})" if args else "map(any)"

        case t if t is Literal:
            return "string"

        case t if t in {UnionType, Union}:
            if type(None) in args:
                return _get_terraform_type(args[0])
            return "any"

        case _:
            return "any"


def _convert_basic_types(python_type: Any) -> str:  # noqa: PLR0911
    """Convert basic python types to Terraform types."""
    match python_type:
        case t if t is str:
            return "string"
        case t if t is int:
            return "number"
        case t if t is bool:
            return "bool"
        case t if t is list:
            return "list(any)"
        case t if t is set:
            return "set(any)"
        case t if t is dict:
            return "map(any)"
        case t if issubclass(t, BaseModel):
            return f"object({_generate_terraform_object_type(t)})"
        case _:
            return "any"


def _get_terraform_type(python_type: Any) -> str:
    """Maps Python types to Terraform types using structural pattern matching."""
    origin = get_origin(python_type)
    args = get_args(python_type)

    return (
        _convert_generic_types(origin, args)
        if origin is not None
        else _convert_basic_types(python_type)
    )


def _generate_terraform_object_type(model: type[BaseModel]) -> str:
    """Generates a Terraform object type with nested structures."""
    fields = []
    for field_name, field_info in model.model_fields.items():
        field_type = _get_terraform_type(field_info.annotation)
        fields.append(f"{field_name} = {field_type}")
    return "{" + ",".join(fields) + "}"
