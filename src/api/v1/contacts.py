"""Contacts (Customers/Vendors) endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.core.middleware import get_company_id
from src.core.pagination import get_page_params, paginate_query
from src.models import Contact
from src.schemas import ContactCreate, ContactRead

router = APIRouter(tags=["contacts"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


@router.post("/contacts", response_model=ContactRead)
def create_contact(
    payload: ContactCreate,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> ContactRead:
    contact = Contact(company_id=company_id, **payload.model_dump())
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@router.get("/contacts", response_model=list[ContactRead])
def list_contacts(
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
    contact_type: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[ContactRead]:
    page_val, page_size_val = get_page_params(page, page_size)
    stmt = select(Contact).where(Contact.company_id == company_id)
    if contact_type:
        stmt = stmt.where(Contact.type == contact_type)
    items, _, _ = paginate_query(stmt, page_val, page_size_val)
    contacts = session.exec(items).all()
    return contacts


@router.get("/contacts/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> ContactRead:
    contact = session.get(Contact, contact_id)
    if not contact or contact.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return contact


@router.patch("/contacts/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: UUID,
    payload: ContactCreate,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> ContactRead:
    contact = session.get(Contact, contact_id)
    if not contact or contact.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    contact_data = payload.model_dump(exclude_unset=True, exclude={"company_id"})
    for field, value in contact_data.items():
        setattr(contact, field, value)
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}", response_model=ContactRead)
def delete_contact(
    contact_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    company_id: UUID = Depends(get_company_id),
) -> ContactRead:
    from src.models import Bill, Invoice

    contact = session.get(Contact, contact_id)
    if not contact or contact.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    has_invoices = session.exec(
        select(Invoice).where(Invoice.contact_id == contact_id, Invoice.company_id == company_id)
    ).first()
    has_bills = session.exec(
        select(Bill).where(Bill.contact_id == contact_id, Bill.company_id == company_id)
    ).first()
    if has_invoices or has_bills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete contact with existing invoices or bills",
        )
    session.delete(contact)
    session.commit()
    return contact
