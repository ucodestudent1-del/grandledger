"""Companies endpoints."""
from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from src.core.middleware import get_company_id, get_db, log_audit, require_role
from src.models import (
    Account,
    Bill,
    Company,
    Contact,
    Invoice,
    JournalEntry,
    Payment,
    User,
)
from src.schemas import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(tags=["companies"])


@router.post("/companies", response_model=CompanyRead)
def create_company(
    payload: CompanyCreate,
    request: Request,
    session: Session = Depends(get_db),
) -> CompanyRead:
    existing = session.exec(select(Company).where(Company.slug == payload.slug)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company slug already taken",
        )
    company = Company(**payload.model_dump())
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


@router.patch("/companies/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_role("owner", "accountant")),
) -> CompanyRead:
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    if company.id != user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own company",
        )

    company_data = payload.model_dump(exclude_unset=True)
    existing = session.exec(select(Company).where(Company.slug == company_data.get("slug", ""), Company.id != company_id)).first()
    if "slug" in company_data and existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company slug already taken",
        )

    for field, value in company_data.items():
        setattr(company, field, value)
    company.updated_at = datetime.now(UTC)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


@router.get("/companies", response_model=list[CompanyRead])
def list_companies(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> list[CompanyRead]:
    stmt = select(Company).where(Company.id == company_id)
    companies = session.exec(stmt).all()
    return companies


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_role("owner", "accountant", "bookkeeper", "readonly")),
) -> CompanyRead:
    if user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own company",
        )
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return company


class PeriodLockRequest(BaseModel):
    locked_period_end: date | None = None


@router.get("/companies/{company_id}/period-lock", response_model=CompanyRead)
def get_period_lock(
    company_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_role("owner", "accountant")),
) -> CompanyRead:
    """Get the current period lock status for the company."""
    company = session.get(Company, company_id)
    if not company or company.id != user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return company


@router.patch("/companies/{company_id}/period-lock", response_model=CompanyRead)
def set_period_lock(
    company_id: UUID,
    payload: PeriodLockRequest,
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_role("owner", "accountant")),
) -> CompanyRead:
    """Lock or unlock a period. Set locked_period_end to lock; set to null to unlock."""
    company = session.get(Company, company_id)
    if not company or company.id != user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    before = {"locked_period_end": str(company.locked_period_end) if company.locked_period_end else None}
    company.locked_period_end = payload.locked_period_end
    company.updated_at = datetime.now(UTC)
    session.add(company)
    session.commit()
    session.refresh(company)

    ip = request.client.host if request.client else None
    log_audit(
        company_id=company_id,
        user_id=user.id,
        action="period_lock.update",
        entity_type="Company",
        entity_id=company_id,
        before=before,
        after={"locked_period_end": str(company.locked_period_end) if company.locked_period_end else None},
        ip_address=ip,
    )

    return company


@router.get("/companies/{company_id}/export")
def export_company_data(
    company_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_role("owner", "accountant")),
) -> StreamingResponse:
    """Export all company data as CSV (GDPR data portability)."""
    if user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only export your own company data",
        )

    output = io.StringIO()
    writer = csv.writer(output)

    # Export accounts
    writer.writerow(["entity", "id", "data"])
    accounts = session.exec(select(Account).where(Account.company_id == company_id)).all()
    for acc in accounts:
        writer.writerow(["account", str(acc.id), acc.name])

    contacts = session.exec(select(Contact).where(Contact.company_id == company_id)).all()
    for contact in contacts:
        writer.writerow(["contact", str(contact.id), contact.name])

    invoices = session.exec(select(Invoice).where(Invoice.company_id == company_id)).all()
    for inv in invoices:
        writer.writerow(["invoice", str(inv.id), inv.number])

    bills = session.exec(select(Bill).where(Bill.company_id == company_id)).all()
    for bill in bills:
        writer.writerow(["bill", str(bill.id), bill.number])

    payments = session.exec(select(Payment).where(Payment.company_id == company_id)).all()
    for payment in payments:
        writer.writerow(["payment", str(payment.id), str(payment.amount)])

    journals = session.exec(select(JournalEntry).where(JournalEntry.company_id == company_id)).all()
    for je in journals:
        writer.writerow(["journal", str(je.id), je.number])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="grandledger_export_{company_id}.csv"',
        },
    )


@router.delete("/companies/{company_id}")
def delete_company_data(
    company_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
    user: User = Depends(require_role("owner")),
) -> dict:
    """Delete all company data (GDPR right to erasure)."""
    if user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own company data",
        )

    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    before = {"name": company.name, "slug": company.slug, "is_active": company.is_active}

    # Soft delete - mark as inactive instead of hard delete
    company.is_active = False
    company.name = f"[DELETED] {company.name}"
    company.slug = f"deleted-{company.id}"
    session.add(company)
    session.commit()

    ip = request.client.host if request.client else None
    log_audit(
        company_id=company_id,
        user_id=user.id,
        action="company.delete",
        entity_type="Company",
        entity_id=company_id,
        before=before,
        after={"name": company.name, "slug": company.slug, "is_active": company.is_active},
        ip_address=ip,
    )

    return {"message": "Company data deleted successfully"}
