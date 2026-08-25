from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.domain.entities.project import Project
from app.exceptions.project import (
    ProjectNotFoundError,
    ProjectValidationError,
)
from app.repositories.project_repository import AbstractProjectRepository
from app.services.project_service import ProjectService


class TrackingRepository(AbstractProjectRepository):
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def add(self, project: Project) -> None:
        self.calls.append(("add", (project.id,)))

    def get_by_id(self, project_id: UUID) -> Project | None:
        self.calls.append(("get_by_id", (project_id,)))
        return None

    def get_model_by_id(self, project_id: UUID):
        self.calls.append(("get_model_by_id", (project_id,)))
        return None

    def delete(self, project_id: UUID) -> bool:
        self.calls.append(("delete", (project_id,)))
        return False


def _mock_factory():
    factory = MagicMock()
    session = factory.return_value
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    tx = session.begin.return_value
    tx.__enter__.return_value = tx
    tx.__exit__.return_value = False
    return factory


def test_get_project_raises_not_found_when_missing() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)
    missing = uuid4()

    with pytest.raises(ProjectNotFoundError) as excinfo:
        service.get_project(missing)

    assert excinfo.value.project_id == missing


def test_delete_project_raises_not_found_when_missing() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)
    missing = uuid4()

    with pytest.raises(ProjectNotFoundError):
        service.delete_project(missing)


def test_update_project_rejects_unknown_field() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.update_project(uuid4(), {"unknown_field": "x"})

    assert excinfo.value.field == "project"


def test_update_project_rejects_empty_name() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.update_project(uuid4(), {"name": "   "})

    assert excinfo.value.field == "name"


def test_update_project_rejects_invalid_status() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.update_project(uuid4(), {"status": "COMPLETED"})

    assert excinfo.value.field == "status"


def test_update_project_rejects_unknown_config_field() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.update_project(uuid4(), {}, {"weird_field": "x"})

    assert excinfo.value.field == "configuration"


def test_update_project_rejects_non_dict_tech_stack() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)

    with pytest.raises(ProjectValidationError) as excinfo:
        service.update_project(uuid4(), {}, {"tech_stack": "not a dict"})

    assert excinfo.value.field == "configuration.tech_stack"


def test_update_project_missing_id_raises_not_found() -> None:
    repo = TrackingRepository()
    service = ProjectService(_mock_factory(), lambda _s: repo)
    missing = uuid4()

    with pytest.raises(ProjectNotFoundError):
        service.update_project(missing, {"name": "New Name"})
