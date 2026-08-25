from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class SettingsError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_host: str
    app_port: int
    log_level: str

    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    def __repr__(self) -> str:
        # keep password out of logs and tracebacks
        return (
            "Settings("
            f"app_env={self.app_env!r}, app_host={self.app_host!r}, "
            f"app_port={self.app_port!r}, log_level={self.log_level!r}, "
            f"database_host={self.database_host!r}, database_port={self.database_port!r}, "
            f"database_name={self.database_name!r}, database_user={self.database_user!r}, "
            "database_password=***)"
        )


def load_dotenv(path: str | os.PathLike[str] = ".env") -> None:
    env_path = Path(path)
    if not env_path.is_file():
        return

    with env_path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SettingsError(f"Missing required environment variable: {name}")
    return value


def _optional(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value else default


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise SettingsError(
            f"Environment variable {name} must be an integer, got {raw!r}"
        ) from exc


def load_settings() -> Settings:
    return Settings(
        app_env=_optional("APP_ENV", "local"),
        app_host=_optional("APP_HOST", "0.0.0.0"),
        app_port=_int("APP_PORT", 8000),
        log_level=_optional("LOG_LEVEL", "INFO"),
        database_host=_required("DATABASE_HOST"),
        database_port=_int("DATABASE_PORT", 5432),
        database_name=_required("DATABASE_NAME"),
        database_user=_required("DATABASE_USER"),
        database_password=_required("DATABASE_PASSWORD"),
    )
