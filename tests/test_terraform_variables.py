# ruff: noqa: ANN401,S603,S607,PLC2701

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from external_resources_io.terraform.generators import (
    _generate_terraform_variable,
    _generate_terraform_variables_from_model,
    _get_terraform_type,
    create_variables_tf_file,
)


# Test Models
class NestedModel(BaseModel):
    """Test nested model"""

    field: str = "default"
    numeric: int


class NestedNestedModel(BaseModel):
    """Test nested nested model"""

    nested_items: list[NestedModel]


class SampleModel(BaseModel):
    """Test model for generation"""

    name: str
    str_with_default: str = "default"
    counter: int = 0
    enabled: bool = True
    tags: dict[str, Any] | None = None
    variants: list[str] = ["default"]
    mode: Literal["auto", "manual"] = "auto"
    nested: NestedModel
    optional_nested: NestedModel | None = None
    optional: str | None = None
    nested_nested: Sequence[NestedNestedModel]
    default_nested: NestedModel = NestedModel(numeric=0)


VARIABLES_TF = {
    "variable": {
        "name": {
            "type": "string",
        },
        "str_with_default": {
            "type": "string",
            "default": "default",
        },
        "counter": {
            "type": "number",
            "default": 0,
        },
        "enabled": {
            "type": "bool",
            "default": True,
        },
        "tags": {
            "type": "map(any)",
            "default": None,
        },
        "variants": {
            "type": "list(string)",
            "default": ["default"],
        },
        "mode": {
            "type": "string",
            "default": "auto",
        },
        "nested": {
            "type": "object({field = string,numeric = number})",
        },
        "optional_nested": {
            "type": "object({field = string,numeric = number})",
            "default": None,
        },
        "optional": {
            "type": "string",
            "default": None,
        },
        "nested_nested": {
            "type": "list(object({nested_items = list(object({field = string,numeric = number}))}))"
        },
        "default_nested": {
            "default": {
                "field": "default",
                "numeric": 0,
            },
            "type": "object({field = string,numeric = number})",
        },
    }
}


@pytest.fixture
def sample_model() -> type[BaseModel]:
    return SampleModel


def terraform_executable() -> bool:
    try:
        subprocess.run(["terraform", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@pytest.mark.parametrize(
    ("python_type", "expected"),
    [
        (str, "string"),
        (int, "number"),
        (bool, "bool"),
        (list[str], "list(string)"),
        (list, "list(any)"),
        (set[str], "set(string)"),
        (set, "set(any)"),
        (dict[str, int], "map(number)"),
        (dict, "map(any)"),
        (Literal["on", "off"], "string"),
        (NestedModel, "object({field = string,numeric = number})"),
    ],
)
def test_get_terraform_type_basic(python_type: Any, expected: str) -> None:
    assert _get_terraform_type(python_type) == expected


@pytest.mark.parametrize(
    ("python_type", "default", "expected"),
    [
        (str, "value", {"default": "value", "type": "string"}),
        (int, None, {"default": None, "type": "number"}),
        (bool, True, {"default": True, "type": "bool"}),
        (str, PydanticUndefined, {"type": "string"}),
    ],
)
def test_generate_terraform_variable(
    python_type: Any, default: Any, expected: dict
) -> None:
    assert (
        _generate_terraform_variable(python_type=python_type, default=default)
        == expected
    )


def test_generate_terraform_variables_from_model(sample_model: type[BaseModel]) -> None:
    output = _generate_terraform_variables_from_model(sample_model)
    assert output == VARIABLES_TF


@pytest.mark.skipif(not terraform_executable(), reason="Terraform not installed")
def test_create_variables_tf_file(
    tmp_path: Path, sample_model: type[BaseModel]
) -> None:
    tf_file = tmp_path / "variables.tf.json"
    create_variables_tf_file(sample_model, str(tf_file))
    # Validate the generated file
    subprocess.run(["terraform", f"-chdir={tmp_path}", "init"], check=True)
