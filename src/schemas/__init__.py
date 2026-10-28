"""Pydantic schemas (request/response DTOs) for all API endpoints."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    refresh_token: str


class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    company_name: str | None = None
    company_slug: str | None = None
    role: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    email: str
    name: str
    role: str
    is_external_accountant: bool = False


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class CompanyCreate(BaseModel):
    name: str
    slug: str
    currency: str = "USD"
    financial_year_start: date | None = None


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    currency: str
    financial_year_start: date | None = None


class AccountCreate(BaseModel):
    code: str
    name: str
    type: str
    parent_id: UUID | None = None
    is_active: bool = True


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    code: str
    name: str
    type: str
    parent_id: UUID | None = None
    is_active: bool
    is_system: bool


class ContactCreate(BaseModel):
    name: str
    type: str
    email: str | None = None
    phone: str | None = None
    address: dict | None = None


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name: str
    type: str
    email: str | None = None
    phone: str | None = None
    address: dict | None = None


class JournalLineCreate(BaseModel):
    account_id: UUID
    description: str | None = None
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")


class JournalEntryCreate(BaseModel):
    lines: list[JournalLineCreate]
    description: str | None = None
    entry_date: date
    source: str | None = None


class JournalLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    journal_entry_id: UUID
    account_id: UUID
    description: str | None = None
    debit: Decimal
    credit: Decimal


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    number: str
    entry_date: date
    description: str | None = None
    status: str
    posted_at: datetime | None = None
    posted_by: UUID | None = None
    source: str | None = None
    created_by: UUID
    lines: list[JournalLineRead]
    created_at: datetime
    updated_at: datetime


class InvoiceLineCreate(BaseModel):
    description: str
    qty: Decimal = Decimal("1")
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0")
    account_id: UUID | None = None


class InvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    description: str
    qty: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    amount: Decimal
    account_id: UUID | None = None


class InvoiceCreate(BaseModel):
    contact_id: UUID
    lines: list[InvoiceLineCreate]
    issue_date: date | None = None
    due_date: date | None = None
    currency: str = "USD"


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    contact_id: UUID
    number: str
    status: str
    issue_date: date | None = None
    due_date: date | None = None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineRead]


class BillLineCreate(BaseModel):
    description: str
    qty: Decimal = Decimal("1")
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0")
    account_id: UUID | None = None


class BillLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bill_id: UUID
    description: str
    qty: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    amount: Decimal
    account_id: UUID | None = None


class BillCreate(BaseModel):
    contact_id: UUID
    lines: list[BillLineCreate]
    issue_date: date | None = None
    due_date: date | None = None
    currency: str = "USD"


class BillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    contact_id: UUID
    number: str
    status: str
    issue_date: date | None = None
    due_date: date | None = None
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    lines: list[BillLineRead]


class PaymentCreate(BaseModel):
    contact_id: UUID
    type: str
    amount: Decimal
    payment_date: date
    allocated_to: list[dict[str, Any]] | None = None
    reference: str | None = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    contact_id: UUID
    type: str
    amount: Decimal
    payment_date: date
    allocated_to: dict | None = None
    journal_entry_id: UUID | None = None
    reference: str | None = None
    created_at: datetime


class BankAccountCreate(BaseModel):
    name: str
    bank_name: str | None = None
    account_number: str | None = None
    starting_balance: Decimal = Decimal("0")
    currency: str = "USD"


class BankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    name: str
    bank_name: str | None = None
    account_number: str | None = None
    starting_balance: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class BankTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    bank_account_id: UUID
    txn_date: date | None = None
    description: str
    amount: Decimal
    balance: Decimal | None = None
    imported_at: datetime
    matched: bool
    journal_entry_id: UUID | None = None
    status: str


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    user_id: UUID | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    before: dict | None = None
    after: dict | None = None
    ip_address: str | None = None
    created_at: datetime


class ReportRequest(BaseModel):
    start_date: date
    end_date: date
    account_id: UUID | None = None


__all__ = [
    "Token",
    "UserCreate",
    "UserRead",
    "LoginRequest",
    "RefreshRequest",
    "CompanyCreate",
    "CompanyRead",
    "AccountCreate",
    "AccountRead",
    "ContactCreate",
    "ContactRead",
    "JournalLineCreate",
    "JournalEntryCreate",
    "JournalLineRead",
    "JournalEntryRead",
    "JournalLineCreate",
    "InvoiceLineCreate",
    "InvoiceLineRead",
    "InvoiceCreate",
    "InvoiceRead",
    "BillLineCreate",
    "BillLineRead",
    "BillCreate",
    "BillRead",
    "PaymentCreate",
    "PaymentRead",
    "BankAccountCreate",
    "BankAccountRead",
    "BankTransactionRead",
    "AuditLogRead",
    "ReportRequest",
]
