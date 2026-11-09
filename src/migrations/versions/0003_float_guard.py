"""Add float-guard check constraints to money columns.

Prevents floating-point values from persisting at the database level
by constraining money columns to 4 decimal places of precision.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_float_guard"
down_revision = "0002_period_lock"
branch_labels = None
depends_on = None

# Columns guarded against float drift (table, column)
GUARDED_COLUMNS: list[tuple[str, str]] = [
    ("journal_lines", "debit"),
    ("journal_lines", "credit"),
    ("invoices", "subtotal"),
    ("invoices", "tax_total"),
    ("invoices", "total"),
    ("invoice_lines", "unit_price"),
    ("invoice_lines", "amount"),
    ("payments", "amount"),
    ("bills", "subtotal"),
    ("bills", "tax_total"),
    ("bills", "total"),
    ("bill_lines", "unit_price"),
    ("bill_lines", "amount"),
    ("bank_accounts", "starting_balance"),
    ("bank_transactions", "amount"),
    ("bank_transactions", "balance"),
]

# 4 decimal places of precision (numeric(20,4) max scale)
PRECISION_SCALE = 4


def _check_constraint_name(table: str, column: str) -> str:
    return f"chk_{table}_{column}_4dp"


def upgrade() -> None:
    for table, column in GUARDED_COLUMNS:
        constraint_name = _check_constraint_name(table, column)
        # Ensure values have at most 4 decimal places:
        # ROUND(col, 4) == col means no fractional part beyond 4dp
        op.create_check_constraint(
            constraint_name,
            table,
            sa.text(f"ROUND({column}::numeric, {PRECISION_SCALE}) = {column}"),
        )


def downgrade() -> None:
    for table, column in GUARDED_COLUMNS:
        constraint_name = _check_constraint_name(table, column)
        op.drop_constraint(constraint_name, table, type_="check")
