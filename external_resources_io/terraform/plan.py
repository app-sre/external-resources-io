from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, BaseModel, Field, field_validator

# Source types: terraform-json/plan.go, action.go, and checks.go.
# https://github.com/hashicorp/terraform-json/blob/main/plan.go
# https://github.com/hashicorp/terraform-json/blob/main/action.go
# https://github.com/hashicorp/terraform-json/blob/main/checks.go
# Nested state and configuration types: state.go and config.go.
# https://github.com/hashicorp/terraform-json/blob/main/state.go
# https://github.com/hashicorp/terraform-json/blob/main/config.go

PLAN_FORMAT_VERSION_MINIMUM = (0, 1)
PLAN_FORMAT_VERSION_COMPONENT_COUNT = 2
PLAN_FORMAT_VERSION_EXCLUSIVE_MAJOR_MAXIMUM = 2


class Action(StrEnum):
    ActionNoop = "no-op"
    ActionCreate = "create"
    ActionRead = "read"
    ActionUpdate = "update"
    ActionDelete = "delete"
    ActionForget = "forget"

    @classmethod
    def _missing_(cls, value: object) -> Action | None:
        if not isinstance(value, str):
            return None
        unknown_action = str.__new__(cls, value)
        unknown_action._name_ = value
        unknown_action._value_ = value
        return unknown_action


class Importing(BaseModel):
    id: str | None = None
    unknown: bool = False
    identity: Any = None


class Change(BaseModel):
    actions: list[Action] = Field(default_factory=list)
    before: Any = None
    after: Any = None
    after_unknown: Any = None
    before_sensitive: Any = None
    after_sensitive: Any = None
    importing: Importing | None = None
    generated_config: str | None = None
    replace_paths: list[list[str | int]] | None = None
    before_identity: Any = None
    after_identity: Any = None


class ResourceChange(BaseModel):
    address: str | None = None
    previous_address: str | None = None
    module_address: str | None = None
    mode: str | None = Field(
        default=None,
        validation_alias=AliasChoices("mode", "resource_mode"),
    )
    type: str = ""
    name: str = ""
    index: str | int | None = None
    provider_name: str | None = None
    deposed: str | None = None
    change: Change | None = None
    action_reason: str | None = None

    @property
    def resource_mode(self) -> str | None:
        return self.mode


class DeferredResourceChange(BaseModel):
    reason: str | None = None
    resource_change: ResourceChange | None = None


class ResourceAttribute(BaseModel):
    resource: str
    attribute: list[str | int]


class PlanVariable(BaseModel):
    value: Any = None


class LifecycleActionTrigger(BaseModel):
    triggering_resource_address: str | None = None
    action_trigger_event: str | None = None
    action_trigger_block_index: int = 0
    actions_list_index: int = 0


class InvokeActionTrigger(BaseModel):
    pass


class ActionInvocation(BaseModel):
    address: str | None = None
    type: str | None = None
    name: str | None = None
    config_values: Any = None
    config_sensitive: Any = None
    config_unknown: Any = None
    provider_name: str | None = None
    lifecycle_action_trigger: LifecycleActionTrigger | None = None
    invoke_action_trigger: InvokeActionTrigger | None = None


class CheckStaticAddress(BaseModel):
    to_display: str
    kind: str
    module: str | None = None
    mode: str | None = None
    type: str | None = None
    name: str | None = None


class CheckDynamicAddress(BaseModel):
    to_display: str
    module: str | None = None
    instance_key: Any = None


class CheckResultProblem(BaseModel):
    message: str


class CheckResultDynamic(BaseModel):
    address: CheckDynamicAddress
    status: str
    problems: list[CheckResultProblem] = Field(default_factory=list)


class CheckResultStatic(BaseModel):
    address: CheckStaticAddress
    status: str
    instances: list[CheckResultDynamic] = Field(default_factory=list)


class Plan(BaseModel):
    format_version: str
    terraform_version: str | None = None
    variables: dict[str, PlanVariable | None] = Field(default_factory=dict)
    planned_values: dict[str, Any] | None = None
    resource_drift: list[ResourceChange] = Field(default_factory=list)
    resource_changes: list[ResourceChange] = Field(default_factory=list)
    deferred_changes: list[DeferredResourceChange] = Field(default_factory=list)
    complete: bool | None = None
    output_changes: dict[str, Change] = Field(default_factory=dict)
    prior_state: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None
    relevant_attributes: list[ResourceAttribute] = Field(default_factory=list)
    checks: list[CheckResultStatic] = Field(default_factory=list)
    timestamp: str | None = None
    action_invocations: list[ActionInvocation] = Field(default_factory=list)

    @field_validator("format_version")
    @classmethod
    def validate_format_version(cls, value: str) -> str:
        components = value.split(".")
        if len(components) < PLAN_FORMAT_VERSION_COMPONENT_COUNT or not all(
            component.isdecimal() for component in components
        ):
            raise ValueError("invalid Terraform plan format version")

        major, minor = int(components[0]), int(components[1])
        if (major, minor) < PLAN_FORMAT_VERSION_MINIMUM or (
            major >= PLAN_FORMAT_VERSION_EXCLUSIVE_MAJOR_MAXIMUM
        ):
            raise ValueError(f"unsupported Terraform plan format version: {value}")

        return value


class TerraformJsonPlanParser:
    def __init__(self, plan_path: str) -> None:
        self.plan = Plan.model_validate_json(
            Path(plan_path).read_text(encoding="utf-8")
        )
