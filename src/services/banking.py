"""Banking service: CSV parsing, import, and reconciliation helpers."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from decimal import Decimal


def parse_csv_bank_statement(
    content: str,
    has_header: bool = True,
    date_col: str = "date",
    desc_col: str = "description",
    amount_col: str = "amount",
    balance_col: str = "balance",
) -> list[dict]:
    """Parse CSV bank statement content into structured transaction dicts.

    Supports common CSV formats from major banks. Returns a list of dicts
    with keys: date, description, amount, balance.
    """
    reader = csv.DictReader(io.StringIO(content)) if has_header else csv.reader(io.StringIO(content))

    transactions: list[dict] = []

    if has_header:
        for row in reader:
            txn = _parse_csv_row(row, date_col, desc_col, amount_col, balance_col)
            if txn:
                transactions.append(txn)
    else:
        headers = [date_col, desc_col, amount_col, balance_col]
        for row in reader:
            if len(row) < 3:
                continue
            row_dict = dict(zip(headers, row, strict=False))
            txn = _parse_csv_row(row_dict, date_col, desc_col, amount_col, balance_col)
            if txn:
                transactions.append(txn)

    return transactions


def _parse_csv_row(
    row: dict,
    date_col: str,
    desc_col: str,
    amount_col: str,
    balance_col: str,
) -> dict | None:
    date_str = (row.get(date_col) or row.get("Date") or "").strip()
    desc_str = (row.get(desc_col) or row.get("Description") or "").strip()
    amount_str = (row.get(amount_col) or row.get("Amount") or "").strip()
    balance_str = (row.get(balance_col) or row.get("Balance") or "").strip()

    if not date_str and not desc_str:
        return None

    entry_date = _parse_date(date_str)

    try:
        amount = Decimal(amount_str) if amount_str else Decimal("0")
    except Exception:
        amount = Decimal("0")

    try:
        balance = Decimal(balance_str) if balance_str else None
    except Exception:
        balance = None

    # Handle withdrawals/deposits columns
    withdrawal = (row.get("Withdrawal") or row.get("debit") or "").strip()
    deposit = (row.get("Deposit") or row.get("credit") or "").strip()
    if withdrawal or deposit:
        amount = Decimal("0")
        try:
            if withdrawal:
                amount -= Decimal(withdrawal)
            if deposit:
                amount += Decimal(deposit)
        except Exception:
            pass

    return {
        "date": entry_date,
        "description": desc_str[:500],
        "amount": amount,
        "balance": balance,
    }


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m/%d/%y",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.utcnow()


def match_transaction_to_journal(
    transactions: list[dict],
    journal_entries: list[dict],
    threshold: Decimal = Decimal("0.01"),
) -> list[dict]:
    """Suggest matches between imported bank transactions and journal entries.

    Uses amount + fuzzy description matching. Returns matched pairs.
    """
    from difflib import SequenceMatcher

    matches: list[dict] = []

    for txn in transactions:
        best_match = None
        best_score = 0.0

        for je in journal_entries:
            # Compare amounts
            je_amount = je.get("amount", Decimal("0"))
            amount_diff = abs(txn["amount"] - je_amount)
            if amount_diff > threshold:
                continue

            # Fuzzy description match
            desc1 = (txn.get("description") or "").lower()
            desc2 = (je.get("description") or "").lower()
            ratio = SequenceMatcher(None, desc1, desc2).ratio()

            if ratio > best_score:
                best_score = ratio
                best_match = je

        if best_match and best_score > 0.3:
            matches.append({
                "transaction": txn,
                "journal_entry": best_match,
                "confidence": best_score,
            })

    return matches
