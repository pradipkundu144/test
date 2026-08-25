from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_project_service
from app.api.schemas import (
    ProjectCreateBody,
    ProjectResponse,
    ProjectUpdateBody,
)
from app.services.project_service import ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectResponse,
    summary="Create a Synapse project and its initial configuration",
)
def create_project(
    body: ProjectCreateBody,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = service.create_project(body.to_input())
    return ProjectResponse.from_entity(project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Fetch a project by id",
)
def get_project(
    project_id: UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    return ProjectResponse.from_entity(service.get_project(project_id))


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Partially update a project (any subset of fields)",
)
def update_project(
    project_id: UUID,
    body: ProjectUpdateBody,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    updated = service.update_project(
        project_id,
        body.project_changes(),
        body.config_changes(),
    )
    return ProjectResponse.from_entity(updated)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a project (cascades to configuration)",
)
def delete_project(
    project_id: UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> Response:
    service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
