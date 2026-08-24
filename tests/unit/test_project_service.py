from unittest.mock import MagicMock
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.entities.project import Project
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.exceptions.project import ProjectCreationError, ProjectValidationError
from app.repositories.project_repository import AbstractProjectRepository
from app.schemas.project import CreateProjectConfigurationInput, CreateProjectInput
from app.services.project_service import ProjectService


class InMemoryRepository(AbstractProjectRepository):
    def __init__(self) -> None:
        self.added: list[Project] = []

    def add(self, project: Project) -> None:
        self.added.append(project)

    def get_by_id(self, project_id: UUID) -> Project | None:
        return next((p for p in self.added if p.id == project_id), None)


class RaisingRepository(AbstractProjectRepository):
    def add(self, project: Project) -> None:
        raise IntegrityError("stmt", {}, Exception("simulated db failure"))

    def get_by_id(self, project_id: UUID) -> Project | None:
        return None


def _mock_session_factory():
    factory = MagicMock()
    session = factory.return_value
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    tx = session.begin.return_value
    tx.__enter__.return_value = tx
    tx.__exit__.return_value = False
    return factory, session


def _valid_input(**overrides) -> CreateProjectInput:
    payload = CreateProjectInput(
        name="Customer Analytics",
        project_type="NEW",
        source="PPM",
        created_by="user-123",
        configuration=CreateProjectConfigurationInput(
            context="ctx",
            goals="goals",
            scope="scope",
            constraints="none",
            tech_stack={"backend": ["Python"]},
            coding_standards="PEP 8",
        ),
        description="a description",
        source_reference_id="PPM-42",
    )
    for key, value in overrides.items():
        setattr(payload, key, value)
    return payload


def _service_with(repo: AbstractProjectRepository) -> tuple[ProjectService, MagicMock]:
    factory, session = _mock_session_factory()
    service = ProjectService(factory, lambda _s: repo)
    return service, session


def test_create_project_success_returns_draft_project_with_config() -> None:
    repo = InMemoryRepository()
    service, _ = _service_with(repo)

    result = service.create_project(_valid_input())

    assert isinstance(result, Project)
    assert result.status is ProjectStatus.DRAFT
    assert result.project_type is ProjectType.NEW
    assert result.source is ProjectSource.PPM
    assert result.configuration.project_id == result.id
    assert result.configuration.tech_stack == {"backend": ["Python"]}
    assert len(repo.added) == 1 and repo.added[0] is result


def test_missing_name_raises_validation_error() -> None:
    repo = InMemoryRepository()
    service, _ = _service_with(repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.create_project(_valid_input(name="   "))

    assert excinfo.value.field == "name"
    assert repo.added == []


def test_invalid_project_type_raises_validation_error() -> None:
    repo = InMemoryRepository()
    service, _ = _service_with(repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.create_project(_valid_input(project_type="BAD"))

    assert excinfo.value.field == "project_type"
    assert repo.added == []


def test_invalid_source_raises_validation_error() -> None:
    repo = InMemoryRepository()
    service, _ = _service_with(repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.create_project(_valid_input(source="UNKNOWN"))

    assert excinfo.value.field == "source"


def test_missing_configuration_context_raises_validation_error() -> None:
    repo = InMemoryRepository()
    service, _ = _service_with(repo)
    payload = _valid_input()
    payload.configuration.context = ""

    with pytest.raises(ProjectValidationError) as excinfo:
        service.create_project(payload)

    assert excinfo.value.field == "configuration.context"


def test_tech_stack_wrong_type_raises_validation_error() -> None:
    repo = InMemoryRepository()
    service, _ = _service_with(repo)
    payload = _valid_input()
    payload.configuration.tech_stack = "not-a-dict"  # type: ignore[assignment]

    with pytest.raises(ProjectValidationError) as excinfo:
        service.create_project(payload)

    assert excinfo.value.field == "configuration.tech_stack"


def test_repository_integrity_error_is_wrapped_as_creation_error() -> None:
    service, _ = _service_with(RaisingRepository())

    with pytest.raises(ProjectCreationError) as excinfo:
        service.create_project(_valid_input())

    assert "Customer Analytics" in excinfo.value.message
    assert isinstance(excinfo.value.__cause__, IntegrityError)


def test_transaction_context_exits_with_exception_on_failure() -> None:
    service, session = _service_with(RaisingRepository())

    with pytest.raises(ProjectCreationError):
        service.create_project(_valid_input())

    session.begin.assert_called_once()
    tx = session.begin.return_value
    exit_args = tx.__exit__.call_args[0]
    assert exit_args[0] is IntegrityError
