import pytest
from pydantic import ValidationError

from external_resources_io.config import Action, Config


def test_config_defaults() -> None:
    config = Config()
    assert config.action == Action.APPLY
    assert config.dry_run
    assert config.log_level == "INFO"


def test_config_readenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLAN_FILE_JSON", "fake")
    monkeypatch.setenv("DRY_RUN", "0")
    config = Config()
    assert config.plan_file_json == "fake"
    assert not config.dry_run


def test_config_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTION", "DESTROY")
    config = Config()
    assert config.action == Action.DESTROY


def test_config_bad_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTION", "fake")
    with pytest.raises(ValidationError):
        Config()
