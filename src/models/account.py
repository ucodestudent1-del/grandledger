"""Account (Chart of Accounts) model."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as Uuid
from sqlalchemy import Column, ForeignKey
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.bill import BillLine
    from src.models.company import Company
    from src.models.invoice import InvoiceLine
    from src.models.journal import JournalLine


class AccountType(str):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    code: str = Field(max_length=50)
    name: str = Field(max_length=255)
    type: str = Field(max_length=50)
    parent_id: UUID | None = Field(default=None, sa_column=Column(Uuid(), ForeignKey("accounts.id")))
    is_active: bool = Field(default=True)
    is_system: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="accounts")  # type: ignore[call-overload]
    parent: "Account" = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Account.id"},
    )  # type: ignore[call-overload]
    children: list["Account"] = Relationship(back_populates="parent")  # type: ignore[call-overload]
    journal_lines: list["JournalLine"] = Relationship(back_populates="account")  # type: ignore[call-overload]
    invoice_lines: list["InvoiceLine"] = Relationship(back_populates="account")  # type: ignore[call-overload]
    bill_lines: list["BillLine"] = Relationship(back_populates="account")  # type: ignore[call-overload]
