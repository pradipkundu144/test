import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.repositories.project_repository import SqlAlchemyProjectRepository
from app.schemas.project import CreateProjectConfigurationInput, CreateProjectInput
from app.services.project_service import ProjectService


@pytest.fixture(autouse=True)
def _reset_tables(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        session.execute(text("TRUNCATE projects CASCADE"))
        session.commit()


def _valid_input(name: str = "Integration Project") -> CreateProjectInput:
    return CreateProjectInput(
        name=name,
        project_type="NEW",
        source="PPM",
        created_by="int-test",
        configuration=CreateProjectConfigurationInput(
            context="integration context",
            goals="integration goals",
            scope="integration scope",
            constraints="none",
            tech_stack={"backend": ["Python"], "db": ["PostgreSQL"]},
            coding_standards="PEP 8",
        ),
        description="integration description",
        source_reference_id="PPM-INT-1",
    )


def test_service_persists_full_aggregate_end_to_end(
    session_factory: sessionmaker,
) -> None:
    service = ProjectService(session_factory, SqlAlchemyProjectRepository)

    project = service.create_project(_valid_input())

    assert project.status is ProjectStatus.DRAFT
    assert project.project_type is ProjectType.NEW
    assert project.source is ProjectSource.PPM

    with session_factory() as session:
        loaded = SqlAlchemyProjectRepository(session).get_by_id(project.id)

    assert loaded is not None
    assert loaded == project


def test_transaction_rollback_when_failure_after_insert(
    session_factory: sessionmaker,
) -> None:
    from app.services.project_service import _build_project, _validate

    payload = _valid_input(name="Poisoned")
    project_type, source = _validate(payload)
    project = _build_project(payload, project_type, source)

    with pytest.raises(RuntimeError, match="simulated"):
        with session_factory() as session:
            with session.begin():
                repo = SqlAlchemyProjectRepository(session)
                repo.add(project)
                session.flush()
                raise RuntimeError("simulated crash after flush")

    with session_factory() as session:
        assert SqlAlchemyProjectRepository(session).get_by_id(project.id) is None
        rowcount = session.execute(
            text("SELECT COUNT(*) FROM project_configurations WHERE project_id = :id"),
            {"id": project.id},
        ).scalar_one()
        assert rowcount == 0


def test_delete_project_cascades_to_configuration(
    session_factory: sessionmaker,
) -> None:
    service = ProjectService(session_factory, SqlAlchemyProjectRepository)
    project = service.create_project(_valid_input(name="Cascade Target"))

    with session_factory() as session:
        session.execute(
            text("DELETE FROM projects WHERE id = :id"),
            {"id": project.id},
        )
        session.commit()

    with session_factory() as session:
        remaining = session.execute(
            text("SELECT COUNT(*) FROM project_configurations WHERE project_id = :id"),
            {"id": project.id},
        ).scalar_one()

    assert remaining == 0
