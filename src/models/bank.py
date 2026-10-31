"""Bank account and bank transaction models."""
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, ForeignKey, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.company import Company


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BankAccountStatus(str):
    PENDING = "pending"
    CLEARED = "cleared"
    RECONCILED = "reconciled"


class BankAccount(SQLModel, table=True):
    __tablename__ = "bank_accounts"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    name: str = Field(max_length=255)
    bank_name: str | None = Field(default=None, max_length=255)
    account_number: str | None = Field(default=None, max_length=100)
    starting_balance: Decimal = Field(default=Decimal("0"), max_digits=20, decimal_places=4)
    currency: str = Field(default="USD", max_length=3)

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False, sa_column_kwargs={"onupdate": _utcnow})

    company: "Company" = Relationship(back_populates="bank_accounts")  # type: ignore[call-overload]
    transactions: list["BankTransaction"] = Relationship(  # type: ignore[call-overload]
        back_populates="bank_account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class BankTransaction(SQLModel, table=True):
    __tablename__ = "bank_transactions"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    bank_account_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("bank_accounts.id", ondelete="CASCADE")))
    txn_date: date = Field(sa_column=Column("date", Date))
    description: str = Field(max_length=500)
    amount: Decimal = Field(max_digits=20, decimal_places=4)
    balance: Decimal | None = Field(default=None, max_digits=20, decimal_places=4)
    imported_at: datetime = Field(default_factory=_utcnow, nullable=False)
    matched: bool = Field(default=False)
    journal_entry_id: UUID | None = Field(default=None, sa_column=Column(Uuid(), ForeignKey("journal_entries.id")))
    status: str = Field(default="pending", max_length=20)

    bank_account: "BankAccount" = Relationship(back_populates="transactions")  # type: ignore[call-overload]
