from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from .api.sentiment import router as sentiment_router
from .config import Settings
from .container import Container, build_container
from .logging import configure_logging
from .schemas import HealthResponse


def create_app(settings: Settings = None, container: Container = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging()
    app_container = container or build_container(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = app_container
        if settings.worker_enabled:
            await app_container.worker.start()
        yield
        await app_container.worker.stop()
        app_container.repository.close()

    app = FastAPI(
        title="Aegis Financial News Sentiment Service",
        version="1.0.0",
        description="Read-only financial news intelligence for the Aegis Orchestrator. This service never executes trades.",
        lifespan=lifespan,
    )
    app.state.container = app_container
    app.include_router(sentiment_router)

    @app.get("/health", response_model=HealthResponse, tags=["operations"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service=settings.service_name)

    @app.get("/ready", response_model=HealthResponse, tags=["operations"])
    async def ready(request: Request):
        checks = {
            "database": "ok" if app_container.repository.ping() else "unavailable",
            "sentiment_engine": "configured" if app_container.engine.available() else "unavailable",
            "news_providers": "configured" if app_container.pipeline.providers else "not_configured",
        }
        ready_status = "ready" if checks["database"] == "ok" and checks["sentiment_engine"] == "configured" else "not_ready"
        response = HealthResponse(status=ready_status, service=settings.service_name, checks=checks)
        if ready_status != "ready":
            return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=response.model_dump(mode="json"))
        return response

    return app


app = create_app()
