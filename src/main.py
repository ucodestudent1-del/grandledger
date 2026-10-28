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
from src.core.rate_limiter import limiter
from src.core.security import decode_access_token
from src.models import User

logger = logging.getLogger("grandledger")

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
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": "60"},
    )


@app.middleware("http")
async def tenant_and_auth_middleware(request: Request, call_next: Any) -> Any:
    """Middleware to set tenant context and authenticate requests."""
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

    return await call_next(request)


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": "1.1.0",
        "environment": settings.ENVIRONMENT,
    }


app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root() -> Any:
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

    # Production: serve the statically exported frontend index.html
    frontend_dist = Path(__file__).resolve().parent.parent / "web" / "out"
    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

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
    if settings.DEBUG:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/{path}")

    frontend_dist = Path(__file__).resolve().parent.parent / "web" / "out"
    file_path = frontend_dist / path

    # Serve the file if it exists (static assets, _next/*, etc.)
    if file_path.is_file():
        return FileResponse(file_path)

    # With trailingSlash, routes are dirs: try /login/index.html
    index_candidate = frontend_dist / path / "index.html"
    if index_candidate.is_file():
        return FileResponse(index_candidate)

    # For client-side routes, serve the root index.html (SPA fallback)
    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return RedirectResponse(url=settings.FRONTEND_URL)
