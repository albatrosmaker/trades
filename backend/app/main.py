import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import configure_logging, generate_request_id, set_request_id
from app.core.redis_client import init_redis, close_redis

# Configure logging before anything else
configure_logging()
logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown."""
    logger.info("Starting AI Equity Research Platform", version=settings.APP_VERSION)
    try:
        await init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

    try:
        await init_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Failed to initialize Redis", error=str(e))
        raise

    logger.info(
        "Application startup complete",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
    )

    yield

    logger.info("Shutting down application")
    await close_db()
    await close_redis()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production AI-powered equity research platform",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Structured logging and metrics middleware."""
    request_id = request.headers.get("X-Request-ID") or generate_request_id()
    set_request_id(request_id)

    start_time = time.perf_counter()
    endpoint = request.url.path

    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_host=request.client.host if request.client else None,
        request_id=request_id,
    )

    try:
        response: Response = await call_next(request)
        process_time = time.perf_counter() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(process_time)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(process_time * 1000, 2),
            request_id=request_id,
        )
        return response

    except Exception as e:
        process_time = time.perf_counter() - start_time
        logger.error(
            "Request failed with unhandled exception",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=round(process_time * 1000, 2),
            request_id=request_id,
            exc_info=True,
        )
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=500,
        ).inc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancers and orchestrators."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/ready", tags=["System"])
async def readiness_check():
    """Readiness check — verifies all dependencies are available."""
    from app.core.redis_client import get_redis
    from app.core.database import engine
    from sqlalchemy import text

    checks = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "ready" if all_healthy else "degraded", "checks": checks},
    )


@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

from app.api.routes.auth import router as auth_router  # noqa: E402
from app.api.routes.companies import router as companies_router  # noqa: E402
from app.api.routes.reports import router as reports_router  # noqa: E402
from app.api.routes.watchlist import router as watchlist_router  # noqa: E402
from app.api.routes.jobs import router as jobs_router  # noqa: E402
from app.api.routes.valuation import router as valuation_router  # noqa: E402

app.include_router(auth_router, prefix="/auth")
app.include_router(companies_router)
app.include_router(reports_router)
app.include_router(watchlist_router)
app.include_router(jobs_router)
app.include_router(valuation_router)
