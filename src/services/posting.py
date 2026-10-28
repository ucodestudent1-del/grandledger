"""The single posting function for all GL writes.

All Sales/Purchase/Payment features must call post_journal() — never write
JournalLine directly. This centralizes debit/credit validation.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from src.core.middleware import log_audit
from src.models import (
    Account,
    JournalEntry,
    JournalEntryStatus,
    JournalLine,
)


class JournalLineData:
    """Raw input for a journal line before persistence."""

    def __init__(
        self,
        account_id: UUID,
        description: str | None = None,
        debit: Decimal = Decimal("0"),
        credit: Decimal = Decimal("0"),
    ) -> None:
        self.account_id = account_id
        self.description = description
        self.debit = debit
        self.credit = credit


def validate_lines_balanced(lines: Sequence[JournalLineData]) -> None:
    total_debit = sum((ln.debit for ln in lines), Decimal("0"))
    total_credit = sum((ln.credit for ln in lines), Decimal("0"))
    if total_debit != total_credit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry is not balanced: debits={total_debit}, credits={total_credit}",
        )


def validate_accounts_exist(session: Session, company_id: UUID, lines: Sequence[JournalLineData]) -> None:
    for line in lines:
        stmt = select(Account).where(
            Account.id == line.account_id,
            Account.company_id == company_id,
        )
        account = session.exec(stmt).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account {line.account_id} not found or not in this company",
            )
        if not account.is_active and not account.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account {account.code} ({account.name}) is inactive",
            )


def generate_journal_number(session: Session, company_id: UUID, entry_date: date) -> str:
    year = entry_date.year
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.number.like(f"JE-{year}-%"))
        .order_by(JournalEntry.number.desc())
    )
    last = session.exec(stmt).first()
    if last:
        last_num = int(last.number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"JE-{year}-{next_num:05d}"


def post_journal(
    *,
    company_id: UUID,
    lines: list[JournalLineData],
    description: str | None,
    entry_date: date,
    created_by: UUID,
    source: str | None = None,
    session: Session | None = None,
    ip_address: str | None = None,
) -> JournalEntry:
    """Create a journal entry in draft status, validate balance, and return it.

    Callers must subsequently call `post_journal_entry` to transition to posted.
    """
    own_session = False
    if session is None:
        import src.database as db_module
        session = Session(db_module.engine)
        own_session = True

    try:
        validate_lines_balanced(lines)
        validate_accounts_exist(session, company_id, lines)

        number = generate_journal_number(session, company_id, entry_date)

        je = JournalEntry(
            company_id=company_id,
            number=number,
            entry_date=entry_date,
            description=description,
            source=source,
            created_by=created_by,
        )
        session.add(je)
        session.flush()

        for line in lines:
            session.add(
                JournalLine(
                    journal_entry_id=je.id,
                    account_id=line.account_id,
                    description=line.description,
                    debit=line.debit,
                    credit=line.credit,
                )
            )

        session.commit()
        session.refresh(je)

        log_audit(
            company_id=company_id,
            user_id=created_by,
            action="journal_entry.create",
            entity_type="JournalEntry",
            entity_id=je.id,
            after={"id": str(je.id), "number": je.number, "status": je.status},
            ip_address=ip_address,
        )

        return je
    except Exception:
        session.rollback()
        raise
    finally:
        if own_session:
            session.close()


def post_journal_entry(je_id: UUID, posted_by: UUID, ip_address: str | None = None) -> JournalEntry:
    """Transition a draft journal entry to posted status.

    The DB trigger enforces balance on posted entries.
    """
    from src.database import engine as db_engine

    with Session(db_engine) as session:
        je = session.get(JournalEntry, je_id)
        if not je:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found",
            )
        if je.status == JournalEntryStatus.POSTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Journal entry already posted",
            )
        if je.status == JournalEntryStatus.VOID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot post a voided journal entry",
            )

        before_state = {"status": je.status}
        je.status = JournalEntryStatus.POSTED
        je.posted_at = datetime.now(UTC)
        je.posted_by = posted_by
        session.add(je)
        session.commit()
        session.refresh(je)

        log_audit(
            company_id=je.company_id,
            user_id=posted_by,
            action="journal_entry.post",
            entity_type="JournalEntry",
            entity_id=je_id,
            before=before_state,
            after={"status": je.status, "posted_at": je.posted_at.isoformat()},
            ip_address=ip_address,
        )

        return je

def void_journal_entry(je_id: UUID, voided_by: UUID, ip_address: str | None = None) -> JournalEntry:
    """Void a journal entry (must be posted)."""
    from src.database import engine as db_engine

    with Session(db_engine) as session:
        je = session.get(JournalEntry, je_id)
        if not je:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found",
            )
        if je.status == JournalEntryStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot void a draft entry — delete it instead",
            )
        if je.status == JournalEntryStatus.VOID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Journal entry already voided",
            )

        before_state = {"status": je.status}
        je.status = JournalEntryStatus.VOID
        je.updated_at = datetime.now(UTC)
        session.add(je)
        session.commit()
        session.refresh(je)

        log_audit(
            company_id=je.company_id,
            user_id=voided_by,
            action="journal_entry.void",
            entity_type="JournalEntry",
            entity_id=je_id,
            before=before_state,
            after={"status": je.status},
            ip_address=ip_address,
        )

        return je


def reverse_journal_entry(
    je_id: UUID,
    reversed_by: UUID,
    entry_date: date | None = None,
    ip_address: str | None = None,
    session: Session | None = None,
) -> JournalEntry:
    """Create a reversing entry that negates all lines of the original.

    The original entry must be posted. The reversal entry is created in
    posted status with negated debits/credits.
    """
    own_session = False
    if session is None:
        import src.database as db_module

        session = Session(db_module.engine)
        own_session = True

    try:
        je = session.get(JournalEntry, je_id)
        if not je:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found",
            )
        if je.status != JournalEntryStatus.POSTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only posted entries can be reversed",
            )

        stmt = select(JournalLine).where(JournalLine.journal_entry_id == je_id)
        original_lines = session.exec(stmt).all()
        if not original_lines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No lines found on the journal entry to reverse",
            )

        reversal_lines = [
            JournalLineData(
                account_id=ln.account_id,
                description=f"Reversal of {ln.description}" if ln.description else f"Reversal of {je.number}",
                debit=ln.credit,
                credit=ln.debit,
            )
            for ln in original_lines
        ]

        reversal_date = entry_date or je.entry_date
        number = generate_journal_number(session, je.company_id, reversal_date)

        reversal = JournalEntry(
            company_id=je.company_id,
            number=f"REV-{number}",
            entry_date=reversal_date,
            description=f"Reversal of {je.number}: {je.description}" if je.description else f"Reversal of {je.number}",
            source="reversal",
            created_by=reversed_by,
            posted_by=reversed_by,
        )
        reversal.posted_at = datetime.now(UTC)
        reversal.posted_by = reversed_by
        reversal.status = JournalEntryStatus.POSTED
        session.add(reversal)
        session.flush()

        for line in reversal_lines:
            session.add(
                JournalLine(
                    journal_entry_id=reversal.id,
                    account_id=line.account_id,
                    description=line.description,
                    debit=line.debit,
                    credit=line.credit,
                )
            )

        session.commit()
        session.refresh(reversal)

        log_audit(
            company_id=je.company_id,
            user_id=reversed_by,
            action="journal_entry.reverse",
            entity_type="JournalEntry",
            entity_id=je_id,
            after={
                "reversed_entry_id": str(reversal.id),
                "reversed_entry_number": reversal.number,
            },
            ip_address=ip_address,
        )

        return reversal
    except Exception:
        session.rollback()
        raise
    finally:
        if own_session:
            session.close()


