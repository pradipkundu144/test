import os

import pytest


_APP_ENV_KEYS = (
    "APP_ENV",
    "APP_HOST",
    "APP_PORT",
    "LOG_LEVEL",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # unit tests must not read the developer's real .env values
    for key in _APP_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    assert all(k not in os.environ for k in _APP_ENV_KEYS)
