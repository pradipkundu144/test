from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import load_dotenv, load_settings
from app.db.session import create_engine_from_settings, create_session_factory


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    load_dotenv()
    settings = load_settings()
    engine = create_engine_from_settings(settings)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine: Engine) -> sessionmaker:
    return create_session_factory(engine)
