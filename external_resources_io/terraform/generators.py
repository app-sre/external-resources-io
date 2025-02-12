# ruff: noqa: ANN401
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
    model: type[BaseModel],
    variables_file: str | None = None,
) -> None:
    """Generates Terraform variables file."""
    if not variables_file:
        variables_file = os.environ.get("VARIABLES_TF_FILE", "./module/variables.tf")
    Path(variables_file).write_text(
        _generate_terraform_variables_from_model(model),
        encoding="utf-8",
    )


def _generate_terraform_variables_from_model(model: type[BaseModel]) -> str:
    """Generates Terraform variables with proper nested structure and defaults."""
    terraform_variables = ""

    for field_name, field_info in model.model_fields.items():
        tf_type = _get_terraform_type(field_info.annotation)
        default = field_info.default if field_info.default is not None else None
        terraform_variables += _generate_terraform_variable(
            name=field_name, tf_type=tf_type, default=default
        )

    return terraform_variables


def _generate_terraform_variable(name: str, tf_type: str, default: Any = None) -> str:
    """Generates a Terraform variable block."""
    variable_block = f'variable "{name}" {{\n'
    variable_block += f"type = {tf_type}\n"

    if default is not PydanticUndefined:
        # Handle special Terraform values and formatting
        if isinstance(default, str) and not default.startswith(('"', "[", "{")):
            default = f'"{default}"'
        elif isinstance(default, bool):
            default = str(default).lower()
        elif default is None:
            default = "null"
        elif isinstance(default, list):
            default = [f'"{v}"' if isinstance(v, str) else str(v) for v in default]
            default = f"[{', '.join(v for v in default)}]"
        variable_block += f"default = {default}\n"
    variable_block += "}\n\n"
    return variable_block


def _conver_generic_types(origin: Any, args: Any) -> str:
    """Convert generic types to Terraform types."""
    match origin:
        case t if t in {list, Sequence}:
            return f"list({_get_terraform_type(args[0])})" if args else "list(any)"

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


def _conver_basic_types(python_type: Any) -> str:
    """Convert basic python types to Terraform types."""
    match python_type:
        case t if t is str:
            return "string"
        case t if t is int:
            return "number"
        case t if t is bool:
            return "bool"
        case t if issubclass(t, BaseModel):
            return f"object({_generate_terraform_object_type(t)})"
        case _:
            return "any"


def _get_terraform_type(python_type: Any) -> str:
    """Maps Python types to Terraform types using structural pattern matching."""
    origin = get_origin(python_type)
    args = get_args(python_type)

    return (
        _conver_generic_types(origin, args)
        if origin is not None
        else _conver_basic_types(python_type)
    )


def _generate_terraform_object_type(model: type[BaseModel]) -> str:
    """Generates a Terraform object type with nested structures."""
    fields = []
    for field_name, field_info in model.model_fields.items():
        field_type = _get_terraform_type(field_info.annotation)
        fields.append(f"{field_name} = {field_type}")
    return "{\n    " + ",\n    ".join(fields) + "\n  }"
