from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.domain.entities.project import Project, ProjectConfiguration
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.repositories.project_repository import SqlAlchemyProjectRepository


@pytest.fixture(autouse=True)
def _reset_tables(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        session.execute(text("TRUNCATE projects CASCADE"))
        session.commit()


def _make_project() -> Project:
    now = datetime.now(UTC)
    project_id = uuid4()
    config = ProjectConfiguration(
        id=uuid4(),
        project_id=project_id,
        context="ctx",
        goals="goals",
        scope="scope",
        constraints="none",
        tech_stack={"backend": ["Python"]},
        coding_standards="PEP 8",
        created_at=now,
        updated_at=now,
    )
    return Project(
        id=project_id,
        name="Customer Analytics",
        description="desc",
        project_type=ProjectType.NEW,
        source=ProjectSource.PPM,
        source_reference_id="PPM-1",
        status=ProjectStatus.DRAFT,
        created_by="user-123",
        created_at=now,
        updated_at=now,
        configuration=config,
    )


def test_add_then_get_by_id_returns_full_aggregate(
    session_factory: sessionmaker,
) -> None:
    project = _make_project()

    with session_factory() as session:
        SqlAlchemyProjectRepository(session).add(project)
        session.commit()

    with session_factory() as session:
        loaded = SqlAlchemyProjectRepository(session).get_by_id(project.id)

    assert loaded is not None
    assert loaded.id == project.id
    assert loaded.name == project.name
    assert loaded.project_type is ProjectType.NEW
    assert loaded.source is ProjectSource.PPM
    assert loaded.status is ProjectStatus.DRAFT
    assert loaded.configuration.project_id == project.id
    assert loaded.configuration.tech_stack == {"backend": ["Python"]}


def test_get_by_id_returns_none_for_unknown(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        result = SqlAlchemyProjectRepository(session).get_by_id(uuid4())

    assert result is None


def test_add_without_commit_does_not_persist(session_factory: sessionmaker) -> None:
    project = _make_project()

    with session_factory() as session:
        SqlAlchemyProjectRepository(session).add(project)
        # session closes without commit; changes are discarded

    with session_factory() as session:
        assert SqlAlchemyProjectRepository(session).get_by_id(project.id) is None


def test_second_configuration_for_same_project_violates_unique(
    session_factory: sessionmaker,
) -> None:
    from sqlalchemy.exc import IntegrityError

    project = _make_project()

    with session_factory() as session:
        SqlAlchemyProjectRepository(session).add(project)
        session.commit()

    now = datetime.now(UTC)
    duplicate = ProjectConfiguration(
        id=uuid4(),
        project_id=project.id,
        context="c",
        goals="g",
        scope="s",
        constraints="c",
        tech_stack={},
        coding_standards="s",
        created_at=now,
        updated_at=now,
    )

    from app.repositories.project_repository import _configuration_to_model

    with session_factory() as session:
        session.add(_configuration_to_model(duplicate))
        with pytest.raises(IntegrityError):
            session.commit()
