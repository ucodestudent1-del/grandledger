"""User model."""
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as Uuid
from sqlalchemy import Column, ForeignKey
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.company import Company
    from src.models.journal import JournalEntry


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UserRole(str):
    OWNER = "owner"
    ACCOUNTANT = "accountant"
    BOOKKEEPER = "bookkeeper"
    READONLY = "readonly"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    email: str = Field(max_length=255)
    name: str = Field(max_length=255)
    role: str = Field(default="owner", max_length=50)
    password_hash: str = Field(max_length=255)
    google_id: str | None = Field(default=None, max_length=255)
    is_external_accountant: bool = Field(default=False)

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False, sa_column_kwargs={"onupdate": _utcnow})

    company: "Company" = Relationship(back_populates="users")  # type: ignore[call-overload]

    journal_entries_posted: list["JournalEntry"] = Relationship(  # type: ignore[call-overload]
        back_populates="posted_by_user",
        sa_relationship_kwargs={"foreign_keys": "JournalEntry.posted_by"},
    )
    journal_entries_created: list["JournalEntry"] = Relationship(  # type: ignore[call-overload]
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "JournalEntry.created_by"},
    )
