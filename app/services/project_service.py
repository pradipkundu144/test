from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.project import ProjectModel
from app.db.models.project_configuration import ProjectConfigurationModel
from app.domain.entities.project import Project, ProjectConfiguration
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.exceptions.project import (
    ProjectCreationError,
    ProjectNotFoundError,
    ProjectPersistenceError,
    ProjectValidationError,
)
from app.logging.logger import get_logger
from app.repositories.project_repository import AbstractProjectRepository
from app.schemas.project import CreateProjectConfigurationInput, CreateProjectInput


logger = get_logger(__name__)


RepositoryFactory = Callable[[Session], AbstractProjectRepository]

_REQUIRED_CONFIG_FIELDS = ("context", "goals", "scope", "constraints", "coding_standards")

_UPDATABLE_PROJECT_FIELDS: frozenset[str] = frozenset(
    {"name", "description", "project_type", "source", "source_reference_id", "status"}
)
_UPDATABLE_CONFIG_FIELDS: frozenset[str] = frozenset(
    {"context", "goals", "scope", "constraints", "tech_stack", "coding_standards"}
)


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

    def get_project(self, project_id: UUID) -> Project:
        with self._session_factory() as session:
            project = self._repository_factory(session).get_by_id(project_id)
            if project is None:
                raise ProjectNotFoundError(project_id)
            return project

    def update_project(
        self,
        project_id: UUID,
        project_changes: dict[str, Any],
        config_changes: dict[str, Any] | None = None,
    ) -> Project:
        _validate_project_update(project_changes)
        _validate_config_update(config_changes or {})

        try:
            with self._session_factory() as session:
                with session.begin():
                    repo = self._repository_factory(session)
                    model = repo.get_model_by_id(project_id)
                    if model is None:
                        raise ProjectNotFoundError(project_id)
                    _apply_project_changes(model, project_changes)
                    if config_changes:
                        _apply_config_changes(model.configuration, config_changes)
        except ProjectNotFoundError:
            raise
        except SQLAlchemyError as exc:
            logger.exception("update_project failed id=%s", project_id)
            raise ProjectPersistenceError(
                f"could not update project {project_id}"
            ) from exc

        logger.info("update_project succeeded id=%s", project_id)
        return self.get_project(project_id)

    def delete_project(self, project_id: UUID) -> None:
        try:
            with self._session_factory() as session:
                with session.begin():
                    deleted = self._repository_factory(session).delete(project_id)
                    if not deleted:
                        raise ProjectNotFoundError(project_id)
        except ProjectNotFoundError:
            raise
        except SQLAlchemyError as exc:
            logger.exception("delete_project failed id=%s", project_id)
            raise ProjectPersistenceError(
                f"could not delete project {project_id}"
            ) from exc

        logger.info("delete_project succeeded id=%s", project_id)


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


def _validate_project_update(changes: dict[str, Any]) -> None:
    unknown = set(changes) - _UPDATABLE_PROJECT_FIELDS
    if unknown:
        raise ProjectValidationError(
            f"unknown project field(s): {sorted(unknown)}", field="project"
        )
    if "name" in changes:
        _require_non_empty("name", changes["name"])
    if "project_type" in changes:
        _require_enum("project_type", changes["project_type"], ProjectType)
    if "source" in changes:
        _require_enum("source", changes["source"], ProjectSource)
    if "status" in changes:
        _require_enum("status", changes["status"], ProjectStatus)


def _validate_config_update(changes: dict[str, Any]) -> None:
    unknown = set(changes) - _UPDATABLE_CONFIG_FIELDS
    if unknown:
        raise ProjectValidationError(
            f"unknown configuration field(s): {sorted(unknown)}",
            field="configuration",
        )
    for field in _REQUIRED_CONFIG_FIELDS:
        if field in changes:
            _require_non_empty(f"configuration.{field}", changes[field])
    if "tech_stack" in changes and not isinstance(changes["tech_stack"], dict):
        raise ProjectValidationError(
            "tech_stack must be an object", field="configuration.tech_stack"
        )


def _require_non_empty(field: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProjectValidationError(f"{field} must not be empty", field=field)


def _require_enum(field: str, value: object, enum_cls: type) -> None:
    try:
        enum_cls(value)
    except ValueError as exc:
        raise ProjectValidationError(
            f"unknown {field} {value!r}", field=field
        ) from exc


def _apply_project_changes(model: ProjectModel, changes: dict[str, Any]) -> None:
    for field, value in changes.items():
        if field == "name" and isinstance(value, str):
            model.name = value.strip()
        else:
            setattr(model, field, value)


def _apply_config_changes(
    model: ProjectConfigurationModel,
    changes: dict[str, Any],
) -> None:
    for field, value in changes.items():
        setattr(model, field, value)


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
