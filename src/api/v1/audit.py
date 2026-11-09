"""Audit log endpoints."""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from src.core.middleware import get_company_id, get_db
from src.core.pagination import get_page_params, paginate_query
from src.models import AuditLog
from src.schemas import AuditLogRead

router = APIRouter(tags=["audit"])


@router.get("/audit/logs", response_model=list[AuditLogRead])
def list_audit_logs(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
    entity_type: str | None = None,
    action: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int | None = None,
    page_size: int | None = None,
    limit: int = 100,
) -> list[AuditLogRead]:
    page_val, page_size_val = get_page_params(page, page_size)
    stmt = select(AuditLog).where(AuditLog.company_id == company_id)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if start_date:
        stmt = stmt.where(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        stmt = stmt.where(AuditLog.created_at <= datetime.combine(end_date, datetime.max.time()))
    stmt = stmt.order_by(AuditLog.created_at.desc())
    items, _, _ = paginate_query(stmt, page_val, page_size_val)
    logs = session.exec(items).all()
    return logs


@router.get("/audit/logs/export")
def export_audit_logs(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
    entity_type: str | None = None,
    action: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> StreamingResponse:
    """Export audit logs as CSV."""
    stmt = select(AuditLog).where(AuditLog.company_id == company_id)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if start_date:
        stmt = stmt.where(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        stmt = stmt.where(AuditLog.created_at <= datetime.combine(end_date, datetime.max.time()))
    stmt = stmt.order_by(AuditLog.created_at.desc())
    logs = session.exec(stmt).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "action", "entity_type", "entity_id", "user_id", "ip_address", "before", "after"])
    for log in logs:
        writer.writerow([
            str(log.id),
            log.created_at.isoformat(),
            log.action,
            log.entity_type,
            str(log.entity_id) if log.entity_id else "",
            str(log.user_id) if log.user_id else "",
            log.ip_address or "",
            log.before or "",
            log.after or "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="grandledger_audit_{datetime.utcnow().strftime("%Y%m%d")}.csv"',
        },
    )
