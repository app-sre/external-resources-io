import pytest

from external_resources_io.config import Config


def test_config_defaults() -> None:
    config = Config()
    assert config.action == "apply"
    assert config.dry_run
    assert config.log_level == "INFO"


def test_config_readenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTION", "fake")
    monkeypatch.setenv("DRY_RUN", "0")
    config = Config()
    assert config.action == "fake"
    assert not config.dry_run


def test_config_lower_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTION", "DESTROY")
    config = Config()
    assert config.action == "destroy"
