from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import Settings


def create_engine_from_settings(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
