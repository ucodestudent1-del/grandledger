"""Dev seed: creates a demo company with chart of accounts and sample data."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from src.core.security import get_password_hash
from src.database import engine
from src.models import (
    Account,
    AccountType,
    BankAccount,
    Bill,
    BillLine,
    BillStatus,
    Company,
    Contact,
    ContactType,
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    User,
    UserRole,
)

DEFAULT_COA: list[dict] = [
    {"code": "1000", "name": "Cash", "type": AccountType.ASSET},
    {"code": "1010", "name": "Accounts Receivable", "type": AccountType.ASSET},
    {"code": "1020", "name": "Inventory", "type": AccountType.ASSET},
    {"code": "1100", "name": "Accounts Payable", "type": AccountType.LIABILITY},
    {"code": "1200", "name": "Credit Card", "type": AccountType.LIABILITY},
    {"code": "1300", "name": "Loans Payable", "type": AccountType.LIABILITY},
    {"code": "1400", "name": "Owner's Equity", "type": AccountType.EQUITY},
    {"code": "1500", "name": "Retained Earnings", "type": AccountType.EQUITY},
    {"code": "4000", "name": "Sales Revenue", "type": AccountType.REVENUE},
    {"code": "4100", "name": "Service Revenue", "type": AccountType.REVENUE},
    {"code": "5000", "name": "Office Expenses", "type": AccountType.EXPENSE},
    {"code": "5100", "name": "Salaries Expense", "type": AccountType.EXPENSE},
    {"code": "5200", "name": "Cost of Goods Sold", "type": AccountType.EXPENSE},
    {"code": "5300", "name": "Marketing Expenses", "type": AccountType.EXPENSE},
    {"code": "5400", "name": "Bank Fees", "type": AccountType.EXPENSE},
]

DEFAULT_BANK_ACCOUNTS: list[dict] = [
    {"name": "Operating Account", "bank_name": "First National Bank", "account_number": "123456789", "starting_balance": Decimal("5000.00")},
]

DEMO_INVOICES: list[dict] = [
    {
        "contact": {"name": "Acme Corp", "type": ContactType.CUSTOMER, "email": "billing@acme.com"},
        "lines": [
            {"description": "Consulting Services", "qty": Decimal("10"), "unit_price": Decimal("150.00"), "tax_rate": Decimal("0")},
        ],
    },
    {
        "contact": {"name": "StartupXYZ", "type": ContactType.CUSTOMER, "email": "hello@startupxyz.com"},
        "lines": [
            {"description": "Monthly Subscription", "qty": Decimal("1"), "unit_price": Decimal("500.00"), "tax_rate": Decimal("10")},
        ],
    },
]

DEMO_BILLS: list[dict] = [
    {
        "contact": {"name": "Office Supply Inc", "type": ContactType.VENDOR, "email": "orders@officesupply.com"},
        "lines": [
            {"description": "Office Supplies", "qty": Decimal("1"), "unit_price": Decimal("250.00"), "tax_rate": Decimal("0")},
        ],
    },
    {
        "contact": {"name": "Cloud Provider LLC", "type": ContactType.VENDOR, "email": "billing@cloudprovider.com"},
        "lines": [
            {"description": "Cloud Hosting - Monthly", "qty": Decimal("1"), "unit_price": Decimal("1200.00"), "tax_rate": Decimal("10")},
        ],
    },
]


def seed_company(
    company_name: str = "Demo Company", company_slug: str = "demo"
) -> tuple[Company, User]:
    with Session(engine) as session:
        existing = session.exec(select(Company).where(Company.slug == company_slug)).first()
        if existing:
            print(f"Company '{company_slug}' already exists, skipping seed.")
            user_row = session.exec(select(User).where(User.company_id == existing.id)).first()
            if user_row is None:
                raise RuntimeError("Existing company has no owner user")
            return existing, user_row

        company = Company(name=company_name, slug=company_slug, currency="USD")
        session.add(company)
        session.flush()

        # Create default COA
        for acct in DEFAULT_COA:
            session.add(
                Account(
                    company_id=company.id,
                    code=acct["code"],
                    name=acct["name"],
                    type=acct["type"],
                    is_system=True,
                )
            )

        # Create bank accounts
        for ba in DEFAULT_BANK_ACCOUNTS:
            session.add(BankAccount(company_id=company.id, **ba))

        # Create demo user
        user = User(
            company_id=company.id,
            email="demo@grandledger.com",
            name="Demo User",
            role=UserRole.OWNER,
            password_hash=get_password_hash("password123"),
        )
        session.add(user)
        session.flush()

        # Create demo contacts and invoices
        for inv_data in DEMO_INVOICES:
            contact_data = inv_data["contact"]
            contact = Contact(company_id=company.id, **contact_data)
            session.add(contact)
            session.flush()

            invoice = Invoice(
                company_id=company.id,
                contact_id=contact.id,
                number=f"INV-2026-{100 + DEMO_INVOICES.index(inv_data):05d}",
                status=InvoiceStatus.DRAFT,
                issue_date=date(2026, 10, 1),
                due_date=date(2026, 10, 31),
                created_by=user.id,
            )

            subtotal = Decimal("0")
            tax_total = Decimal("0")
            for line_data in inv_data["lines"]:
                amount = line_data["qty"] * line_data["unit_price"]
                tax = amount * line_data["tax_rate"] / Decimal("100")
                invoice.lines.append(
                    InvoiceLine(
                        description=line_data["description"],
                        qty=line_data["qty"],
                        unit_price=line_data["unit_price"],
                        tax_rate=line_data["tax_rate"],
                        amount=amount,
                    )
                )
                subtotal += amount
                tax_total += tax

            invoice.subtotal = subtotal
            invoice.tax_total = tax_total
            invoice.total = subtotal + tax_total
            session.add(invoice)

        # Create demo bills
        for bill_data in DEMO_BILLS:
            contact_data = bill_data["contact"]
            contact = Contact(company_id=company.id, **contact_data)
            session.add(contact)
            session.flush()

            bill = Bill(
                company_id=company.id,
                contact_id=contact.id,
                number=f"BILL-2026-{100 + DEMO_BILLS.index(bill_data):05d}",
                status=BillStatus.DRAFT,
                issue_date=date(2026, 10, 1),
                due_date=date(2026, 10, 31),
                created_by=user.id,
            )

            subtotal = Decimal("0")
            tax_total = Decimal("0")
            for line_data in bill_data["lines"]:
                amount = line_data["qty"] * line_data["unit_price"]
                tax = amount * line_data["tax_rate"] / Decimal("100")
                bill.lines.append(
                    BillLine(
                        description=line_data["description"],
                        qty=line_data["qty"],
                        unit_price=line_data["unit_price"],
                        tax_rate=line_data["tax_rate"],
                        amount=amount,
                    )
                )
                subtotal += amount
                tax_total += tax

            bill.subtotal = subtotal
            bill.tax_total = tax_total
            bill.total = subtotal + tax_total
            session.add(bill)

        session.commit()
        session.refresh(company)
        session.refresh(user)

        print(f"Seeded company '{company_name}' with COA, bank accounts, contacts, invoices, and bills.")
        print("  Email: demo@grandledger.com")
        print("  Password: password123")
        return company, user


def clear_seed() -> None:
    """Delete all demo data (useful for re-seeding)."""
    from sqlmodel import SQLModel

    with Session(engine) as session:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        session.commit()
        print("Cleared all data.")


if __name__ == "__main__":
    clear_seed()
    seed_company()
