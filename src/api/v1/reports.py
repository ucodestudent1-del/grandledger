"""Financial reports endpoints."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from src.models import (
    Account,
    BankAccount,
    BankTransaction,
    Invoice,
    InvoiceStatus,
    JournalEntry,
    JournalEntryStatus,
    JournalLine,
)
from src.schemas import ReportRequest

router = APIRouter(tags=["reports"])


def get_company_id(request: Request) -> UUID:
    from src.core.middleware import get_company_id as _gci

    return _gci(request)


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.post("/reports/profit-loss")
def profit_loss(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    revenue_lines, expense_lines, total_revenue, total_expenses = _get_pnl_data(
        session, company_id, payload.start_date, payload.end_date
    )

    net_income = total_revenue - total_expenses

    return {
        "report": "Profit & Loss",
        "period": {
            "start_date": payload.start_date.isoformat(),
            "end_date": payload.end_date.isoformat(),
        },
        "revenue": [
            {"account": "Revenue", "amount": str(total_revenue)}
        ],
        "expenses": [
            {"account": "Expenses", "amount": str(total_expenses)}
        ],
        "net_income": str(net_income),
    }


@router.post("/reports/balance-sheet")
def balance_sheet(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    assets, liabilities, equity = _get_bs_data(session, company_id, payload.end_date)

    return {
        "report": "Balance Sheet",
        "as_of": payload.end_date.isoformat(),
        "assets": {"total": str(assets)},
        "liabilities": {"total": str(liabilities)},
        "equity": {"total": str(equity)},
    }


@router.post("/reports/trial-balance")
def trial_balance(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    accounts = _get_account_balances(session, company_id, payload.start_date, payload.end_date)
    total_debit = sum(a["debit"] for a in accounts if a["debit"] > 0)
    total_credit = sum(a["credit"] for a in accounts if a["credit"] > 0)

    return {
        "report": "Trial Balance",
        "period": {
            "start_date": payload.start_date.isoformat(),
            "end_date": payload.end_date.isoformat(),
        },
        "accounts": accounts,
        "total_debits": str(total_debit),
        "total_credits": str(total_credit),
    }


@router.post("/reports/general-ledger")
def general_ledger(
    request: Request,
    payload: ReportRequest,
    account_id: UUID | None = None,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    stmt = (
        select(Account, JournalLine, JournalEntry)
        .join(JournalLine, JournalEntry.id == JournalLine.journal_entry_id)
        .join(Account, JournalLine.account_id == Account.id)
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.status == JournalEntryStatus.POSTED)
        .where(JournalEntry.entry_date >= payload.start_date)
        .where(JournalEntry.entry_date <= payload.end_date)
        .order_by(Account.code, JournalEntry.entry_date)
    )
    if account_id:
        stmt = stmt.where(Account.id == account_id)

    results = session.exec(stmt).all()

    ledger: dict[str, list] = {}
    for acct, line, je in results:
        key = str(acct.id)
        if key not in ledger:
            ledger[key] = {
                "account_id": str(acct.id),
                "account_code": acct.code,
                "account_name": acct.name,
                "entries": [],
                "debit_total": Decimal("0"),
                "credit_total": Decimal("0"),
            }
        entry = {
            "date": je.entry_date.isoformat(),
            "description": line.description or je.description,
            "debit": str(line.debit),
            "credit": str(line.credit),
            "reference": je.number,
        }
        ledger[key]["entries"].append(entry)
        ledger[key]["debit_total"] += line.debit
        ledger[key]["credit_total"] += line.credit

    return {
        "report": "General Ledger",
        "period": {
            "start_date": payload.start_date.isoformat(),
            "end_date": payload.end_date.isoformat(),
        },
        "accounts": list(ledger.values()),
    }


@router.post("/reports/ar-aging")
def ar_aging(
    request: Request,
    as_of: date | None = None,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    if as_of is None:
        from datetime import datetime

        as_of = datetime.utcnow().date()

    stmt = select(Invoice).where(
        Invoice.company_id == company_id,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PAID]),
        Invoice.due_date <= as_of,
    )
    invoices = session.exec(stmt).all()

    buckets = {
        "current": Decimal("0"),
        "0-30": Decimal("0"),
        "31-60": Decimal("0"),
        "61-90": Decimal("0"),
        "90+": Decimal("0"),
    }

    total_outstanding = Decimal("0")

    for inv in invoices:
        paid = _get_payments_for_invoice(session, inv)
        outstanding = inv.total - paid

        if outstanding <= 0:
            continue

        total_outstanding += outstanding
        days_overdue = (as_of - inv.due_date).days if inv.due_date else 0

        if days_overdue == 0:
            buckets["current"] += outstanding
        elif days_overdue <= 30:
            buckets["0-30"] += outstanding
        elif days_overdue <= 60:
            buckets["31-60"] += outstanding
        elif days_overdue <= 90:
            buckets["61-90"] += outstanding
        else:
            buckets["90+"] += outstanding

    return {
        "report": "AR Aging",
        "as_of": as_of.isoformat(),
        "total_outstanding": str(total_outstanding),
        "buckets": {k: str(v) for k, v in buckets.items()},
    }


@router.post("/reports/ap-aging")
def ap_aging(
    request: Request,
    as_of: date | None = None,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    if as_of is None:
        from datetime import datetime

        as_of = datetime.utcnow().date()

    from src.models import Bill, BillStatus

    stmt = select(Bill).where(
        Bill.company_id == company_id,
        Bill.status.in_([BillStatus.POSTED]),
        Bill.due_date <= as_of,
    )
    bills = session.exec(stmt).all()

    buckets = {
        "current": Decimal("0"),
        "0-30": Decimal("0"),
        "31-60": Decimal("0"),
        "61-90": Decimal("0"),
        "90+": Decimal("0"),
    }

    total_outstanding = Decimal("0")

    for bill in bills:
        paid = _get_payments_for_bill(session, bill)
        outstanding = bill.total - paid

        if outstanding <= 0:
            continue

        total_outstanding += outstanding
        days_overdue = (as_of - bill.due_date).days if bill.due_date else 0

        if days_overdue == 0:
            buckets["current"] += outstanding
        elif days_overdue <= 30:
            buckets["0-30"] += outstanding
        elif days_overdue <= 60:
            buckets["31-60"] += outstanding
        elif days_overdue <= 90:
            buckets["61-90"] += outstanding
        else:
            buckets["90+"] += outstanding

    return {
        "report": "AP Aging",
        "as_of": as_of.isoformat(),
        "total_outstanding": str(total_outstanding),
        "buckets": {k: str(v) for k, v in buckets.items()},
    }


@router.post("/reports/cash-summary")
def cash_summary(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    bank_accounts = session.exec(
        select(BankAccount).where(BankAccount.company_id == company_id)
    ).all()

    account_summaries = []
    total_balance = Decimal("0")

    for ba in bank_accounts:
        current_balance = ba.starting_balance
        stmt = (
            select(BankTransaction)
            .where(BankTransaction.bank_account_id == ba.id)
        .where(BankTransaction.txn_date >= payload.start_date)
        .where(BankTransaction.txn_date <= payload.end_date)
        )
        txns = session.exec(stmt).all()
        period_change = sum(t.amount for t in txns)
        current_balance += period_change
        total_balance += current_balance
        account_summaries.append(
            {
                "id": str(ba.id),
                "name": ba.name,
                "bank_name": ba.bank_name,
                "account_number": ba.account_number,
                "starting_balance": str(ba.starting_balance),
                "period_change": str(period_change),
                "ending_balance": str(current_balance),
            }
        )

    return {
        "report": "Cash Summary",
        "period": {
            "start_date": payload.start_date.isoformat(),
            "end_date": payload.end_date.isoformat(),
        },
        "accounts": account_summaries,
        "total_balance": str(total_balance),
    }


def _get_pnl_data(
    session: Session, company_id: UUID, start_date: date, end_date: date
) -> tuple[list, list, Decimal, Decimal]:
    stmt = (
        select(Account, JournalLine, JournalEntry)
        .join(JournalLine, JournalEntry.id == JournalLine.journal_entry_id)
        .join(Account, JournalLine.account_id == Account.id)
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.status == JournalEntryStatus.POSTED)
        .where(JournalEntry.entry_date >= start_date)
        .where(JournalEntry.entry_date <= end_date)
    )
    results = session.exec(stmt).all()

    total_revenue = Decimal("0")
    total_expenses = Decimal("0")

    for acct, line, _ in results:
        net = line.debit - line.credit
        if acct.type == "revenue":
            total_revenue += net
        elif acct.type == "expense":
            total_expenses += net

    return [], [], total_revenue, total_expenses


def _get_bs_data(session: Session, company_id: UUID, as_of: date) -> tuple[Decimal, Decimal, Decimal]:
    stmt = (
        select(Account, JournalLine, JournalEntry)
        .join(JournalLine, JournalEntry.id == JournalLine.journal_entry_id)
        .join(Account, JournalLine.account_id == Account.id)
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.status == JournalEntryStatus.POSTED)
        .where(JournalEntry.entry_date <= as_of)
    )
    results = session.exec(stmt).all()

    assets = Decimal("0")
    liabilities = Decimal("0")
    equity = Decimal("0")

    for acct, line, _ in results:
        net = line.debit - line.credit
        if acct.type == "asset":
            assets += net
        elif acct.type == "liability":
            liabilities += net
        elif acct.type == "equity":
            equity += net

    return assets, liabilities, equity


def _get_account_balances(
    session: Session, company_id: UUID, start_date: date, end_date: date
) -> list[dict]:
    stmt = (
        select(Account, JournalLine, JournalEntry)
        .join(JournalLine, JournalEntry.id == JournalLine.journal_entry_id)
        .join(Account, JournalLine.account_id == Account.id)
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.status == JournalEntryStatus.POSTED)
        .where(JournalEntry.entry_date >= start_date)
        .where(JournalEntry.entry_date <= end_date)
        .order_by(Account.code)
    )
    results = session.exec(stmt).all()

    balances: dict[str, dict] = {}
    for acct, line, _ in results:
        key = str(acct.id)
        if key not in balances:
            balances[key] = {
                "account_id": str(acct.id),
                "account_code": acct.code,
                "account_name": acct.name,
                "account_type": acct.type,
                "debit": Decimal("0"),
                "credit": Decimal("0"),
            }
        balances[key]["debit"] += line.debit
        balances[key]["credit"] += line.credit

    result = []
    for b in balances.values():
        b["debit"] = str(b["debit"])
        b["credit"] = str(b["credit"])
        result.append(b)
    return result


def _get_payments_for_invoice(session: Session, invoice: Invoice) -> Decimal:
    if not invoice.allocated_to:
        return Decimal("0")
    total = Decimal("0")
    for alloc in invoice.allocated_to:
        total += Decimal(str(alloc.get("amount", 0)))
    return total


def _get_payments_for_bill(session: Session, bill) -> Decimal:
    if not bill.allocated_to:
        return Decimal("0")
    total = Decimal("0")
    for alloc in bill.allocated_to:
        total += Decimal(str(alloc.get("amount", 0)))
    return total
