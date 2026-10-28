"""API route registration."""
from fastapi import APIRouter

from src.api.v1 import (
    accounts,
    audit,
    auth,
    banking,
    bills,
    companies,
    contacts,
    invoices,
    journals,
    payments,
    reports,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(companies.router)
api_router.include_router(accounts.router)
api_router.include_router(contacts.router)
api_router.include_router(journals.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(bills.router)
api_router.include_router(banking.router)
api_router.include_router(reports.router)
api_router.include_router(audit.router)
