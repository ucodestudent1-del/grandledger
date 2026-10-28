"""Contact (Customer/Vendor) model."""
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, ForeignKey, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.bill import Bill
    from src.models.company import Company
    from src.models.invoice import Invoice
    from src.models.payment import Payment


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ContactType(str):
    CUSTOMER = "customer"
    VENDOR = "vendor"


class Contact(SQLModel, table=True):
    __tablename__ = "contacts"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    name: str = Field(max_length=255)
    type: str = Field(max_length=20)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: dict | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="contacts")  # type: ignore[call-overload]
    invoices: list["Invoice"] = Relationship(back_populates="contact")  # type: ignore[call-overload]
    payments: list["Payment"] = Relationship(back_populates="contact")  # type: ignore[call-overload]
    bills: list["Bill"] = Relationship(back_populates="contact")  # type: ignore[call-overload]
