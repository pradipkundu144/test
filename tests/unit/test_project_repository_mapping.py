from datetime import UTC, datetime
from uuid import uuid4

from app.domain.entities.project import Project, ProjectConfiguration
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.repositories.project_repository import (
    _model_to_project,
    _project_to_model,
)


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


def test_project_to_model_maps_scalar_fields() -> None:
    project = _make_project()

    model = _project_to_model(project)

    assert model.id == project.id
    assert model.name == project.name
    assert model.description == project.description
    assert model.project_type == "NEW"
    assert model.source == "PPM"
    assert model.status == "DRAFT"
    assert model.source_reference_id == project.source_reference_id
    assert model.created_by == project.created_by


def test_project_to_model_attaches_configuration() -> None:
    project = _make_project()

    model = _project_to_model(project)

    assert model.configuration is not None
    assert model.configuration.id == project.configuration.id
    assert model.configuration.project_id == project.id
    assert model.configuration.tech_stack == {"backend": ["Python"]}
    assert model.configuration.context == "ctx"


def test_round_trip_entity_model_entity_is_equal() -> None:
    project = _make_project()

    round_tripped = _model_to_project(_project_to_model(project))

    assert round_tripped == project
    assert round_tripped.configuration == project.configuration


def test_model_to_project_coerces_strings_back_to_enums() -> None:
    project = _make_project()

    round_tripped = _model_to_project(_project_to_model(project))

    assert round_tripped.project_type is ProjectType.NEW
    assert round_tripped.source is ProjectSource.PPM
    assert round_tripped.status is ProjectStatus.DRAFT
