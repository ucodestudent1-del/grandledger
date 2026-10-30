"""Add locked_period_end to companies for period locking.

Revision ID: 0002_period_lock
Revises: 0001_initial
Create Date: 2026-10-26
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_period_lock"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("locked_period_end", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "locked_period_end")
