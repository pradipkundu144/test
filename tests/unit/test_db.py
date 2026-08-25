from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import Settings
from app.db.base import Base
from app.db.session import create_engine_from_settings, create_session_factory


def _fake_settings() -> Settings:
    return Settings(
        app_env="test",
        app_host="127.0.0.1",
        app_port=8001,
        log_level="INFO",
        database_host="localhost",
        database_port=5432,
        database_name="synapse",
        database_user="synapse",
        database_password="x",
    )


def test_metadata_has_naming_convention() -> None:
    convention = Base.metadata.naming_convention
    assert convention["pk"] == "pk_%(table_name)s"
    assert convention["fk"] == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    assert convention["uq"] == "uq_%(table_name)s_%(column_0_name)s"


def test_create_engine_from_settings_uses_psycopg_url() -> None:
    engine = create_engine_from_settings(_fake_settings())

    assert isinstance(engine, Engine)
    assert str(engine.url).startswith("postgresql+psycopg://")


def test_create_session_factory_returns_sessionmaker() -> None:
    engine = create_engine_from_settings(_fake_settings())
    factory = create_session_factory(engine)

    assert isinstance(factory, sessionmaker)
    assert factory.kw["expire_on_commit"] is False
    assert factory.kw["autoflush"] is False
