"""Audit log endpoints."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from src.models import AuditLog
from src.schemas import AuditLogRead

router = APIRouter(tags=["audit"])


def get_company_id(request: Request) -> UUID:
    from src.core.middleware import get_company_id as _gci

    return _gci(request)


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.get("/audit/logs", response_model=list[AuditLogRead])
def list_audit_logs(
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
    entity_type: str | None = None,
    action: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
) -> list[AuditLogRead]:
    stmt = select(AuditLog).where(AuditLog.company_id == company_id)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if start_date:
        stmt = stmt.where(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        stmt = stmt.where(AuditLog.created_at <= datetime.combine(end_date, datetime.max.time()))
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
    logs = session.exec(stmt).all()
    return logs
