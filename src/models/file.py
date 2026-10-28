"""File model."""
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as Uuid
from sqlalchemy import Column, ForeignKey
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.company import Company


def _utcnow() -> datetime:
    return datetime.now(UTC)


class File(SQLModel, table=True):
    __tablename__ = "files"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    url: str = Field(max_length=500)
    filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    size: int = Field()
    uploaded_at: datetime = Field(default_factory=_utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="files")  # type: ignore[call-overload]
