"""Bills (AP) endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from src.core.middleware import get_company_id
from src.core.pagination import get_page_params, paginate_query
from src.models import (
    Account,
    Bill,
    BillLine,
    BillStatus,
    Contact,
    User,
)
from src.schemas import BillCreate, BillLineRead, BillRead
from src.services.posting import JournalLineData, post_journal, post_journal_entry

router = APIRouter(tags=["bills"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.post("/bills", response_model=BillRead)
def create_bill(
    payload: BillCreate,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> BillRead:
    user: User = request.state.user

    contact = session.get(Contact, payload.contact_id)
    if not contact or contact.company_id != company_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    if contact.type != "vendor":
        raise HTTPException(status_code=400, detail="Contact must be a vendor")

    bill = Bill(
        company_id=company_id,
        contact_id=payload.contact_id,
        status=BillStatus.DRAFT,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        currency="USD",
        created_by=user.id,
    )

    subtotal = Decimal("0")
    tax_total = Decimal("0")
    for line in payload.lines:
        amount = line.qty * line.unit_price
        tax = amount * line.tax_rate / Decimal("100")
        bill.lines.append(
            BillLine(
                description=line.description,
                qty=line.qty,
                unit_price=line.unit_price,
                tax_rate=line.tax_rate,
                amount=amount,
                account_id=line.account_id,
            )
        )
        subtotal += amount
        tax_total += tax

    bill.subtotal = subtotal
    bill.tax_total = tax_total
    bill.total = subtotal + tax_total
    bill.number = _generate_bill_number(session, company_id)

    session.add(bill)
    session.commit()
    session.refresh(bill)
    return _build_read(bill)


@router.get("/bills", response_model=list[BillRead])
def list_bills(
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
    status_filter: str | None = None,
    contact_id: UUID | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[BillRead]:
    page_val, page_size_val = get_page_params(page, page_size)
    stmt = select(Bill).where(Bill.company_id == company_id)
    if status_filter:
        stmt = stmt.where(Bill.status == status_filter)
    if contact_id:
        stmt = stmt.where(Bill.contact_id == contact_id)
    items, _, _ = paginate_query(stmt, page_val, page_size_val)
    bills = session.exec(items).all()
    return [_build_read(b) for b in bills]


@router.get("/bills/{bill_id}", response_model=BillRead)
def get_bill(
    bill_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> BillRead:
    bill = session.get(Bill, bill_id)
    if not bill or bill.company_id != company_id:
        raise HTTPException(status_code=404, detail="Bill not found")
    return _build_read(bill)


@router.post("/bills/{bill_id}/post", response_model=BillRead)
def post_bill(
    bill_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> BillRead:
    user: User = request.state.user
    bill = session.get(Bill, bill_id)
    if not bill or bill.company_id != company_id:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.status != BillStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft bills can be posted")

    ip = request.client.host if request.client else None

    # Create journal entry: DR Expense, CR Accounts Payable
    ap_account = _get_ap_account(session, company_id)
    expense_account = _get_expense_account(session, company_id)

    lines: list[JournalLineData] = []
    for line in bill.lines:
        exp_account = session.get(Account, line.account_id) if line.account_id else expense_account
        lines.append(
            JournalLineData(
                account_id=exp_account.id if exp_account else expense_account.id,
                description=f"Bill {bill.number}: {line.description}",
                debit=line.amount + (line.amount * line.tax_rate / Decimal("100")),
                credit=Decimal("0"),
            )
        )
    lines.append(
        JournalLineData(
            account_id=ap_account.id,
            description=f"Bill {bill.number} to {bill.contact.name}",
            debit=Decimal("0"),
            credit=bill.total,
        )
    )

    je = post_journal(
        company_id=company_id,
        lines=lines,
        description=f"Bill {bill.number} posted",
             entry_date=bill.issue_date or datetime.now(UTC).date(),
        created_by=user.id,
        source="bill",
        session=session,
        ip_address=ip,
    )
    post_journal_entry(je.id, posted_by=user.id, ip_address=ip)

    bill.status = BillStatus.POSTED
    bill.journal_entry_id = je.id
    session.add(bill)
    session.commit()
    session.refresh(bill)
    return _build_read(bill)


@router.post("/bills/{bill_id}/void", response_model=BillRead)
def void_bill(
    bill_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> BillRead:
    user: User = request.state.user
    bill = session.get(Bill, bill_id)
    if not bill or bill.company_id != company_id:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.status in (BillStatus.VOID,):
        raise HTTPException(status_code=400, detail="Bill already voided")

    bill.status = BillStatus.VOID
    session.add(bill)
    session.commit()
    session.refresh(bill)

    if bill.journal_entry_id:
        ip = request.client.host if request.client else None
        reversal_je = post_journal(
            company_id=company_id,
            lines=[
                JournalLineData(
                    account_id=_get_ap_account(session, company_id).id,
                    description=f"Void reversal of bill {bill.number}",
                    debit=Decimal("0"),
                    credit=bill.total,
                ),
                JournalLineData(
                    account_id=_get_expense_account(session, company_id).id,
                    description=f"Void reversal of bill {bill.number}",
                    debit=bill.subtotal,
                    credit=Decimal("0"),
                ),
            ],
            description=f"Void reversal of bill {bill.number}",
             entry_date=datetime.now(UTC).date(),
             created_by=user.id,
             source="bill_void",
            session=session,
            ip_address=ip,
        )
        post_journal_entry(reversal_je.id, posted_by=user.id, ip_address=ip)

    return _build_read(bill)


def _generate_bill_number(session: Session, company_id: UUID) -> str:
    year = datetime.now(UTC).year
    stmt = (
        select(Bill)
        .where(Bill.company_id == company_id)
        .where(Bill.number.like(f"BILL-{year}-%"))
        .order_by(Bill.number.desc())
    )
    last = session.exec(stmt).first()
    if last:
        last_num = int(last.number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"BILL-{year}-{next_num:05d}"


def _get_ap_account(session: Session, company_id: UUID) -> Account:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.name.ilike("%accounts payable%"),
    )
    return session.exec(stmt).first()


def _get_expense_account(session: Session, company_id: UUID) -> Account:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.type == "expense",
    )
    return session.exec(stmt).first()


def _get_tax_account(session: Session, company_id: UUID) -> Account | None:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.name.ilike("%tax%"),
    )
    return session.exec(stmt).first()


def _build_read(bill: Bill) -> BillRead:
    return BillRead(
        id=bill.id,
        company_id=bill.company_id,
        contact_id=bill.contact_id,
        number=bill.number,
        status=bill.status,
        issue_date=bill.issue_date,
        due_date=bill.due_date,
        subtotal=bill.subtotal,
        tax_total=bill.tax_total,
        total=bill.total,
        currency=bill.currency,
        created_at=bill.created_at,
        updated_at=bill.updated_at,
        lines=[BillLineRead.model_validate(ln) for ln in bill.lines],
    )
