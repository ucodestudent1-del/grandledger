"""Password reset token model."""
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, String, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.user import User


def _utcnow() -> datetime:
    return datetime.now(UTC)


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    user_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("users.id", ondelete="CASCADE")))
    token_hash: str = Field(sa_column=Column(String(255), nullable=False))
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)

    user: "User" = Relationship(back_populates="password_reset_tokens")

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at
