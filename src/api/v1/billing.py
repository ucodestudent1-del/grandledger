"""Billing and subscription endpoints (Stripe integration)."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from src.config import settings
from src.core.middleware import get_company_id, get_db, log_audit
from src.models import Company, Subscription, User
from src.schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    SubscriptionRead,
)

router = APIRouter(tags=["billing"])

# Stripe configuration
stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_PRICES = {
    "starter": "price_starter_monthly",
    "professional": "price_professional_monthly",
    "enterprise": "price_enterprise_monthly",
}

PLAN_LIMITS = {
    "starter": {"users": 3, "companies": 1},
    "professional": {"users": 10, "companies": 5},
    "enterprise": {"users": 100, "companies": 50},
}


def _get_or_create_stripe_customer(
    session: Session, company: Company, user: User
) -> str:
    """Get or create a Stripe customer for the company."""
    subscription = session.exec(
        select(Subscription).where(Subscription.company_id == company.id)
    ).first()

    if subscription and subscription.stripe_customer_id:
        return subscription.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=company.name,
        metadata={"company_id": str(company.id)},
    )

    if subscription:
        subscription.stripe_customer_id = customer.id
        session.add(subscription)
    else:
        subscription = Subscription(
            company_id=company.id,
            stripe_customer_id=customer.id,
            plan="starter",
            status="incomplete",
        )
        session.add(subscription)

    session.commit()
    return customer.id


@router.post("/billing/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    payload: CheckoutSessionRequest,
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> CheckoutSessionResponse:
    """Create a Stripe Checkout session for subscription signup."""
    user: User = request.state.user
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    if payload.plan not in PLAN_PRICES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan. Choose from: {', '.join(PLAN_PRICES.keys())}",
        )

    # Check if already subscribed to this plan
    existing = session.exec(
        select(Subscription).where(
            Subscription.company_id == company_id,
            Subscription.status == "active",
        )
    ).first()
    if existing and existing.plan == payload.plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already subscribed to this plan",
        )

    customer_id = _get_or_create_stripe_customer(session, company, user)

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": PLAN_PRICES[payload.plan],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
            metadata={
                "company_id": str(company_id),
                "plan": payload.plan,
            },
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {str(exc)}",
        ) from exc

    return CheckoutSessionResponse(
        checkout_url=checkout_session.url,
        session_id=checkout_session.id,
    )


@router.post("/billing/webhook")
async def stripe_webhook(
    request: Request,
    session: Session = Depends(get_db),
) -> dict:
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
        ) from None
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        ) from None

    # Idempotency: check if already processed

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        _handle_checkout_completed(session_data, session)

    elif event["type"] == "customer.subscription.created":
        sub_data = event["data"]["object"]
        _handle_subscription_created(sub_data, session)

    elif event["type"] == "customer.subscription.updated":
        sub_data = event["data"]["object"]
        _handle_subscription_updated(sub_data, session)

    elif event["type"] == "customer.subscription.deleted":
        sub_data = event["data"]["object"]
        _handle_subscription_deleted(sub_data, session)

    elif event["type"] == "invoice.payment_succeeded":
        inv_data = event["data"]["object"]
        _handle_invoice_payment_succeeded(inv_data, session)

    elif event["type"] == "invoice.payment_failed":
        inv_data = event["data"]["object"]
        _handle_invoice_payment_failed(inv_data, session)

    return {"received": True}


def _handle_checkout_completed(session_data: dict, session: Session) -> None:
    """Handle checkout.session.completed event."""
    customer_id = session_data.get("customer")
    subscription_id = session_data.get("subscription")
    plan = session_data.get("metadata", {}).get("plan", "starter")

    sub = session.exec(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    ).first()
    if sub:
        sub.stripe_subscription_id = subscription_id
        sub.stripe_price_id = session_data.get("line_items", {}).get("data", [{}])[0].get("price", {}).get("id")
        sub.plan = plan
        sub.status = "active"
        sub.current_period_start = datetime.fromtimestamp(
            session_data.get("created", 0), tz=UTC
        )
        session.add(sub)


def _handle_subscription_created(sub_data: dict, session: Session) -> None:
    """Handle customer.subscription.created event."""
    customer_id = sub_data.get("customer")
    sub = session.exec(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    ).first()
    if sub:
        sub.stripe_subscription_id = sub_data.get("id")
        sub.status = sub_data.get("status", "incomplete")
        sub.current_period_start = datetime.fromtimestamp(
            sub_data.get("current_period_start", 0), tz=UTC
        )
        sub.current_period_end = datetime.fromtimestamp(
            sub_data.get("current_period_end", 0), tz=UTC
        )
        session.add(sub)


def _handle_subscription_updated(sub_data: dict, session: Session) -> None:
    """Handle customer.subscription.updated event."""
    subscription_id = sub_data.get("id")
    sub = session.exec(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    ).first()
    if sub:
        sub.status = sub_data.get("status", sub.status)
        sub.cancel_at_period_end = sub_data.get("cancel_at_period_end", False)
        sub.current_period_start = datetime.fromtimestamp(
            sub_data.get("current_period_start", 0), tz=UTC
        )
        sub.current_period_end = datetime.fromtimestamp(
            sub_data.get("current_period_end", 0), tz=UTC
        )
        session.add(sub)


def _handle_subscription_deleted(sub_data: dict, session: Session) -> None:
    """Handle customer.subscription.deleted event."""
    subscription_id = sub_data.get("id")
    sub = session.exec(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    ).first()
    if sub:
        sub.status = "canceled"
        sub.canceled_at = datetime.now(UTC)
        session.add(sub)


def _handle_invoice_payment_succeeded(inv_data: dict, session: Session) -> None:
    """Handle invoice.payment.succeeded event."""
    stripe_invoice_id = inv_data.get("id")
    customer_id = inv_data.get("customer")

    # Check idempotency
    existing = session.exec(
        select(__import__("src.models.billing", fromlist=["InvoicePayment"]).InvoicePayment).where(
            __import__("src.models.billing", fromlist=["InvoicePayment"]).InvoicePayment.stripe_invoice_id
            == stripe_invoice_id
        )
    ).first()
    if existing:
        return

    sub = session.exec(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    ).first()
    if not sub:
        return

    payment = __import__("src.models.billing", fromlist=["InvoicePayment"]).InvoicePayment(
        company_id=sub.company_id,
        stripe_invoice_id=stripe_invoice_id,
        stripe_payment_intent_id=inv_data.get("payment_intent"),
        amount=inv_data.get("amount_paid", 0),
        currency=inv_data.get("currency", "usd"),
        status="paid",
        paid_at=datetime.fromtimestamp(inv_data.get("created", 0), tz=UTC),
    )
    session.add(payment)

    # Update subscription status
    sub.status = "active"
    session.add(sub)


def _handle_invoice_payment_failed(inv_data: dict, session: Session) -> None:
    """Handle invoice.payment_failed event."""
    customer_id = inv_data.get("customer")

    sub = session.exec(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    ).first()
    if sub:
        sub.status = "past_due"
        session.add(sub)


@router.get("/billing/subscription", response_model=SubscriptionRead)
def get_subscription(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> SubscriptionRead:
    """Get the current subscription for the company."""
    sub = session.exec(
        select(Subscription).where(Subscription.company_id == company_id)
    ).first()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found"
        )
    return sub


@router.post("/billing/subscription/cancel")
def cancel_subscription(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    """Cancel the subscription at period end."""
    user: User = request.state.user
    sub = session.exec(
        select(Subscription).where(Subscription.company_id == company_id)
    ).first()
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription"
        )

    try:
        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        sub.cancel_at_period_end = True
        session.add(sub)
        session.commit()

        log_audit(
            company_id=company_id,
            user_id=user.id,
            action="subscription.cancel",
            entity_type="Subscription",
            entity_id=sub.id,
            ip_address=request.client.host if request.client else None,
        )

        return {"message": "Subscription will cancel at period end"}
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {str(exc)}",
        ) from exc


@router.post("/billing/portal")
def create_customer_portal_session(
    request: Request,
    session: Session = Depends(get_db),
    company_id: UUID = Depends(get_company_id),
) -> dict:
    """Create a Stripe customer portal session for billing management."""
    sub = session.exec(
        select(Subscription).where(Subscription.company_id == company_id)
    ).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No customer found"
        )

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/billing",
        )

        portal_record = __import__("src.models.billing", fromlist=["CustomerPortalSession"]).CustomerPortalSession(
            company_id=company_id,
            stripe_session_id=portal_session.id,
            status="active",
            expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        )
        session.add(portal_record)
        session.commit()

        return {"portal_url": portal_session.url}
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {str(exc)}",
        ) from exc


@router.get("/billing/plans")
def get_plans() -> dict:
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price_monthly": 2900,
                "currency": "usd",
                "limits": PLAN_LIMITS["starter"],
                "description": "Perfect for freelancers and solo bookkeepers",
            },
            {
                "id": "professional",
                "name": "Professional",
                "price_monthly": 7900,
                "currency": "usd",
                "limits": PLAN_LIMITS["professional"],
                "description": "For growing small businesses",
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price_monthly": 19900,
                "currency": "usd",
                "limits": PLAN_LIMITS["enterprise"],
                "description": "For established accounting firms",
            },
        ]
    }
