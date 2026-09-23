import pytest
from pydantic import ValidationError

from external_resources_io.terraform.plan import Action, Change, Plan, ResourceAttribute


def test_resource_attribute_accepts_integer_path_steps() -> None:
    attribute = ResourceAttribute.model_validate({
        "resource": "aws_vpc_endpoint_service.this",
        "attribute": ["private_dns_name_configuration", 0, "name"],
    })

    assert attribute.attribute == ["private_dns_name_configuration", 0, "name"]


def test_change_accepts_optional_fields_and_mixed_replace_path_steps() -> None:
    change = Change.model_validate({
        "actions": ["delete", "create"],
        "replace_paths": [["nested_block", 0, "attribute"]],
        "importing": {"id": "resource-id", "identity": {"key": "value"}},
        "before_identity": {"key": "before"},
        "after_identity": {"key": "after"},
    })

    assert change.after_unknown is None
    assert change.replace_paths == [["nested_block", 0, "attribute"]]
    assert change.importing is not None
    assert change.importing.id == "resource-id"


def test_action_accepts_future_string_values() -> None:
    change = Change.model_validate({"actions": ["future-action"]})

    assert change.actions == ["future-action"]
    assert Action.ActionDelete == "delete"


def test_plan_accepts_go_plan_fields() -> None:
    plan = Plan.model_validate({
        "format_version": "1.2",
        "terraform_version": "1.13.4",
        "variables": {"region": {"value": "us-east-1"}},
        "resource_changes": [
            {
                "address": "aws_instance.example[0]",
                "mode": "managed",
                "type": "aws_instance",
                "name": "example",
                "index": 0,
                "deposed": "deposed-key",
                "action_reason": "replace_because_tainted",
                "change": {"actions": ["no-op"]},
            }
        ],
        "relevant_attributes": [
            {
                "resource": "aws_instance.example[0]",
                "attribute": ["network_interface", 0, "id"],
            }
        ],
        "checks": [
            {
                "address": {
                    "to_display": "aws_instance.example",
                    "kind": "resource",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "example",
                },
                "status": "pass",
                "instances": [
                    {
                        "address": {
                            "to_display": "aws_instance.example[0]",
                            "instance_key": 0,
                        },
                        "status": "pass",
                    }
                ],
            }
        ],
        "action_invocations": [
            {
                "address": "aws_instance.example",
                "type": "example_action",
                "name": "example",
                "lifecycle_action_trigger": {
                    "triggering_resource_address": "aws_instance.example",
                    "action_trigger_event": "after_create",
                    "action_trigger_block_index": 0,
                    "actions_list_index": 0,
                },
            }
        ],
    })

    resource_change = plan.resource_changes[0]
    region = plan.variables["region"]
    assert region is not None
    assert region.value == "us-east-1"
    assert resource_change.mode == "managed"
    assert resource_change.resource_mode == "managed"
    assert resource_change.deposed == "deposed-key"
    assert plan.relevant_attributes[0].attribute == ["network_interface", 0, "id"]
    assert plan.checks[0].instances[0].address.instance_key == 0
    assert plan.action_invocations[0].lifecycle_action_trigger is not None


@pytest.mark.parametrize("format_version", ["0.1", "1.0", "1.2.3"])
def test_plan_accepts_supported_format_versions(format_version: str) -> None:
    assert Plan.model_validate({"format_version": format_version}).format_version == (
        format_version
    )


@pytest.mark.parametrize("format_version", ["invalid", "0.0", "2.0"])
def test_plan_rejects_unsupported_format_versions(format_version: str) -> None:
    with pytest.raises(ValidationError):
        Plan.model_validate({"format_version": format_version})


def test_plan_requires_format_version() -> None:
    with pytest.raises(ValidationError):
        Plan.model_validate({})
