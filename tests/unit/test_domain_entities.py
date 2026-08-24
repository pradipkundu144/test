from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.entities.project import Project, ProjectConfiguration
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType


def _build_configuration(project_id, now):
    return ProjectConfiguration(
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


def _build_project(project_id, config, now):
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


def test_project_and_configuration_hold_expected_values() -> None:
    project_id = uuid4()
    now = datetime.now(UTC)

    config = _build_configuration(project_id, now)
    project = _build_project(project_id, config, now)

    assert project.configuration is config
    assert project.configuration.project_id == project.id
    assert project.status is ProjectStatus.DRAFT
    assert project.configuration.tech_stack == {"backend": ["Python"]}


def test_project_is_frozen() -> None:
    now = datetime.now(UTC)
    project_id = uuid4()
    project = _build_project(project_id, _build_configuration(project_id, now), now)

    with pytest.raises(FrozenInstanceError):
        project.name = "new name"  # type: ignore[misc]


def test_configuration_is_frozen() -> None:
    project_id = uuid4()
    config = _build_configuration(project_id, datetime.now(UTC))

    with pytest.raises(FrozenInstanceError):
        config.goals = "different"  # type: ignore[misc]
