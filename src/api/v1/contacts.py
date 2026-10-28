"""Contacts (Customers/Vendors) endpoints."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.models import Contact
from src.schemas import ContactCreate, ContactRead

router = APIRouter(tags=["contacts"])


def get_session() -> Session:
    import src.database as db_module
    return Session(db_module.engine)


def get_company_id(request: Request) -> UUID:
    from src.core.middleware import get_company_id as _gci

    return _gci(request)


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
) -> list[ContactRead]:
    stmt = select(Contact).where(Contact.company_id == company_id)
    if contact_type:
        stmt = stmt.where(Contact.type == contact_type)
    contacts = session.exec(stmt).all()
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
