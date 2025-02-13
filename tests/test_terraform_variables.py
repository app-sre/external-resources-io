# ruff: noqa: ANN401,S603,S607,PLC2701

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from external_resources_io.terraform.generators import (
    _generate_default,
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


VARIABLES_TF = {
    "variable": {
        "name": {
            "type": "string",
        },
        "str_with_default": {
            "type": "string",
            "default": '"default"',
        },
        "count": {
            "type": "number",
            "default": "0",
        },
        "enabled": {
            "type": "bool",
            "default": "true",
        },
        "tags": {
            "type": "map(any)",
            "default": "null",
        },
        "variants": {
            "type": "list(string)",
            "default": '["default"]',
        },
        "mode": {
            "type": "string",
            "default": '"auto"',
        },
        "nested": {
            "type": "map({field = string,numeric = number})",
        },
        "optional_nested": {
            "type": "map({field = string,numeric = number})",
            "default": "null",
        },
        "optional": {
            "type": "string",
            "default": "null",
        },
        "nested_nested": {
            "type": "list(map({nested_items = list(map({field = string,numeric = number}))}))"
        },
    }
}


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
        (NestedModel, "map({field = string,numeric = number})"),
    ],
)
def test_get_terraform_type_basic(python_type: Any, expected: str) -> None:
    assert _get_terraform_type(python_type) == expected


@pytest.mark.parametrize(
    ("python_type", "default", "expected"),
    [
        (str, "value", {"default": '"value"', "type": "string"}),
        (int, None, {"default": "null", "type": "number"}),
        (bool, True, {"default": "true", "type": "bool"}),
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


@pytest.mark.parametrize(
    ("default", "expected"),
    [
        ("value", '"value"'),
        (True, "true"),
        (False, "false"),
        (None, "null"),
        ([1, 2, 3], "[1, 2, 3]"),
        (["1", "2", "3"], '["1", "2", "3"]'),
        ([True, False], "[true, false]"),
    ],
)
def test_generate_default(default: Any, expected: str) -> None:
    assert _generate_default(default) == expected


def test_generate_terraform_variables_from_model(sample_model: type[BaseModel]) -> None:
    output = _generate_terraform_variables_from_model(sample_model)
    assert output == VARIABLES_TF


def test_create_variables_tf_file(
    tmp_path: Path, sample_model: type[BaseModel]
) -> None:
    tf_file = tmp_path / "variables.tf.json"
    create_variables_tf_file(sample_model, str(tf_file))
    assert json.loads(tf_file.read_text()) == VARIABLES_TF
