"""Company model."""
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as Uuid
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.audit import AuditLog
    from src.models.bank import BankAccount
    from src.models.bill import Bill
    from src.models.contact import Contact
    from src.models.file import File
    from src.models.invoice import Invoice
    from src.models.journal import JournalEntry
    from src.models.payment import Payment
    from src.models.user import User


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: UUID = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    name: str = Field(max_length=255)
    slug: str = Field(max_length=100, unique=True, index=True)
    currency: str = Field(default="USD", max_length=3)
    financial_year_start: date | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    users: list["User"] = Relationship(back_populates="company", sa_relationship_kwargs={"lazy": "selectin"})  # type: ignore[call-overload]
    accounts: list["Account"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    contacts: list["Contact"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    journal_entries: list["JournalEntry"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    invoices: list["Invoice"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    payments: list["Payment"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    bills: list["Bill"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    bank_accounts: list["BankAccount"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    audit_logs: list["AuditLog"] = Relationship(back_populates="company")  # type: ignore[call-overload]
    files: list["File"] = Relationship(back_populates="company")  # type: ignore[call-overload]
