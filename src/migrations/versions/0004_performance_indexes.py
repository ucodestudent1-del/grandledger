"""Add database indexes for performance on frequently queried columns.

Indexes on company_id (for RLS queries), entry_date (for reports),
account_id (for ledger queries), and status (for filtering).
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_performance_indexes"
down_revision = "0003_float_guard"
branch_labels = None
depends_on = None

# (table, column) pairs to index
INDEX_COLUMNS: list[tuple[str, str]] = [
    ("users", "company_id"),
    ("accounts", "company_id"),
    ("accounts", "type"),
    ("contacts", "company_id"),
    ("contacts", "type"),
    ("journal_entries", "company_id"),
    ("journal_entries", "entry_date"),
    ("journal_entries", "status"),
    ("journal_lines", "journal_entry_id"),
    ("journal_lines", "account_id"),
    ("invoices", "company_id"),
    ("invoices", "contact_id"),
    ("invoices", "status"),
    ("invoice_lines", "invoice_id"),
    ("invoice_lines", "account_id"),
    ("bills", "company_id"),
    ("bills", "contact_id"),
    ("bills", "status"),
    ("bill_lines", "bill_id"),
    ("bill_lines", "account_id"),
    ("payments", "company_id"),
    ("payments", "contact_id"),
    ("payments", "type"),
    ("bank_accounts", "company_id"),
    ("bank_transactions", "company_id"),
    ("bank_transactions", "bank_account_id"),
    ("bank_transactions", "txn_date"),
    ("bank_transactions", "matched"),
    ("bank_transactions", "status"),
    ("audit_logs", "company_id"),
    ("audit_logs", "created_at"),
    ("active_sessions", "user_id"),
    ("active_sessions", "expires_at"),
    ("password_reset_tokens", "user_id"),
]


def _index_name(table: str, column: str) -> str:
    return f"ix_{table}_{column}"


def upgrade() -> None:
    for table, column in INDEX_COLUMNS:
        index_name = _index_name(table, column)
        op.create_index(index_name, table, [column])


def downgrade() -> None:
    for table, column in INDEX_COLUMNS:
        index_name = _index_name(table, column)
        op.drop_index(index_name, table_name=table)
