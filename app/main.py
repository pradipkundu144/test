from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import exception_handlers
from app.api.v1.router import router as v1_router
from app.config.settings import load_dotenv, load_settings
from app.db.session import create_engine_from_settings, create_session_factory
from app.logging.logger import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    settings = load_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)

    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    logger.info("Synapse API starting (env=%s)", settings.app_env)
    try:
        yield
    finally:
        engine.dispose()
        logger.info("Synapse API shut down")


app = FastAPI(
    title="Synapse",
    version="0.1.0",
    description="AI-powered SDLC platform — Project Intake service.",
    lifespan=lifespan,
)

exception_handlers.install(app)
app.include_router(v1_router)


@app.get("/health", tags=["health"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}
