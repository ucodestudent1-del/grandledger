"""Payment model."""
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, Date, ForeignKey, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.company import Company
    from src.models.contact import Contact


def _utcnow() -> datetime:
    return datetime.now(UTC)


class PaymentType(str):
    PAYMENT = "payment"
    RECEIPT = "receipt"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    contact_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("contacts.id")))
    type: str = Field(max_length=20)
    amount: Decimal = Field(max_digits=20, decimal_places=4)
    payment_date: date = Field(sa_column=Column("payment_date", Date))
    allocated_to: dict | None = Field(default=None, sa_column=Column(JSON))
    journal_entry_id: UUID | None = Field(default=None, sa_column=Column(Uuid(), ForeignKey("journal_entries.id")))
    reference: str | None = Field(default=None, max_length=255)
    created_by: UUID = Field(sa_column=Column(Uuid(), ForeignKey("users.id")))

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="payments")  # type: ignore[call-overload]
    contact: "Contact" = Relationship(back_populates="payments")  # type: ignore[call-overload]
