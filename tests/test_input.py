from external_resources_io.input import (
    parse_model,
    AppInterfaceProvision,
    Provision,
    Output,
)

from typing import Any
from collections.abc import Mapping
from pytest import fixture


@fixture
def data() -> dict[str, Any]:
    return {
        "data": {},
        "provision": {
            "provision_provider": "aws",
            "provisioner": "app-int-example-01",
            "provider": "rds",
            "identifier": "app-int-example-01-rds",
            "target_cluster": "appint-ex-01",
            "target_namespace": "external-resources-poc",
            "target_secret_name": "creds",
            "module_provision_data": {
                "tf_state_bucket": "test-external-resources-state",
                "tf_state_region": "us-east-1",
                "tf_state_dynamodb_table": "test-external-resources-lock",
                "tf_state_key": "aws/app-int-example-01/rds/app-int-example-01-rds/terraform.tfstate",
            },
        },
    }


@fixture
def app_interface_provision(data: Mapping[str, Any]) -> AppInterfaceProvision:
    return parse_model(AppInterfaceProvision, data["provision"])


def test_parse_provision(app_interface_provision: AppInterfaceProvision) -> None:
    p = Provision(**app_interface_provision.model_dump())
    assert p.provision_provider == "aws"
