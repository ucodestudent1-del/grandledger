"""Financial reports endpoints."""
from __future__ import annotations

from datetime import UTC, date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from src.core.middleware import get_company_id, get_db
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


@router.post("/reports/profit-loss")
def profit_loss(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_db),
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
        "revenue": revenue_lines,
        "expenses": expense_lines,
        "net_income": str(net_income),
    }


@router.post("/reports/balance-sheet")
def balance_sheet(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    assets, liabilities, equity, asset_lines, liability_lines, equity_lines = _get_bs_data(
        session, company_id, payload.end_date
    )

    return {
        "report": "Balance Sheet",
        "as_of": payload.end_date.isoformat(),
        "assets": {"total": str(assets), "items": asset_lines},
        "liabilities": {"total": str(liabilities), "items": liability_lines},
        "equity": {"total": str(equity), "items": equity_lines},
    }


@router.post("/reports/trial-balance")
def trial_balance(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_db),
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
    session: Session = Depends(get_db),
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
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    if as_of is None:
        from datetime import datetime

        as_of = datetime.now(UTC).date()

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
    contacts: dict[str, dict] = {}

    for inv in invoices:
        paid = _get_payments_for_invoice(session, inv)
        outstanding = inv.total - paid

        if outstanding <= 0:
            continue

        total_outstanding += outstanding
        days_overdue = (as_of - inv.due_date).days if inv.due_date else 0

        if days_overdue == 0:
            bucket_key = "current"
        elif days_overdue <= 30:
            bucket_key = "0-30"
        elif days_overdue <= 60:
            bucket_key = "31-60"
        elif days_overdue <= 90:
            bucket_key = "61-90"
        else:
            bucket_key = "90+"

        buckets[bucket_key] += outstanding

        contact_key = str(inv.contact_id)
        if contact_key not in contacts:
            contact_name = _get_contact_name(session, inv.contact_id)
            contacts[contact_key] = {
                "contact_name": contact_name,
                "total_due": Decimal("0"),
                "buckets": {
                    "current": Decimal("0"),
                    "0-30": Decimal("0"),
                    "31-60": Decimal("0"),
                    "61-90": Decimal("0"),
                    "90+": Decimal("0"),
                },
            }
        contacts[contact_key]["total_due"] += outstanding
        contacts[contact_key]["buckets"][bucket_key] += outstanding

    contact_list = []
    for c in contacts.values():
        contact_list.append({
            "contact_name": c["contact_name"],
            "total_due": str(c["total_due"]),
            "buckets": {k: str(v) for k, v in c["buckets"].items()},
        })

    return {
        "report": "AR Aging",
        "as_of": as_of.isoformat(),
        "total_outstanding": str(total_outstanding),
        "buckets": {k: str(v) for k, v in buckets.items()},
        "contacts": contact_list,
    }


@router.post("/reports/ap-aging")
def ap_aging(
    request: Request,
    as_of: date | None = None,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    if as_of is None:
        from datetime import datetime

        as_of = datetime.now(UTC).date()

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
    vendors: dict[str, dict] = {}

    for bill in bills:
        paid = _get_payments_for_bill(session, bill)
        outstanding = bill.total - paid

        if outstanding <= 0:
            continue

        total_outstanding += outstanding
        days_overdue = (as_of - bill.due_date).days if bill.due_date else 0

        if days_overdue == 0:
            bucket_key = "current"
        elif days_overdue <= 30:
            bucket_key = "0-30"
        elif days_overdue <= 60:
            bucket_key = "31-60"
        elif days_overdue <= 90:
            bucket_key = "61-90"
        else:
            bucket_key = "90+"

        buckets[bucket_key] += outstanding

        vendor_key = str(bill.contact_id)
        if vendor_key not in vendors:
            vendor_name = _get_contact_name(session, bill.contact_id)
            vendors[vendor_key] = {
                "vendor_name": vendor_name,
                "total_due": Decimal("0"),
                "buckets": {
                    "current": Decimal("0"),
                    "0-30": Decimal("0"),
                    "31-60": Decimal("0"),
                    "61-90": Decimal("0"),
                    "90+": Decimal("0"),
                },
            }
        vendors[vendor_key]["total_due"] += outstanding
        vendors[vendor_key]["buckets"][bucket_key] += outstanding

    vendor_list = []
    for v in vendors.values():
        vendor_list.append({
            "vendor_name": v["vendor_name"],
            "total_due": str(v["total_due"]),
            "buckets": {k: str(val) for k, val in v["buckets"].items()},
        })

    return {
        "report": "AP Aging",
        "as_of": as_of.isoformat(),
        "total_outstanding": str(total_outstanding),
        "buckets": {k: str(v) for k, v in buckets.items()},
        "vendors": vendor_list,
    }


@router.post("/reports/cash-summary")
def cash_summary(
    request: Request,
    payload: ReportRequest,
    session: Session = Depends(get_db),
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
) -> tuple[list[dict], list[dict], Decimal, Decimal]:
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

    revenue_map: dict[str, dict] = {}
    expense_map: dict[str, dict] = {}

    for acct, line, _ in results:
        net = line.debit - line.credit
        if acct.type == "revenue":
            total_revenue += net
            key = str(acct.id)
            if key not in revenue_map:
                revenue_map[key] = {"account": acct.name, "amount": Decimal("0")}
            revenue_map[key]["amount"] += net
        elif acct.type == "expense":
            total_expenses += net
            key = str(acct.id)
            if key not in expense_map:
                expense_map[key] = {"account": acct.name, "amount": Decimal("0")}
            expense_map[key]["amount"] += net

    revenue_lines = [{"account": v["account"], "amount": str(v["amount"])} for v in revenue_map.values()]
    expense_lines = [{"account": v["account"], "amount": str(v["amount"])} for v in expense_map.values()]

    return revenue_lines, expense_lines, total_revenue, total_expenses


def _get_bs_data(
    session: Session, company_id: UUID, as_of: date
) -> tuple[Decimal, Decimal, Decimal, list[dict], list[dict], list[dict]]:
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

    asset_map: dict[str, dict] = {}
    liability_map: dict[str, dict] = {}
    equity_map: dict[str, dict] = {}

    for acct, line, _ in results:
        net = line.debit - line.credit
        key = str(acct.id)
        if acct.type == "asset":
            assets += net
            if key not in asset_map:
                asset_map[key] = {"account_name": acct.name, "amount": Decimal("0")}
            asset_map[key]["amount"] += net
        elif acct.type == "liability":
            liabilities += net
            if key not in liability_map:
                liability_map[key] = {"account_name": acct.name, "amount": Decimal("0")}
            liability_map[key]["amount"] += net
        elif acct.type == "equity":
            equity += net
            if key not in equity_map:
                equity_map[key] = {"account_name": acct.name, "amount": Decimal("0")}
            equity_map[key]["amount"] += net

    asset_lines = [{"account_name": v["account_name"], "amount": str(v["amount"])} for v in asset_map.values()]
    liability_lines = [{"account_name": v["account_name"], "amount": str(v["amount"])} for v in liability_map.values()]
    equity_lines = [{"account_name": v["account_name"], "amount": str(v["amount"])} for v in equity_map.values()]

    return assets, liabilities, equity, asset_lines, liability_lines, equity_lines


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


def _get_contact_name(session: Session, contact_id: UUID) -> str:
    from src.models import Contact

    contact = session.get(Contact, contact_id)
    if contact:
        return contact.name
    return "Unknown"
