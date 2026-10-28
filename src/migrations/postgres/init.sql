-- GrandLedger database initialization
-- Creates the journal entry balance enforcement trigger

CREATE OR REPLACE FUNCTION enforce_balanced_entry()
RETURNS TRIGGER AS $$
DECLARE
    total_debit NUMERIC(20,4) := 0;
    total_credit NUMERIC(20,4) := 0;
BEGIN
    -- Only enforce on posted entries
    IF NEW.status = 'posted' THEN
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

CREATE TRIGGER balanced_entry_insert_trigger
BEFORE INSERT ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION enforce_balanced_entry();
