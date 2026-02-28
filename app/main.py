from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import router as v1_router
from app.core.exceptions import AppException
from app.core.logging import logger, setup_logging, request_id_ctx_var
from app.db.session import engine


# Prometheus histogram for request latency
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path", "status_code"],
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns a unique request ID to each incoming request."""

    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        request_id_ctx_var.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records request latency for Prometheus."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start
        REQUEST_LATENCY.labels(
            request.method, request.url.path, response.status_code
        ).observe(elapsed)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects common security headers into every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="FastAPI Postgres Template",
    description=(
        "Production-ready FastAPI template with PostgreSQL, "
        "async SQLAlchemy 2.0, JWT auth."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api/v1")


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request, exc: AppException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or {},
    )


@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request, exc: ValueError
) -> JSONResponse:
    """Catches unhandled ValueErrors and returns 422."""
    return JSONResponse(
        status_code=422,
        content={"data": None, "error": str(exc), "meta": None},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check — verifies DB connectivity in addition to app status."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        logger.exception("Health check: database unreachable")
        db_status = "unreachable"

    status = "ok" if db_status == "ok" else "degraded"
    return {"status": status, "database": db_status}


# Register middlewares (order matters: outermost first)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    """Prometheus metrics scrape endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
