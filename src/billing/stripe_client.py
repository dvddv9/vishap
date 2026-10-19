# -*- coding: utf-8 -*-
"""Stripe client wrapper (v6.1), lazy init."""
import os
import time

import stripe

from dotenv import load_dotenv
load_dotenv()



class BillingError(Exception):
    """Raised when Stripe billing is misconfigured."""


def _stripe():
    """Lazy-init the Stripe module with the API key from env."""
    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        raise BillingError("STRIPE_SECRET_KEY not set")
    stripe.api_key = key
    return stripe


def create_checkout_session(customer_email: str, success_url: str, cancel_url: str) -> dict:
    """Create a Stripe Checkout Session (subscription mode)."""
    s = _stripe()
    session = s.checkout.Session.create(
        mode="subscription",
        customer_email=customer_email,
        line_items=[{"price": os.getenv("STRIPE_PRICE_ID"), "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return {"session_id": session.id, "url": session.url}


def get_customer(email: str) -> dict:
    """Look up a Stripe customer by email (first match)."""
    s = _stripe()
    customers = s.Customer.list(email=email, limit=1)
    if customers.data:
        return {"customer_id": customers.data[0].id}
    return {"customer_id": None}


def create_invoice(customer_id: str, description: str, amount_cents: int) -> dict:
    """Create a one-off invoice for an enterprise customer (sent, not auto-charged).

    ``auto_advance=False`` keeps the invoice in draft until ``send_invoice`` is
    called, so a human can review it before the customer sees it.
    """
    s = _stripe()
    item = s.InvoiceItem.create(
        customer=customer_id,
        amount=amount_cents,
        currency="usd",
        description=description,
    )
    invoice = s.Invoice.create(
        customer=customer_id,
        collection_method="send_invoice",
        days_until_due=30,
        auto_advance=False,
    )
    return {
        "invoice_id": invoice.id,
        "status": invoice.status,
        "invoice_item_id": item.id,
    }


def send_invoice(invoice_id: str) -> dict:
    """Finalise a draft invoice and email the hosted payment link."""
    s = _stripe()
    invoice = s.Invoice.send_invoice(invoice_id)
    return {
        "invoice_id": invoice.id,
        "status": invoice.status,
        "hosted_url": getattr(invoice, "hosted_invoice_url", None),
    }


def record_usage(customer_id: str, quantity: int = 1) -> dict:
    """Record usage. NOTE: ``customer_id`` must be a Stripe customer id (cus_...).

    stripe>=16 removed ``SubscriptionItem.create_usage_record``; usage is now
    reported via ``billing.MeterEvent`` (see STRIPE_METER_EVENT env, default
    ``vishap_analysis``).
    """
    s = _stripe()
    record = s.billing.MeterEvent.create(
        event_name=os.getenv("STRIPE_METER_EVENT", "vishap_analysis"),
        payload={
            "stripe_customer_id": customer_id,
            "value": str(quantity),
        },
        timestamp=int(time.time()),
    )
    return {"usage_record_id": record.identifier}
