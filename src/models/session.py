"""Active session / refresh token model for revocation."""
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, ForeignKey, String, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.user import User


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ActiveSession(SQLModel, table=True):
    __tablename__ = "active_sessions"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    user_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE")))
    refresh_token_hash: str = Field(sa_column=Column(String(255), nullable=False))
    user_agent: str | None = Field(default=None, sa_column=Column(String(500)))
    ip_address: str | None = Field(default=None, max_length=45)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False, sa_column=Column(Boolean, default=False))
    last_used_at: datetime = Field(default_factory=_utcnow, nullable=False)

    user: "User" = Relationship(back_populates="active_sessions")
