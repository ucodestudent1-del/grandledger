"""FastAPI main application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlmodel import Session

from src.api import api_router
from src.config import settings
from src.core.logging import configure_logging
from src.core.rate_limiter import limiter
from src.core.security import decode_access_token
from src.models import User

logger = logging.getLogger("grandledger")


def _generate_request_id() -> str:
    from uuid import uuid4
    return str(uuid4())

origins: list[str] = []
if settings.DEBUG:
    origins = ["http://localhost:3000", "http://localhost:8000"]
else:
    env_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []
    origins = [o.strip() for o in env_origins if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    if settings.DEBUG and "sqlite" in settings.DATABASE_URL:
        from src.database import init_db

        init_db()
    configure_logging()
    logger.info("Starting GrandLedger API (env=%s)", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down GrandLedger API")


app = FastAPI(
    title="GrandLedger API",
    description="Multi-tenant double-entry bookkeeping SaaS MVP",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": "60"},
    )


@app.middleware("http")
async def tenant_and_auth_middleware(request: Request, call_next: Any) -> Any:
    """Middleware to set tenant context and authenticate requests."""
    request_id = request.headers.get("X-Request-ID", _generate_request_id())
    request.state.request_id = request_id

    if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
        return await call_next(request)

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ", 1)[1]
            payload = decode_access_token(token)
            if payload:
                import src.database as db_module

                with Session(db_module.engine) as session:
                    user = session.get(User, UUID(payload.get("sub", "")))
                    if user and str(user.company_id) == payload.get("company_id"):
                        request.state.user = user
                        request.state.company_id = user.company_id
                        from src.core.middleware import set_tenant_id
                        set_tenant_id(user.company_id)
                    else:
                        request.state.user = None
                        request.state.company_id = None
            else:
                request.state.user = None
                request.state.company_id = None
        except Exception:
            request.state.user = None
            request.state.company_id = None
    else:
        request.state.user = None
        request.state.company_id = None

    try:
        return await call_next(request)
    finally:
        from src.core.middleware import set_tenant_id
        set_tenant_id(None)


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring."""
    from sqlmodel import text

    import src.database as db_module

    checks: dict[str, Any] = {"database": "ok", "redis": "ok"}

    try:
        with Session(db_module.engine) as session:
            session.exec(text("SELECT 1"))  # type: ignore
    except Exception:
        checks["database"] = "error"
        return {
            "status": "unhealthy",
            "version": "1.1.0",
            "environment": settings.ENVIRONMENT,
            "checks": checks,
        }

    try:
        from src.core.rate_limiter import limiter

        if limiter and hasattr(limiter, "_client"):
            limiter._client.ping()
    except Exception:
        checks["redis"] = "degraded"

    return {
        "status": "healthy",
        "version": "1.1.0",
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }


@app.get("/metrics")
def metrics() -> Any:
    """Prometheus metrics endpoint."""
    try:
        from fastapi.responses import Response
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
    except ImportError:
        return JSONResponse(
            status_code=200,
            content={"message": "Prometheus client not installed"},
        )


app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root() -> Any:
    frontend_dist = Path(__file__).resolve().parent.parent / "web" / "out"
    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    if settings.DEBUG:
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
<head><title>GrandLedger API</title></head>
<body>
<h1>GrandLedger API</h1>
<p>API is running. Documentation: <a href="/docs">/docs</a></p>
<p>Frontend dev server: <a href="{settings.FRONTEND_URL}">{settings.FRONTEND_URL}</a></p>
</body>
</html>"""
        )

    return HTMLResponse(
        content="""<!DOCTYPE html>
<html>
<head><title>GrandLedger API</title></head>
<body>
<h1>GrandLedger API</h1>
<p>API is running. Documentation: <a href="/docs">/docs</a></p>
</body>
</html>"""
    )


@app.get("/{path:path}", include_in_schema=False)
def spa_fallback(path: str) -> Any:
    """Serve frontend assets for client-side routes in production."""
    if path.startswith("api/v1/") or path.startswith("docs") or path.startswith("redoc"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")

    frontend_dist = Path(__file__).resolve().parent.parent / "web" / "out"
    file_path = frontend_dist / path

    if file_path.is_file():
        return FileResponse(file_path)

    index_candidate = frontend_dist / path / "index.html"
    if index_candidate.is_file():
        return FileResponse(index_candidate)

    if settings.DEBUG and not (frontend_dist / "index.html").exists():
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/{path}")

    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return RedirectResponse(url=settings.FRONTEND_URL)
