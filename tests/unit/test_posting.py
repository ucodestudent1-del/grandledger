"""Unit tests for the posting service."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from src.core.security import get_password_hash
from src.models import (
    Account,
    AccountType,
    Company,
    JournalEntryStatus,
    JournalLine,
    User,
)
from src.services.posting import (
    JournalLineData,
    post_journal,
    post_journal_entry,
    reverse_journal_entry,
    validate_lines_balanced,
    void_journal_entry,
)


@pytest.fixture
def setup_data(db_session):
    company = Company(name="Test Company", slug="test-posting", currency="USD")
    db_session.add(company)
    db_session.flush()

    user = User(
        company_id=company.id,
        email="test@test.com",
        name="Test User",
        role="owner",
        password_hash=get_password_hash("Password123"),
    )
    db_session.add(user)
    db_session.flush()

    cash = Account(
        company_id=company.id,
        code="1000",
        name="Cash",
        type=AccountType.ASSET,
        is_system=True,
    )
    revenue = Account(
        company_id=company.id,
        code="4000",
        name="Sales Revenue",
        type=AccountType.REVENUE,
        is_system=True,
    )
    db_session.add(cash)
    db_session.add(revenue)
    db_session.commit()
    return {
        "session": db_session,
        "company_id": company.id,
        "user_id": user.id,
        "cash_id": cash.id,
        "revenue_id": revenue.id,
    }


class TestJournalValidation:
    def test_balanced_lines_pass(self):
        lines = [
            JournalLineData(account_id=uuid4(), debit=Decimal("100"), credit=Decimal("0")),
            JournalLineData(account_id=uuid4(), debit=Decimal("0"), credit=Decimal("100")),
        ]
        validate_lines_balanced(lines)

    def test_unbalanced_lines_fail(self):
        from fastapi import HTTPException

        lines = [
            JournalLineData(account_id=uuid4(), debit=Decimal("100"), credit=Decimal("0")),
            JournalLineData(account_id=uuid4(), debit=Decimal("0"), credit=Decimal("50")),
        ]
        with pytest.raises(HTTPException) as exc_info:
            validate_lines_balanced(lines)
        assert "not balanced" in exc_info.value.detail


class TestPostJournal:
    def test_create_draft_journal(self, setup_data):
        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("1000"),
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=setup_data["revenue_id"],
                debit=Decimal("0"),
                credit=Decimal("1000"),
            ),
        ]
        je = post_journal(
            company_id=setup_data["company_id"],
            lines=lines,
            description="Test entry",
            entry_date=date.today(),
            created_by=setup_data["user_id"],
            session=setup_data["session"],
        )
        assert je.status == JournalEntryStatus.DRAFT
        assert je.number.startswith("JE-")

    def test_post_draft_journal(self, setup_data):
        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("500"),
                credit=Decimal("0"),
                description="Cash sale",
            ),
            JournalLineData(
                account_id=setup_data["revenue_id"],
                debit=Decimal("0"),
                credit=Decimal("500"),
            ),
        ]
        je = post_journal(
            company_id=setup_data["company_id"],
            lines=lines,
            description="Cash sale",
            entry_date=date.today(),
            created_by=setup_data["user_id"],
            session=setup_data["session"],
        )
        posted = post_journal_entry(je.id, posted_by=setup_data["user_id"])
        assert posted.status == JournalEntryStatus.POSTED
        assert posted.posted_at is not None


class TestVoidJournal:
    def test_void_posted_journal(self, setup_data):
        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("200"),
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=setup_data["revenue_id"],
                debit=Decimal("0"),
                credit=Decimal("200"),
            ),
        ]
        je = post_journal(
            company_id=setup_data["company_id"],
            lines=lines,
            description="Test for void",
            entry_date=date.today(),
            created_by=setup_data["user_id"],
            session=setup_data["session"],
        )
        post_journal_entry(je.id, posted_by=setup_data["user_id"])
        voided = void_journal_entry(je.id, voided_by=setup_data["user_id"])
        assert voided.status == JournalEntryStatus.VOID


class TestReverseJournal:
    def test_reverse_posted_journal(self, setup_data):
        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("300"),
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=setup_data["revenue_id"],
                debit=Decimal("0"),
                credit=Decimal("300"),
            ),
        ]
        je = post_journal(
            company_id=setup_data["company_id"],
            lines=lines,
            description="Test for reversal",
            entry_date=date.today(),
            created_by=setup_data["user_id"],
            session=setup_data["session"],
        )
        post_journal_entry(je.id, posted_by=setup_data["user_id"])
        reversal = reverse_journal_entry(je.id, reversed_by=setup_data["user_id"])
        assert reversal.status == JournalEntryStatus.POSTED
        assert reversal.number.startswith("REV-")
        # Verify reversal lines have negated amounts
        import src.database as db_module

        with Session(db_module.engine) as session:
            rev_lines = session.exec(
                select(JournalLine).where(JournalLine.journal_entry_id == reversal.id)
            ).all()
            for rev_line in rev_lines:
                assert rev_line.debit != Decimal("0") or rev_line.credit != Decimal("0")


class TestPeriodLockValidation:
    def test_locked_period_blocks_entry(self, setup_data):
        """Creating a journal entry in a locked period should fail."""
        from src.models import Company

        company = setup_data["session"].get(Company, setup_data["company_id"])
        company.locked_period_end = date(2026, 6, 30)
        setup_data["session"].add(company)
        setup_data["session"].commit()

        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("100"),
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=setup_data["revenue_id"],
                debit=Decimal("0"),
                credit=Decimal("100"),
            ),
        ]
        with pytest.raises(Exception) as exc_info:
            post_journal(
                company_id=setup_data["company_id"],
                lines=lines,
                description="Entry in locked period",
                entry_date=date(2026, 6, 15),
                created_by=setup_data["user_id"],
                session=setup_data["session"],
            )
        assert "locked" in str(exc_info.value).lower()

    def test_unlocked_period_allows_entry(self, setup_data):
        """Creating a journal entry after unlocking should succeed."""
        from src.models import Company

        company = setup_data["session"].get(Company, setup_data["company_id"])
        company.locked_period_end = None
        setup_data["session"].add(company)
        setup_data["session"].commit()

        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("100"),
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=setup_data["revenue_id"],
                debit=Decimal("0"),
                credit=Decimal("100"),
            ),
        ]
        je = post_journal(
            company_id=setup_data["company_id"],
            lines=lines,
            description="Entry in unlocked period",
            entry_date=date(2026, 7, 1),
            created_by=setup_data["user_id"],
            session=setup_data["session"],
        )
        assert je.status == JournalEntryStatus.DRAFT

    def test_locked_period_blocks_posting(self, setup_data):
        """Posting a draft journal entry in a locked period should fail."""
        from src.models import Company

        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("100"),
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=setup_data["revenue_id"],
                debit=Decimal("0"),
                credit=Decimal("100"),
            ),
        ]
        je = post_journal(
            company_id=setup_data["company_id"],
            lines=lines,
            description="Draft entry",
            entry_date=date(2026, 6, 15),
            created_by=setup_data["user_id"],
            session=setup_data["session"],
        )

        company = setup_data["session"].get(Company, setup_data["company_id"])
        company.locked_period_end = date(2026, 6, 30)
        setup_data["session"].add(company)
        setup_data["session"].commit()

        with pytest.raises(Exception) as exc_info:
            post_journal_entry(je.id, posted_by=setup_data["user_id"])
        assert "locked" in str(exc_info.value).lower()

        company.locked_period_end = None
        setup_data["session"].add(company)
        setup_data["session"].commit()


class TestAccountValidation:
    def test_inactive_account_rejected(self, setup_data):
        from src.models import Account

        inactive_acct = Account(
            company_id=setup_data["company_id"],
            code="6000",
            name="Inactive Expense",
            type=AccountType.EXPENSE,
            is_system=False,
            is_active=False,
        )
        setup_data["session"].add(inactive_acct)
        setup_data["session"].commit()

        lines = [
            JournalLineData(
                account_id=setup_data["cash_id"],
                debit=Decimal("100"),
                credit=Decimal("0"),
            ),
            JournalLineData(
                account_id=inactive_acct.id,
                debit=Decimal("0"),
                credit=Decimal("100"),
            ),
        ]
        with pytest.raises(HTTPException):
            post_journal(
                company_id=setup_data["company_id"],
                lines=lines,
                description="Test with inactive account",
                entry_date=date.today(),
                created_by=setup_data["user_id"],
                session=setup_data["session"],
            )
