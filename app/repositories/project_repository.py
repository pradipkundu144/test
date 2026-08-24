from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.project import ProjectModel
from app.db.models.project_configuration import ProjectConfigurationModel
from app.domain.entities.project import Project, ProjectConfiguration
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType


class AbstractProjectRepository(ABC):
    # persistence contract for the Project aggregate; implementations must not commit
    @abstractmethod
    def add(self, project: Project) -> None: ...

    @abstractmethod
    def get_by_id(self, project_id: UUID) -> Project | None: ...


class SqlAlchemyProjectRepository(AbstractProjectRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> None:
        self._session.add(_project_to_model(project))

    def get_by_id(self, project_id: UUID) -> Project | None:
        stmt = (
            select(ProjectModel)
            .options(selectinload(ProjectModel.configuration))
            .where(ProjectModel.id == project_id)
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        return None if model is None else _model_to_project(model)


def _project_to_model(project: Project) -> ProjectModel:
    return ProjectModel(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type.value,
        source=project.source.value,
        source_reference_id=project.source_reference_id,
        status=project.status.value,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        configuration=_configuration_to_model(project.configuration),
    )


def _configuration_to_model(config: ProjectConfiguration) -> ProjectConfigurationModel:
    return ProjectConfigurationModel(
        id=config.id,
        project_id=config.project_id,
        context=config.context,
        goals=config.goals,
        scope=config.scope,
        constraints=config.constraints,
        tech_stack=config.tech_stack,
        coding_standards=config.coding_standards,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _model_to_project(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        name=model.name,
        description=model.description,
        project_type=ProjectType(model.project_type),
        source=ProjectSource(model.source),
        source_reference_id=model.source_reference_id,
        status=ProjectStatus(model.status),
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
        configuration=_model_to_configuration(model.configuration),
    )


def _model_to_configuration(model: ProjectConfigurationModel) -> ProjectConfiguration:
    return ProjectConfiguration(
        id=model.id,
        project_id=model.project_id,
        context=model.context,
        goals=model.goals,
        scope=model.scope,
        constraints=model.constraints,
        tech_stack=model.tech_stack,
        coding_standards=model.coding_standards,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
