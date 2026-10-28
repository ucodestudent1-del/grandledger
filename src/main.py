"""FastAPI main application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from src.api import api_router
from src.config import settings
from src.core.security import decode_access_token
from src.models import User

origins: list[str] = []
if settings.DEBUG:
    origins = ["http://localhost:3000", "http://localhost:8000"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    # Create tables on startup (SQLite dev convenience)
    if "sqlite" in settings.DATABASE_URL:
        from src.database import init_db

        init_db()
    yield


app = FastAPI(
    title="GrandLedger API",
    description="Multi-tenant double-entry bookkeeping SaaS MVP",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root() -> Any:
    return RedirectResponse(url="/docs")
