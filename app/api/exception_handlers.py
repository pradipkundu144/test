from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.project import (
    ProjectNotFoundError,
    ProjectPersistenceError,
    ProjectValidationError,
)
from app.logging.logger import get_logger

logger = get_logger(__name__)


async def _not_found(_: Request, exc: Exception) -> JSONResponse:
    err = exc if isinstance(exc, ProjectNotFoundError) else None
    return JSONResponse(
        status_code=404,
        content={
            "error": "project_not_found",
            "message": err.message if err else "not found",
        },
    )


async def _validation(_: Request, exc: Exception) -> JSONResponse:
    err = exc if isinstance(exc, ProjectValidationError) else None
    return JSONResponse(
        status_code=422,
        content={
            "error": "project_validation_error",
            "message": err.message if err else "validation failed",
            "field": err.field if err else None,
        },
    )


async def _persistence(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("persistence failure")
    err = exc if isinstance(exc, ProjectPersistenceError) else None
    return JSONResponse(
        status_code=500,
        content={
            "error": "project_persistence_error",
            "message": err.message if err else "internal server error",
        },
    )


def install(app: FastAPI) -> None:
    app.add_exception_handler(ProjectNotFoundError, _not_found)
    app.add_exception_handler(ProjectValidationError, _validation)
    app.add_exception_handler(ProjectPersistenceError, _persistence)
