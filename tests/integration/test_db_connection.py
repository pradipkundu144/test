from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


def test_session_executes_select_one(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


def test_session_reports_postgres_server_version(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        version = session.execute(text("SHOW server_version")).scalar_one()

    assert version.startswith("16.")
