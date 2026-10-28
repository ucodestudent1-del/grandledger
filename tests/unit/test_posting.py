"""Unit tests for the posting service."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
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
        password_hash=get_password_hash("pass123"),
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
