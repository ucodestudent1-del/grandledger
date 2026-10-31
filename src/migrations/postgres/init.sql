-- GrandLedger database initialization
-- Creates the journal entry balance enforcement trigger and RLS policies

CREATE OR REPLACE FUNCTION enforce_balanced_entry()
RETURNS TRIGGER AS $$
DECLARE
    total_debit NUMERIC(20,4) := 0;
    total_credit NUMERIC(20,4) := 0;
BEGIN
    -- Only enforce on posted entries
    IF NEW.status = 'posted' AND (OLD.status IS NULL OR OLD.status != 'posted') THEN
        SELECT COALESCE(SUM(dl.debit), 0), COALESCE(SUM(dl.credit), 0)
        INTO total_debit, total_credit
        FROM journal_lines dl
        WHERE dl.journal_entry_id = NEW.id;

        IF (total_debit - total_credit) <> 0 THEN
            RAISE EXCEPTION 'Journal entry % is not balanced: debits=%, credits=%',
                NEW.id, total_debit, total_credit;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER balanced_entry_trigger
BEFORE UPDATE ON journal_entries
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION enforce_balanced_entry();

-- Row-Level Security (RLS) for multi-tenant isolation
-- The application sets app.company_id on each connection via middleware
-- This provides defense-in-depth alongside application-level filtering

CREATE OR REPLACE FUNCTION set_company_id(p_company_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.company_id', p_company_id::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable RLS on all tenant-scoped tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW SECURITY;
ALTER TABLE journal_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW SECURITY;
ALTER TABLE invoice_lines ENABLE ROW SECURITY;
ALTER TABLE bills ENABLE ROW SECURITY;
ALTER TABLE bill_lines ENABLE ROW SECURITY;
ALTER TABLE payments ENABLE ROW SECURITY;
ALTER TABLE bank_accounts ENABLE ROW SECURITY;
ALTER TABLE bank_transactions ENABLE ROW SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_reset_tokens ENABLE ROW SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;

-- Policy: only see data for the current company
CREATE POLICY company_isolation_policy ON companies
    FOR ALL TO app_user
    USING (id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON users
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON accounts
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON journal_entries
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON journal_lines
    FOR ALL TO app_user
    USING (
        journal_entry_id IN (
            SELECT id FROM journal_entries WHERE company_id = current_setting('app.company_id', true)::UUID
        )
    );

CREATE POLICY company_isolation_policy ON contacts
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON invoices
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON invoice_lines
    FOR ALL TO app_user
    USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE company_id = current_setting('app.company_id', true)::UUID
        )
    );

CREATE POLICY company_isolation_policy ON bills
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON bill_lines
    FOR ALL TO app_user
    USING (
        bill_id IN (
            SELECT id FROM bills WHERE company_id = current_setting('app.company_id', true)::UUID
        )
    );

CREATE POLICY company_isolation_policy ON payments
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON bank_accounts
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON bank_transactions
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON audit_logs
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);

CREATE POLICY company_isolation_policy ON active_sessions
    FOR ALL TO app_user
    USING (user_id IN (
        SELECT id FROM users WHERE company_id = current_setting('app.company_id', true)::UUID
    ));

CREATE POLICY company_isolation_policy ON password_reset_tokens
    FOR ALL TO app_user
    USING (user_id IN (
        SELECT id FROM users WHERE company_id = current_setting('app.company_id', true)::UUID
    ));

CREATE POLICY company_isolation_policy ON files
    FOR ALL TO app_user
    USING (company_id = current_setting('app.company_id', true)::UUID);
