from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import sessionmaker

from app.repositories.project_repository import SqlAlchemyProjectRepository
from app.services.project_service import ProjectService


def get_session_factory(request: Request) -> sessionmaker:
    # engine + factory live on app.state, created once in the lifespan
    return request.app.state.session_factory


def get_project_service(
    session_factory: Annotated[sessionmaker, Depends(get_session_factory)],
) -> ProjectService:
    return ProjectService(session_factory, SqlAlchemyProjectRepository)
