"""Invoices (AR) endpoints."""
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
    Contact,
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    User,
)
from src.schemas import InvoiceCreate, InvoiceLineRead, InvoiceRead
from src.services.posting import JournalLineData, post_journal, post_journal_entry

router = APIRouter(tags=["invoices"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.post("/invoices", response_model=InvoiceRead)
def create_invoice(
    payload: InvoiceCreate,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> InvoiceRead:
    user: User = request.state.user

    contact = session.get(Contact, payload.contact_id)
    if not contact or contact.company_id != company_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    if contact.type != "customer":
        raise HTTPException(status_code=400, detail="Contact must be a customer")

    stmt = select(Account).where(Account.company_id == company_id, Account.type == "revenue")
    revenue_account = session.exec(stmt).first()
    if not revenue_account:
        raise HTTPException(status_code=400, detail="No revenue account configured for this company")

    ar_account_stmt = select(Account).where(
        Account.company_id == company_id, Account.name.ilike("%accounts receivable%")
    )
    ar_account = session.exec(ar_account_stmt).first()
    if not ar_account:
        ar_account = revenue_account

    invoice = Invoice(
        company_id=company_id,
        contact_id=payload.contact_id,
        status=InvoiceStatus.DRAFT,
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
        invoice.lines.append(
            InvoiceLine(
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

    invoice.subtotal = subtotal
    invoice.tax_total = tax_total
    invoice.total = subtotal + tax_total

    number = _generate_invoice_number(session, company_id)
    invoice.number = number

    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return _build_read(invoice)


@router.get("/invoices", response_model=list[InvoiceRead])
def list_invoices(
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
    status_filter: str | None = None,
    contact_id: UUID | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[InvoiceRead]:
    page_val, page_size_val = get_page_params(page, page_size)
    stmt = select(Invoice).where(Invoice.company_id == company_id)
    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter)
    if contact_id:
        stmt = stmt.where(Invoice.contact_id == contact_id)
    items, _, _ = paginate_query(stmt, page_val, page_size_val)
    invoices = session.exec(items).all()
    return [_build_read(inv) for inv in invoices]


@router.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(
    invoice_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
):
    """Download an invoice as PDF."""
    from src.services.pdf import render_invoice_pdf

    invoice = session.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company_id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdf_bytes = render_invoice_pdf(invoice)

    import io

    from starlette.responses import StreamingResponse

    pdf_stream = io.BytesIO(pdf_bytes)
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=invoice_{invoice.number}.pdf"},
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> InvoiceRead:
    invoice = session.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _build_read(invoice)


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceRead)
def issue_invoice(
    invoice_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> InvoiceRead:
    user: User = request.state.user
    invoice = session.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft invoices can be issued")

    ip = request.client.host if request.client else None

    # Create journal entry: DR Accounts Receivable, CR Revenue, CR Tax Payable
    ar_account = _get_ar_account(session, company_id)
    revenue_account = _get_revenue_account(session, company_id)
    if not ar_account or not revenue_account:
        raise HTTPException(
            status_code=400,
            detail="Missing required accounts (Accounts Receivable, Revenue) for this company",
        )
    tax_account = _get_tax_account(session, company_id)

    lines: list[JournalLineData] = [
        JournalLineData(
            account_id=ar_account.id,
            description=f"Invoice {invoice.number}",
            debit=invoice.total,
            credit=Decimal("0"),
        ),
        JournalLineData(
            account_id=revenue_account.id,
            description=f"Invoice {invoice.number}",
            debit=Decimal("0"),
            credit=invoice.subtotal,
        ),
    ]
    if invoice.tax_total > 0:
        if not tax_account:
            raise HTTPException(
                status_code=400,
                detail="Missing tax account for this company",
            )
        lines.append(
            JournalLineData(
                account_id=tax_account.id,
                description=f"Tax on invoice {invoice.number}",
                debit=Decimal("0"),
                credit=invoice.tax_total,
            )
        )

    je = post_journal(
        company_id=company_id,
        lines=lines,
        description=f"Invoice {invoice.number} issued",
             entry_date=invoice.issue_date or datetime.now(UTC).date(),
        created_by=user.id,
        source="invoice",
        session=session,
        ip_address=ip,
    )
    post_journal_entry(je.id, posted_by=user.id, ip_address=ip)

    invoice.status = InvoiceStatus.ISSUED
    invoice.journal_entry_id = je.id
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return _build_read(invoice)


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceRead)
def void_invoice(
    invoice_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> InvoiceRead:
    user: User = request.state.user
    invoice = session.get(Invoice, invoice_id)
    if not invoice or invoice.company_id != company_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status in (InvoiceStatus.VOID, InvoiceStatus.PAID):
        raise HTTPException(status_code=400, detail="Cannot void this invoice")

    invoice.status = InvoiceStatus.VOID
    session.add(invoice)
    session.commit()
    session.refresh(invoice)

    # If the invoice has a posted JE, we need to reverse it
    if invoice.journal_entry_id:
        ip = request.client.host if request.client else None
        ar_account = _get_ar_account(session, company_id)
        revenue_account = _get_revenue_account(session, company_id)
        if not ar_account or not revenue_account:
            raise HTTPException(
                status_code=400,
                detail="Missing required accounts for reversal",
            )
        reversal_je = post_journal(
            company_id=company_id,
            lines=[
                JournalLineData(
                    account_id=ar_account.id,
                    description=f"Void reversal of invoice {invoice.number}",
                    debit=Decimal("0"),
                    credit=invoice.total,
                ),
                JournalLineData(
                    account_id=revenue_account.id,
                    description=f"Void reversal of invoice {invoice.number}",
                    debit=invoice.subtotal,
                    credit=Decimal("0"),
                ),
            ],
            description=f"Void reversal of invoice {invoice.number}",
             entry_date=datetime.now(UTC).date(),
             created_by=user.id,
             source="invoice_void",
            session=session,
            ip_address=ip,
        )
        post_journal_entry(reversal_je.id, posted_by=user.id, ip_address=ip)

    return _build_read(invoice)


def _generate_invoice_number(session: Session, company_id: UUID) -> str:
    year = datetime.now(UTC).year
    stmt = (
        select(Invoice)
        .where(Invoice.company_id == company_id)
        .where(Invoice.number.like(f"INV-{year}-%"))
        .order_by(Invoice.number.desc())
    )
    last = session.exec(stmt).first()
    if last:
        last_num = int(last.number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"INV-{year}-{next_num:05d}"


def _get_ar_account(session: Session, company_id: UUID) -> Account | None:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.name.ilike("%accounts receivable%"),
    )
    return session.exec(stmt).first()


def _get_revenue_account(session: Session, company_id: UUID) -> Account | None:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.type == "revenue",
    )
    return session.exec(stmt).first()


def _get_tax_account(session: Session, company_id: UUID) -> Account | None:
    stmt = select(Account).where(
        Account.company_id == company_id,
        Account.name.ilike("%tax%"),
    )
    return session.exec(stmt).first()


def _build_read(invoice: Invoice) -> InvoiceRead:
    return InvoiceRead(
        id=invoice.id,
        company_id=invoice.company_id,
        contact_id=invoice.contact_id,
        number=invoice.number,
        status=invoice.status,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        subtotal=invoice.subtotal,
        tax_total=invoice.tax_total,
        total=invoice.total,
        currency=invoice.currency,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        lines=[InvoiceLineRead.model_validate(ln) for ln in invoice.lines],
    )
