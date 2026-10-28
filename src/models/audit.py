"""Audit log model."""
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, ForeignKey, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.company import Company


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    user_id: UUID | None = Field(default=None, sa_column=Column(Uuid(), ForeignKey("users.id")))
    action: str = Field(max_length=100)
    entity_type: str = Field(max_length=100)
    entity_id: str | None = Field(default=None)
    before: dict | None = Field(default=None, sa_column=Column(JSON))
    after: dict | None = Field(default=None, sa_column=Column(JSON))
    ip_address: str | None = Field(default=None, max_length=45)

    created_at: datetime = Field(default_factory=_utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="audit_logs")  # type: ignore[call-overload]
