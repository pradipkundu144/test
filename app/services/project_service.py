from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.project import Project, ProjectConfiguration
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.exceptions.project import ProjectCreationError, ProjectValidationError
from app.logging.logger import get_logger
from app.repositories.project_repository import AbstractProjectRepository
from app.schemas.project import CreateProjectConfigurationInput, CreateProjectInput


logger = get_logger(__name__)


RepositoryFactory = Callable[[Session], AbstractProjectRepository]

_REQUIRED_CONFIG_FIELDS = ("context", "goals", "scope", "constraints", "coding_standards")


class ProjectService:
    def __init__(
        self,
        session_factory: sessionmaker,
        repository_factory: RepositoryFactory,
    ) -> None:
        self._session_factory = session_factory
        self._repository_factory = repository_factory

    def create_project(self, payload: CreateProjectInput) -> Project:
        logger.info("create_project started name=%r", payload.name)

        project_type, source = _validate(payload)
        project = _build_project(payload, project_type, source)

        try:
            with self._session_factory() as session:
                with session.begin():
                    self._repository_factory(session).add(project)
        except SQLAlchemyError as exc:
            logger.exception("create_project failed name=%r", payload.name)
            raise ProjectCreationError(
                f"could not persist project {payload.name!r}"
            ) from exc

        logger.info("create_project succeeded id=%s", project.id)
        return project


def _validate(payload: CreateProjectInput) -> tuple[ProjectType, ProjectSource]:
    _require_non_empty("name", payload.name)
    _require_non_empty("created_by", payload.created_by)

    try:
        project_type = ProjectType(payload.project_type)
    except ValueError as exc:
        raise ProjectValidationError(
            f"unknown project_type {payload.project_type!r}", field="project_type"
        ) from exc

    try:
        source = ProjectSource(payload.source)
    except ValueError as exc:
        raise ProjectValidationError(
            f"unknown source {payload.source!r}", field="source"
        ) from exc

    _validate_configuration(payload.configuration)
    return project_type, source


def _validate_configuration(config: CreateProjectConfigurationInput) -> None:
    for field in _REQUIRED_CONFIG_FIELDS:
        _require_non_empty(f"configuration.{field}", getattr(config, field))
    if not isinstance(config.tech_stack, dict):
        raise ProjectValidationError(
            "tech_stack must be an object", field="configuration.tech_stack"
        )


def _require_non_empty(field: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProjectValidationError(f"{field} must not be empty", field=field)


def _build_project(
    payload: CreateProjectInput,
    project_type: ProjectType,
    source: ProjectSource,
) -> Project:
    now = datetime.now(UTC)
    project_id = uuid4()

    configuration = ProjectConfiguration(
        id=uuid4(),
        project_id=project_id,
        context=payload.configuration.context,
        goals=payload.configuration.goals,
        scope=payload.configuration.scope,
        constraints=payload.configuration.constraints,
        tech_stack=payload.configuration.tech_stack,
        coding_standards=payload.configuration.coding_standards,
        created_at=now,
        updated_at=now,
    )

    return Project(
        id=project_id,
        name=payload.name.strip(),
        description=payload.description,
        project_type=project_type,
        source=source,
        source_reference_id=payload.source_reference_id,
        status=ProjectStatus.DRAFT,
        created_by=payload.created_by.strip(),
        created_at=now,
        updated_at=now,
        configuration=configuration,
    )
