"""Journal entry and journal line models."""
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, ForeignKey, Text, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.company import Company
    from src.models.user import User


def _utcnow() -> datetime:
    return datetime.now(UTC)


class JournalEntryStatus(str):
    DRAFT = "draft"
    POSTED = "posted"
    VOID = "void"


class JournalEntry(SQLModel, table=True):
    __tablename__ = "journal_entries"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    number: str = Field(max_length=50)
    entry_date: date = Field(sa_column=Column("entry_date", Date))
    description: str | None = Field(default=None, sa_column=Column(Text))
    status: str = Field(default="draft", max_length=20)
    posted_at: datetime | None = Field(default=None)
    posted_by: UUID | None = Field(default=None, sa_column=Column(Uuid(), ForeignKey("users.id")))
    source: str | None = Field(default=None, max_length=100)
    created_by: UUID = Field(sa_column=Column(Uuid(), ForeignKey("users.id")))

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="journal_entries")  # type: ignore[call-overload]
    lines: list["JournalLine"] = Relationship(  # type: ignore[call-overload]
        back_populates="journal_entry",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    posted_by_user: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "JournalEntry.posted_by"})
    created_by_user: "User" = Relationship(sa_relationship_kwargs={"foreign_keys": "JournalEntry.created_by"})


class JournalLine(SQLModel, table=True):
    __tablename__ = "journal_lines"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    journal_entry_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("journal_entries.id", ondelete="CASCADE")))
    account_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("accounts.id")))
    description: str | None = Field(default=None, sa_column=Column(Text))
    debit: Decimal = Field(default=Decimal("0"), max_digits=20, decimal_places=4)
    credit: Decimal = Field(default=Decimal("0"), max_digits=20, decimal_places=4)

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)

    journal_entry: "JournalEntry" = Relationship(back_populates="lines")  # type: ignore[call-overload]
    account: "Account" = Relationship(back_populates="journal_lines")  # type: ignore[call-overload]
