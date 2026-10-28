"""Journal entries endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.models import JournalEntry, User
from src.schemas import JournalEntryCreate, JournalEntryRead
from src.services.posting import (
    JournalLineData,
    post_journal,
    post_journal_entry,
    reverse_journal_entry,
    void_journal_entry,
)

router = APIRouter(tags=["journals"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


def get_company_id(request: Request) -> UUID:
    from src.core.middleware import get_company_id as _gci

    return _gci(request)


@router.post("/journals", response_model=JournalEntryRead)
def create_journal(
    payload: JournalEntryCreate,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> JournalEntryRead:
    user: User = request.state.user
    ip = request.client.host if request.client else None

    lines = [
        JournalLineData(
            account_id=ln.account_id,
            description=ln.description,
            debit=ln.debit,
            credit=ln.credit,
        )
        for ln in payload.lines
    ]

    je = post_journal(
        company_id=company_id,
        lines=lines,
        description=payload.description,
        entry_date=payload.entry_date,
        created_by=user.id,
        source=payload.source,
        session=session,
        ip_address=ip,
    )
    session.refresh(je)
    return _build_read(je)


@router.get("/journals", response_model=list[JournalEntryRead])
def list_journals(
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
    status_filter: str | None = None,
) -> list[JournalEntryRead]:
    stmt = select(JournalEntry).where(JournalEntry.company_id == company_id)
    if status_filter:
        stmt = stmt.where(JournalEntry.status == status_filter)
    entries = session.exec(stmt).all()
    return [_build_read(je) for je in entries]


@router.get("/journals/{je_id}", response_model=JournalEntryRead)
def get_journal(
    je_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> JournalEntryRead:
    je = session.get(JournalEntry, je_id)
    if not je or je.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found",
        )
    return _build_read(je)


@router.post("/journals/{je_id}/post", response_model=JournalEntryRead)
def post_journal_endpoint(
    je_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> JournalEntryRead:
    user: User = request.state.user
    ip = request.client.host if request.client else None
    je = post_journal_entry(je_id, posted_by=user.id, ip_address=ip)
    session.refresh(je)
    return _build_read(je)


@router.post("/journals/{je_id}/void", response_model=JournalEntryRead)
def void_journal(
    je_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> JournalEntryRead:
    user: User = request.state.user
    ip = request.client.host if request.client else None
    je = void_journal_entry(je_id, voided_by=user.id, ip_address=ip)
    session.refresh(je)
    return _build_read(je)


@router.post("/journals/{je_id}/reverse", response_model=JournalEntryRead)
def reverse_journal(
    je_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> JournalEntryRead:
    user: User = request.state.user
    ip = request.client.host if request.client else None
    je = reverse_journal_entry(
        je_id,
        reversed_by=user.id,
        entry_date=datetime.utcnow().date(),
        ip_address=ip,
    )
    session.refresh(je)
    return _build_read(je)


def _build_read(je: JournalEntry) -> JournalEntryRead:
    from src.schemas import JournalLineRead

    return JournalEntryRead(
        id=je.id,
        company_id=je.company_id,
        number=je.number,
        entry_date=je.entry_date,
        description=je.description,
        status=je.status,
        posted_at=je.posted_at,
        posted_by=je.posted_by,
        source=je.source,
        created_by=je.created_by,
        lines=[JournalLineRead.model_validate(ln) for ln in je.lines],
        created_at=je.created_at,
        updated_at=je.updated_at,
    )
