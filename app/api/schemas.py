from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.project import Project
from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType
from app.schemas.project import CreateProjectConfigurationInput, CreateProjectInput


class ProjectConfigurationCreateBody(BaseModel):
    context: str = Field(min_length=1)
    goals: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    constraints: str = Field(min_length=1)
    tech_stack: dict[str, Any]
    coding_standards: str = Field(min_length=1)


class ProjectCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    project_type: ProjectType
    source: ProjectSource
    created_by: str = Field(min_length=1, max_length=255)
    configuration: ProjectConfigurationCreateBody
    description: str | None = None
    source_reference_id: str | None = Field(default=None, max_length=255)

    def to_input(self) -> CreateProjectInput:
        return CreateProjectInput(
            name=self.name,
            project_type=self.project_type.value,
            source=self.source.value,
            created_by=self.created_by,
            configuration=CreateProjectConfigurationInput(
                context=self.configuration.context,
                goals=self.configuration.goals,
                scope=self.configuration.scope,
                constraints=self.configuration.constraints,
                tech_stack=self.configuration.tech_stack,
                coding_standards=self.configuration.coding_standards,
            ),
            description=self.description,
            source_reference_id=self.source_reference_id,
        )


class ProjectConfigurationUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: str | None = Field(default=None, min_length=1)
    goals: str | None = Field(default=None, min_length=1)
    scope: str | None = Field(default=None, min_length=1)
    constraints: str | None = Field(default=None, min_length=1)
    tech_stack: dict[str, Any] | None = None
    coding_standards: str | None = Field(default=None, min_length=1)


class ProjectUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    project_type: ProjectType | None = None
    source: ProjectSource | None = None
    source_reference_id: str | None = Field(default=None, max_length=255)
    status: ProjectStatus | None = None
    configuration: ProjectConfigurationUpdateBody | None = None

    def project_changes(self) -> dict[str, Any]:
        # only include fields the client explicitly set, so PATCH stays partial
        data = self.model_dump(exclude_unset=True, exclude={"configuration"})
        for field in ("project_type", "source", "status"):
            if field in data and data[field] is not None:
                data[field] = data[field].value if hasattr(data[field], "value") else data[field]
        return data

    def config_changes(self) -> dict[str, Any]:
        if self.configuration is None:
            return {}
        return self.configuration.model_dump(exclude_unset=True)


class ProjectConfigurationResponse(BaseModel):
    id: UUID
    project_id: UUID
    context: str
    goals: str
    scope: str
    constraints: str
    tech_stack: dict[str, Any]
    coding_standards: str
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    project_type: ProjectType
    source: ProjectSource
    source_reference_id: str | None
    status: ProjectStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    configuration: ProjectConfigurationResponse

    @classmethod
    def from_entity(cls, project: Project) -> ProjectResponse:
        c = project.configuration
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            project_type=project.project_type,
            source=project.source,
            source_reference_id=project.source_reference_id,
            status=project.status,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at,
            configuration=ProjectConfigurationResponse(
                id=c.id,
                project_id=c.project_id,
                context=c.context,
                goals=c.goals,
                scope=c.scope,
                constraints=c.constraints,
                tech_stack=c.tech_stack,
                coding_standards=c.coding_standards,
                created_at=c.created_at,
                updated_at=c.updated_at,
            ),
        )


class ErrorResponse(BaseModel):
    error: str
    message: str
    field: str | None = None
