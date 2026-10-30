"""Companies endpoints."""
from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.core.middleware import log_audit, require_role
from src.models import Company, User
from src.schemas import CompanyCreate, CompanyRead

router = APIRouter(tags=["companies"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.post("/companies", response_model=CompanyRead)
def create_company(
    payload: CompanyCreate,
    request: Request,
    session: Session = Depends(get_session),
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
    payload: CompanyCreate,
    request: Request,
    session: Session = Depends(get_session),
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


@router.get("/companies")
def list_companies(
    session: Session = Depends(get_session),
) -> list[CompanyRead]:
    companies = session.exec(select(Company)).all()
    return companies


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: UUID,
    session: Session = Depends(get_session),
) -> CompanyRead:
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
    session: Session = Depends(get_session),
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
    session: Session = Depends(get_session),
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
