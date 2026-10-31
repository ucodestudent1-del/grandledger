"""Accounts (Chart of Accounts) endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.core.middleware import get_company_id, get_db
from src.core.pagination import get_page_params, paginate_query
from src.models import Account
from src.schemas import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(tags=["accounts"])


@router.post("/accounts", response_model=AccountRead)
def create_account(
    payload: AccountCreate,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AccountRead:
    if payload.parent_id:
        parent = session.get(Account, payload.parent_id)
        if not parent or parent.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent account not found in this company",
            )

    existing = session.exec(
        select(Account).where(
            Account.company_id == company_id,
            Account.code == payload.code,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account code already exists in this company",
        )

    account = Account(company_id=company_id, **payload.model_dump(exclude={"company_id", "is_system"}))
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.get("/accounts", response_model=list[AccountRead])
def list_accounts(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
    account_type: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[AccountRead]:

    page_val, page_size_val = get_page_params(page, page_size)
    stmt = select(Account).where(Account.company_id == company_id)
    if account_type:
        stmt = stmt.where(Account.type == account_type)
    items, _, _ = paginate_query(stmt, page_val, page_size_val)
    accounts = session.exec(items).all()
    return accounts


@router.get("/accounts/{account_id}", response_model=AccountRead)
def get_account(
    account_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AccountRead:
    account = session.get(Account, account_id)
    if not account or account.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.patch("/accounts/{account_id}", response_model=AccountRead)
def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> AccountRead:
    account = session.get(Account, account_id)
    if not account or account.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    if account.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System accounts cannot be modified",
        )

    account_data = payload.model_dump(exclude_unset=True, exclude={"company_id", "is_system"})
    for field, value in account_data.items():
        setattr(account, field, value)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account
