"""Companies endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.models import Company
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


@router.get("/companies", response_model=list[CompanyRead])
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
