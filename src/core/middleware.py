"""Middleware: tenant context, audit logging, RBAC."""
from __future__ import annotations

import threading
from contextlib import suppress
from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlmodel import Session, text

from src.core.security import decode_access_token
from src.models import User

_tenant_context: threading.local = threading.local()


def set_tenant_id(company_id: UUID | None) -> None:
    """Store the current tenant (company) ID in thread-local context."""
    _tenant_context.company_id = company_id


def get_tenant_id() -> UUID | None:
    """Get the current tenant (company) ID from thread-local context."""
    return getattr(_tenant_context, "company_id", None)


def get_db() -> Session:
    import src.database as db_module

    session = Session(db_module.engine)
    # Set RLS context for PostgreSQL (no-op on SQLite)
    tenant_id = get_tenant_id()
    if tenant_id:
        with suppress(Exception):
            session.exec(text("SET LOCAL app.company_id = :cid"), {"cid": str(tenant_id)})
    return session


def get_current_user(request: Request) -> User:
    import src.database as db_module

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    company_id = payload.get("company_id")
    if not user_id or not company_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    with Session(db_module.engine) as session:
        user = session.get(User, UUID(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if str(user.company_id) != str(company_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
        request.state.user = user
        request.state.company_id = user.company_id
        return user


def get_company_id(request: Request) -> UUID:
    """Extract the tenant/company ID from the request state."""
    company_id = getattr(request.state, "company_id", None)
    if not company_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return company_id


def require_role(*allowed_roles: str) -> Any:
    """Dependency decorator that enforces role-based access control.

    Usage:
        @router.get("/admin")
        def admin_route(user: User = Depends(require_role("owner"))):
            ...
    """

    def role_checker(request: Request) -> User:
        user: User = request.state.user
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker


def log_audit(
    company_id: UUID,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    before: dict | None = None,
    after: dict | None = None,
    ip_address: str | None = None,
) -> None:
    import src.database as db_module
    from src.models import AuditLog

    with Session(db_module.engine) as session:
        session.add(
            AuditLog(
                company_id=company_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else None,
                before=before,
                after=after,
                ip_address=ip_address,
            )
        )
        session.commit()
