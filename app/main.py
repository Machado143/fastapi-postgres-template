from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.exceptions import AppException
from app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="FastAPI Postgres Template",
    description="Production-ready FastAPI template with PostgreSQL, async SQLAlchemy 2.0, JWT auth.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api/v1")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or {},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Simple health check used by Docker/K8s.

    Returns a static JSON so that external systems know the app is up.
    """
    return {"status": "ok"}
