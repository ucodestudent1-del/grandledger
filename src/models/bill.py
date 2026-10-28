"""Bill and bill line models."""
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, ForeignKey, Text, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.company import Company
    from src.models.contact import Contact


class BillStatus(str):
    DRAFT = "draft"
    POSTED = "posted"
    VOID = "void"


class Bill(SQLModel, table=True):
    __tablename__ = "bills"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    contact_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("contacts.id")))
    number: str = Field(max_length=50)
    status: str = Field(default="draft", max_length=20)
    issue_date: date | None = Field(default=None)
    due_date: date | None = Field(default=None)
    subtotal: Decimal = Field(default=Decimal("0"), max_digits=20, decimal_places=4)
    tax_total: Decimal = Field(default=Decimal("0"), max_digits=20, decimal_places=4)
    total: Decimal = Field(default=Decimal("0"), max_digits=20, decimal_places=4)
    currency: str = Field(default="USD", max_length=3)
    journal_entry_id: UUID | None = Field(default=None, sa_column=Column(Uuid(), ForeignKey("journal_entries.id")))
    allocated_to: dict | None = Field(default=None, sa_column=Column(JSON))
    created_by: UUID = Field(sa_column=Column(Uuid(), ForeignKey("users.id")))

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="bills")  # type: ignore[call-overload]
    contact: "Contact" = Relationship(back_populates="bills")  # type: ignore[call-overload]
    lines: list["BillLine"] = Relationship(  # type: ignore[call-overload]
        back_populates="bill",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class BillLine(SQLModel, table=True):
    __tablename__ = "bill_lines"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    bill_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("bills.id", ondelete="CASCADE")))
    description: str = Field(sa_column=Column(Text))
    qty: Decimal = Field(default=Decimal("1"), max_digits=15, decimal_places=4)
    unit_price: Decimal = Field(max_digits=20, decimal_places=4)
    tax_rate: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    amount: Decimal = Field(max_digits=20, decimal_places=4)
    account_id: UUID | None = Field(default=None, sa_column=Column(Uuid(), ForeignKey("accounts.id")))

    bill: "Bill" = Relationship(back_populates="lines")  # type: ignore[call-overload]
    account: "Account" = Relationship(back_populates="bill_lines")  # type: ignore[call-overload]
