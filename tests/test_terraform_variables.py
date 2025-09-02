# ruff: noqa: ANN401,PLC2701

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from external_resources_io.config import EnvVar
from external_resources_io.terraform.generators import (
    _convert_json_to_hcl,
    _generate_terraform_variable,
    _generate_terraform_variables_from_model,
    _get_terraform_type,
    create_variables_tf_file,
)
from external_resources_io.terraform.run import (
    terraform_available,
    terraform_fmt,
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
    empty_list: list[int] = []
    empty_set: set[int] = set()
    empty_dict: dict[str, int] = {}
    tags: dict[str, Any] | None = None
    variants: list[str] = ["foo", "bar"]
    mode: Literal["auto", "manual"] = "auto"
    nested: NestedModel
    optional_nested: NestedModel | None = None
    optional: str | None = None
    nested_nested: Sequence[NestedNestedModel]
    default_nested: NestedModel = NestedModel(numeric=0)
    none_none: str | bytes = ""
    field_with_description: str | None = Field(description="A string variable")


VARIABLES_TF_DICT = {
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
        "empty_dict": {
            "default": {},
            "type": "map(number)",
        },
        "empty_list": {
            "default": [],
            "type": "list(number)",
        },
        "empty_set": {
            "default": set(),
            "type": "set(number)",
        },
        "tags": {
            "type": "map(any)",
            "default": None,
        },
        "variants": {
            "type": "list(string)",
            "default": ["foo", "bar"],
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
        "none_none": {
            "type": "any",
            "default": "",
        },
        "field_with_description": {
            "type": "string",
            "description": "A string variable",
        },
    }
}

VARIABLES_TF = """
variable "counter" {
  type    = number
  default = 0
}

variable "default_nested" {
  type = object({ field = string, numeric = number })
  default = {
    field   = "default"
    numeric = 0
  }
}

variable "empty_dict" {
  type    = map(number)
  default = {}
}

variable "empty_list" {
  type    = list(number)
  default = []
}

variable "empty_set" {
  type    = set(number)
  default = []
}

variable "enabled" {
  type    = bool
  default = true
}

variable "field_with_description" {
  type        = string
  description = "A string variable"
}

variable "mode" {
  type    = string
  default = "auto"
}

variable "name" {
    type = string
}

variable "nested" {
  type = object({ field = string, numeric = number })
}

variable "nested_nested" {
  type = list(object({ nested_items = list(object({ field = string, numeric = number })) }))
}

variable "none_none" {
  type    = any
  default = ""
}

variable "optional" {
  type    = string
  default = null
}

variable "optional_nested" {
  type    = object({ field = string, numeric = number })
  default = null
}

variable "str_with_default" {
  type    = string
  default = "default"
}

variable "tags" {
  type    = map(any)
  default = null
}

variable "variants" {
  type = list(string)
  default = ["foo", "bar"]
}
""".lstrip("\n")


@pytest.fixture
def sample_model() -> type[BaseModel]:
    return SampleModel


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
    ("python_type", "default", "description", "expected"),
    [
        (str, "value", None, {"default": "value", "type": "string"}),
        (int, None, None, {"default": None, "type": "number"}),
        (bool, True, None, {"default": True, "type": "bool"}),
        (str, PydanticUndefined, None, {"type": "string"}),
        (
            str,
            "value",
            "A string variable",
            {"default": "value", "type": "string", "description": "A string variable"},
        ),
    ],
)
def test_generate_terraform_variable(
    python_type: Any, default: Any, description: str | None, expected: dict
) -> None:
    assert (
        _generate_terraform_variable(
            python_type=python_type, default=default, description=description
        )
        == expected
    )


def test_generate_terraform_variables_from_model(sample_model: type[BaseModel]) -> None:
    output = _generate_terraform_variables_from_model(sample_model)
    assert output == VARIABLES_TF_DICT


def test_convert_json_to_hcl(sample_model: type[BaseModel]) -> None:
    output = terraform_fmt(
        _convert_json_to_hcl(_generate_terraform_variables_from_model(sample_model))
    )
    expected = terraform_fmt(VARIABLES_TF)
    assert output == expected


def test_create_variables_tf_file(
    tmp_path: Path, sample_model: type[BaseModel]
) -> None:
    tf_file = tmp_path / "variables.tf"
    create_variables_tf_file(sample_model, str(tf_file))
    assert tf_file.exists()
    if terraform_available():
        # Format the generated file
        subprocess.run(["terraform", f"-chdir={tmp_path}", "fmt"], check=True)
        # Validate the generated file
        subprocess.run(["terraform", f"-chdir={tmp_path}", "validate"], check=True)


def test_create_variables_tf_file_output_env_var(
    tmp_path: Path,
    sample_model: type[BaseModel],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tf_file = tmp_path / "variables.tf"
    monkeypatch.setenv(EnvVar.VARIABLES_TF_FILE, str(tf_file))
    create_variables_tf_file(sample_model)
    assert tf_file.exists()
