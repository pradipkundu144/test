from pathlib import Path

import pytest

from app.config.settings import (
    Settings,
    SettingsError,
    load_dotenv,
    load_settings,
)


def _set_valid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_HOST", "db.example.com")
    monkeypatch.setenv("DATABASE_PORT", "5433")
    monkeypatch.setenv("DATABASE_NAME", "synapse_test")
    monkeypatch.setenv("DATABASE_USER", "tester")
    monkeypatch.setenv("DATABASE_PASSWORD", "s3cret")


def test_load_settings_returns_typed_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = load_settings()

    assert isinstance(settings, Settings)
    assert settings.app_env == "test"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 9000
    assert settings.log_level == "DEBUG"
    assert settings.database_host == "db.example.com"
    assert settings.database_port == 5433
    assert settings.database_name == "synapse_test"
    assert settings.database_user == "tester"
    assert settings.database_password == "s3cret"


def test_load_settings_applies_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_valid_env(monkeypatch)

    settings = load_settings()

    assert settings.app_env == "local"
    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 8000
    assert settings.log_level == "INFO"


def test_load_settings_raises_when_required_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_env(monkeypatch)
    monkeypatch.delenv("DATABASE_HOST")

    with pytest.raises(SettingsError, match="DATABASE_HOST"):
        load_settings()


def test_load_settings_raises_on_non_integer_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_env(monkeypatch)
    monkeypatch.setenv("DATABASE_PORT", "not-a-number")

    with pytest.raises(SettingsError, match="DATABASE_PORT"):
        load_settings()


def test_database_url_uses_psycopg_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_valid_env(monkeypatch)

    url = load_settings().database_url

    assert url == "postgresql+psycopg://tester:s3cret@db.example.com:5433/synapse_test"


def test_repr_masks_password(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_valid_env(monkeypatch)

    text = repr(load_settings())

    assert "s3cret" not in text
    assert "database_password=***" in text


def test_load_dotenv_populates_missing_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment line\n"
        "\n"
        'DATABASE_HOST="dotenv-host"\n'
        "DATABASE_PORT=6543\n"
        "DATABASE_NAME=dotenv_db\n"
        "DATABASE_USER=dotenv_user\n"
        "DATABASE_PASSWORD=dotenv_pw\n"
    )

    monkeypatch.setenv("DATABASE_HOST", "explicit-host")

    load_dotenv(env_file)
    settings = load_settings()

    # existing env wins over .env
    assert settings.database_host == "explicit-host"
    # missing keys are filled from .env
    assert settings.database_port == 6543
    assert settings.database_name == "dotenv_db"
    assert settings.database_password == "dotenv_pw"


def test_load_dotenv_missing_file_is_noop(tmp_path: Path) -> None:
    load_dotenv(tmp_path / "does-not-exist")
