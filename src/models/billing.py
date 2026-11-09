"""Subscription and billing models."""
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.company import Company


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SubscriptionPlan(str):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class Subscription(SQLModel, table=True):
    """Customer subscription to GrandLedger SaaS."""

    __tablename__ = "subscriptions"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    stripe_customer_id: str = Field(max_length=255, index=True)
    stripe_subscription_id: str | None = Field(default=None, max_length=255, unique=True, index=True)
    stripe_price_id: str | None = Field(default=None, max_length=255)
    plan: str = Field(max_length=50)
    status: str = Field(default=SubscriptionStatus.INCOMPLETE, max_length=50)
    current_period_start: datetime | None = Field(default=None)
    current_period_end: datetime | None = Field(default=None)
    cancel_at_period_end: bool = Field(default=False)
    canceled_at: datetime | None = Field(default=None)
    trial_start: datetime | None = Field(default=None)
    trial_end: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=_utcnow, nullable=False, sa_column_kwargs={"onupdate": _utcnow})

    company: "Company" = Relationship(back_populates="subscription")


class InvoicePayment(SQLModel, table=True):
    """Record of SaaS invoice payments processed via Stripe."""

    __tablename__ = "invoice_payments"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    stripe_invoice_id: str = Field(max_length=255, unique=True, index=True)
    stripe_payment_intent_id: str | None = Field(default=None, max_length=255)
    amount: int = Field()  # cents
    currency: str = Field(default="usd", max_length=10)
    status: str = Field(max_length=50)
    paid_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)

    company: "Company" = Relationship(back_populates="invoice_payments")


class CustomerPortalSession(SQLModel, table=True):
    """Stripe customer portal session records."""

    __tablename__ = "customer_portal_sessions"

    id: UUID | None = Field(default_factory=uuid4, sa_column=Column(Uuid(), primary_key=True))
    company_id: UUID = Field(sa_column=Column(Uuid(), ForeignKey("companies.id", ondelete="CASCADE")))
    stripe_session_id: str = Field(max_length=255, unique=True, index=True)
    status: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    expires_at: datetime | None = Field(default=None)
