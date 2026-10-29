"""Payments (AR receipts/AP payments) endpoints."""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from src.core.middleware import get_company_id
from src.core.pagination import get_page_params, paginate_query
from src.models import (
    Account,
    BankAccount,
    Contact,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentType,
    User,
)
from src.schemas import PaymentCreate, PaymentRead
from src.services.posting import JournalLineData, post_journal, post_journal_entry

router = APIRouter(tags=["payments"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.post("/payments", response_model=PaymentRead)
def create_payment(
    payload: PaymentCreate,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> PaymentRead:
    user: User = request.state.user

    contact = session.get(Contact, payload.contact_id)
    if not contact or contact.company_id != company_id:
        raise HTTPException(status_code=404, detail="Contact not found")

    if payload.type == PaymentType.RECEIPT and contact.type != "customer":
        raise HTTPException(status_code=400, detail="Receipts require a customer contact")
    if payload.type == PaymentType.PAYMENT and contact.type != "vendor":
        raise HTTPException(status_code=400, detail="Payments require a vendor contact")

    payment = Payment(
        company_id=company_id,
        contact_id=payload.contact_id,
        type=payload.type,
        amount=payload.amount,
        payment_date=payload.payment_date,
        reference=payload.reference,
        allocated_to=payload.allocated_to,
        created_by=user.id,
    )
    session.add(payment)
    session.flush()

    # Build journal entry for the payment
    # Receipt: DR Bank, CR Accounts Receivable
    # Payment: DR Accounts Payable, CR Bank
    bank_account = _get_default_bank_account(session, company_id)
    if not bank_account:
        raise HTTPException(
            status_code=400,
            detail="No bank account configured for this company",
        )
    if payload.type == PaymentType.RECEIPT:
        ar_account = _get_ar_account(session, company_id)
        credit_account = ar_account if ar_account else bank_account
        lines = [
            JournalLineData(
                account_id=bank_account.id,
                description=f"Payment {payment.id} for {contact.name}",
                debit=payload.amount,
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=credit_account.id,
                description=f"Payment {payment.id} for {contact.name}",
                debit=Decimal("0"),
                credit=payload.amount,
            ),
        ]
    else:  # payment
        ap_account = _get_ap_account(session, company_id)
        debit_account = ap_account if ap_account else bank_account
        lines = [
            JournalLineData(
                account_id=debit_account.id,
                description=f"Payment {payment.id} to {contact.name}",
                debit=payload.amount,
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=bank_account.id,
                description=f"Payment {payment.id} to {contact.name}",
                debit=Decimal("0"),
                credit=payload.amount,
            ),
        ]

    ip = request.client.host if request.client else None
    je = post_journal(
        company_id=company_id,
        lines=lines,
        description=f"{payload.type.capitalize()} of {payload.amount} from {contact.name}",
        entry_date=payload.payment_date,
        created_by=user.id,
        source="payment",
        session=session,
        ip_address=ip,
    )
    post_journal_entry(je.id, posted_by=user.id, ip_address=ip)

    payment.journal_entry_id = je.id
    session.add(payment)
    session.commit()
    session.refresh(payment)

    # Mark invoices as paid if fully allocated
    _apply_allocations(session, company_id, payload, user, payment, request)

    return _build_read(payment)


@router.get("/payments", response_model=list[PaymentRead])
def list_payments(
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
    payment_type: str | None = None,
    contact_id: UUID | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[PaymentRead]:
    page_val, page_size_val = get_page_params(page, page_size)
    stmt = select(Payment).where(Payment.company_id == company_id)
    if payment_type:
        stmt = stmt.where(Payment.type == payment_type)
    if contact_id:
        stmt = stmt.where(Payment.contact_id == contact_id)
    items, _, _ = paginate_query(stmt, page_val, page_size_val)
    payments = session.exec(items).all()
    return [_build_read(p) for p in payments]


@router.get("/payments/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> PaymentRead:
    payment = session.get(Payment, payment_id)
    if not payment or payment.company_id != company_id:
        raise HTTPException(status_code=404, detail="Payment not found")
    return _build_read(payment)


def _get_default_bank_account(session: Session, company_id: UUID) -> BankAccount | None:
    stmt = select(BankAccount).where(BankAccount.company_id == company_id)
    return session.exec(stmt).first()


def _get_ar_account(session: Session, company_id: UUID) -> Account | None:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.name.ilike("%accounts receivable%"),
    )
    return session.exec(stmt).first()


def _get_ap_account(session: Session, company_id: UUID) -> Account | None:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.name.ilike("%accounts payable%"),
    )
    return session.exec(stmt).first()


def _apply_allocations(
    session: Session,
    company_id: UUID,
    payload: PaymentCreate,
    user: User,
    payment: Payment,
    request: Request,
) -> None:
    """Mark invoices as paid or partially paid based on allocations."""
    if not payload.allocated_to:
        return

    for alloc in payload.allocated_to:
        invoice_id = alloc.get("invoice_id")
        alloc_amount = Decimal(str(alloc.get("amount", 0)))
        if not invoice_id or alloc_amount <= 0:
            continue

        invoice = session.get(Invoice, UUID(invoice_id))
        if not invoice or invoice.company_id != company_id:
            continue

        total_allocated = sum(
            Decimal(str(a.get("amount", 0)))
            for a in (invoice.allocated_to or [])
            if a.get("invoice_id") == invoice_id
        ) + alloc_amount

        if total_allocated >= invoice.total:
            invoice.status = InvoiceStatus.PAID
        elif total_allocated > 0:
            invoice.status = InvoiceStatus.ISSUED  # partially paid, keep issued

        if not invoice.allocated_to:
            invoice.allocated_to = []
        invoice.allocated_to.append({"invoice_id": str(invoice_id), "amount": str(alloc_amount)})
        session.add(invoice)

    session.commit()


def _build_read(payment: Payment) -> PaymentRead:
    return PaymentRead(
        id=payment.id,
        company_id=payment.company_id,
        contact_id=payment.contact_id,
        type=payment.type,
        amount=payment.amount,
        payment_date=payment.payment_date,
        allocated_to=payment.allocated_to,
        journal_entry_id=payment.journal_entry_id,
        reference=payment.reference,
        created_at=payment.created_at,
    )
