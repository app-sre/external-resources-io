# ruff: noqa: S603,S607,PLC2701
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import BaseModel

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
    count: int = 0
    enabled: bool = True
    tags: dict[str, Any] | None = None
    variants: list[str] = ["default"]
    mode: Literal["auto", "manual"] = "auto"
    nested: NestedModel
    optional_nested: NestedModel | None = None
    optional: str | None = None
    nested_nested: Sequence[NestedNestedModel]


VARIABLES_TF = """variable "name" {
  type = string
}

variable "str_with_default" {
  type    = string
  default = "default"
}

variable "count" {
  type    = number
  default = 0
}

variable "enabled" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(any)
  default = null
}

variable "variants" {
  type    = list(string)
  default = ["default"]
}

variable "mode" {
  type    = string
  default = "auto"
}

variable "nested" {
  type = object({
    field   = string,
    numeric = number
  })
}

variable "optional_nested" {
  type = object({
    field   = string,
    numeric = number
  })
  default = null
}

variable "optional" {
  type    = string
  default = null
}

variable "nested_nested" {
  type = list(object({
    nested_items = list(object({
      field   = string,
      numeric = number
    }))
  }))
}

"""


# Fixtures
@pytest.fixture
def sample_model() -> type[BaseModel]:
    return SampleModel


def terraform_executable() -> bool:
    try:
        subprocess.run(["terraform", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# Unit Tests
def test_get_terraform_type_basic() -> None:
    assert _get_terraform_type(str) == "string"
    assert _get_terraform_type(int) == "number"
    assert _get_terraform_type(bool) == "bool"
    assert _get_terraform_type(list[str]) == "list(string)"
    assert _get_terraform_type(dict[str, int]) == "map(number)"


def test_get_terraform_type_literal() -> None:
    literal_type = Literal["on", "off"]
    assert _get_terraform_type(literal_type) == "string"


def test_get_terraform_type_model() -> None:
    assert _get_terraform_type(NestedModel) == (
        "object({\n    field = string,\n    numeric = number\n  })"
    )


def test_generate_terraform_variable() -> None:
    output = _generate_terraform_variable(
        name="test_var", tf_type="string", default="value"
    )
    assert output == ('variable "test_var" {\ntype = string\ndefault = "value"\n}\n\n')


@pytest.mark.skipif(not terraform_executable(), reason="Terraform not installed")
def test_generate_terraform_variables_from_model(sample_model: type[BaseModel]) -> None:
    output = subprocess.run(
        ["terraform", "fmt", "-"],
        input=_generate_terraform_variables_from_model(sample_model),
        text=True,
        check=True,
        capture_output=True,
    ).stdout
    assert output == VARIABLES_TF, output


# Integration Test
@pytest.mark.skipif(not terraform_executable(), reason="Terraform not installed")
def test_terraform_fmt_compatibility(
    tmp_path: Path, sample_model: type[BaseModel]
) -> None:
    tf_file = tmp_path / "variables.tf"
    create_variables_tf_file(sample_model, str(tf_file))
    # Run terraform fmt
    subprocess.run(["terraform", "fmt", str(tf_file)], check=True)
