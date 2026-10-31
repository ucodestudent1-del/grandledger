"""Add password reset tokens, active sessions, and user verification fields.

Revision ID: 0e13104a2cfe
Revises: 0002_period_lock
Create Date: 2026-10-31

"""
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0e13104a2cfe"
down_revision = "0002_period_lock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
    )

    op.create_table(
        "active_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, default=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
    )

    op.create_index("idx_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("idx_active_sessions_user_id", "active_sessions", ["user_id"])
    op.create_index("idx_active_sessions_token_hash", "active_sessions", ["refresh_token_hash"])


def downgrade() -> None:
    op.drop_index("idx_active_sessions_token_hash", table_name="active_sessions")
    op.drop_index("idx_active_sessions_user_id", table_name="active_sessions")
    op.drop_index("idx_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("active_sessions")
    op.drop_table("password_reset_tokens")
    op.drop_column("users", "is_active")
    op.drop_column("users", "is_verified")
