"""Banking endpoints: accounts, CSV import, transactions, matching."""
from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlmodel import Session, select

from src.core.middleware import get_company_id, get_db
from src.core.pagination import get_page_params, paginate_query
from src.models import BankAccount, BankTransaction
from src.schemas import BankAccountCreate, BankAccountRead, BankTransactionRead

router = APIRouter(tags=["bank"])


@router.post("/bank/accounts", response_model=BankAccountRead)
def create_bank_account(
    payload: BankAccountCreate,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> BankAccountRead:
    account = BankAccount(company_id=company_id, **payload.model_dump())
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.get("/bank/accounts", response_model=list[BankAccountRead])
def list_bank_accounts(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> list[BankAccountRead]:
    stmt = select(BankAccount).where(BankAccount.company_id == company_id)
    accounts = session.exec(stmt).all()
    return accounts


@router.get("/bank/accounts/{account_id}", response_model=BankAccountRead)
def get_bank_account(
    account_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> BankAccountRead:
    bank_account = session.get(BankAccount, account_id)
    if not bank_account or bank_account.company_id != company_id:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return bank_account


@router.post("/bank/transactions/import")
def import_transactions(
    request: Request,
    bank_account_id: UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    bank_account = session.get(BankAccount, bank_account_id)
    if not bank_account or bank_account.company_id != company_id:
        raise HTTPException(status_code=404, detail="Bank account not found")

    content = file.file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    imported_count = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            date_str = row.get("date", "")
            description = row.get("description", "")
            amount_str = row.get("amount", "0")
            balance_str = row.get("balance", "")

            entry_date = _parse_date(date_str)
            amount = Decimal(amount_str) if amount_str else Decimal("0")
            balance = Decimal(balance_str) if balance_str else None

            txn = BankTransaction(
                company_id=company_id,
                bank_account_id=bank_account.id,
                 txn_date=entry_date,
                description=description[:500],
                amount=amount,
                balance=balance,
                status="pending",
            )
            session.add(txn)
            session.flush()

            # Check if transaction already exists (dedup by date + amount + description)
            existing = session.exec(
                select(BankTransaction).where(
                    BankTransaction.company_id == company_id,
                    BankTransaction.bank_account_id == bank_account.id,
                    BankTransaction.txn_date == entry_date,
                    BankTransaction.amount == amount,
                    BankTransaction.description == description[:500],
                )
            ).first()
            if existing:
                session.delete(txn)
                errors.append(f"Row {i}: duplicate transaction skipped")
                continue

            imported_count += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    session.commit()
    return {"imported": imported_count, "errors": errors, "bank_account_id": str(bank_account_id)}


@router.get("/bank/transactions", response_model=list[BankTransactionRead])
def list_transactions(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
    bank_account_id: UUID | None = None,
    matched: bool | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[BankTransactionRead]:
    page_val, page_size_val = get_page_params(page, page_size)
    stmt = select(BankTransaction).where(BankTransaction.company_id == company_id)
    if bank_account_id:
        stmt = stmt.where(BankTransaction.bank_account_id == bank_account_id)
    if matched is not None:
        stmt = stmt.where(BankTransaction.matched == matched)
    if status:
        stmt = stmt.where(BankTransaction.status == status)
    items, _, _ = paginate_query(stmt, page_val, page_size_val)
    transactions = session.exec(items).all()
    return transactions


@router.post("/bank/transactions/{txn_id}/match")
def match_transaction(
    txn_id: UUID,
    request: Request,
    journal_entry_id: UUID | None = None,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> BankTransactionRead:
    txn = session.get(BankTransaction, txn_id)
    if not txn or txn.company_id != company_id:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn.matched = True
    txn.status = "cleared"
    if journal_entry_id:
        txn.journal_entry_id = journal_entry_id
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


@router.post("/bank/transactions/{txn_id}/reconcile")
def reconcile_transaction(
    txn_id: UUID,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> BankTransactionRead:
    txn = session.get(BankTransaction, txn_id)
    if not txn or txn.company_id != company_id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not txn.matched:
        raise HTTPException(status_code=400, detail="Transaction must be matched first")

    txn.status = "reconciled"
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


def _parse_date(date_str: str):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return datetime.now(UTC).date()
