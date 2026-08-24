from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.enums.project import ProjectSource, ProjectStatus, ProjectType


@dataclass(frozen=True)
class ProjectConfiguration:
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


@dataclass(frozen=True)
class Project:
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
    configuration: ProjectConfiguration
