# -*- coding: utf-8 -*-
"""Stripe webhook handler (v6.1, tenant activation since v6.4)."""
import os

import stripe
from fastapi import HTTPException

from src.api.tenants import activate_tenant, deactivate_tenant

#: Subscription statuses that grant access.
ACTIVE_STATUSES = frozenset({"active", "trialing"})

#: Statuses that revoke access.
CANCELED_STATUSES = frozenset({"canceled", "unpaid", "incomplete_expired"})


def _verify_event(payload: bytes, sig_header: str) -> dict:
    """Verify the signature and return the event."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET not set")

    try:
        return stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")


def _dispatch(event: dict) -> tuple[dict, str | None]:
    """Map an event to (response payload, tenant action).

    Tenant fields are added only when present in the event, so the response to a
    minimal event stays minimal.
    """
    etype = event["type"]

    if etype == "customer.subscription.updated":
        sub = event["data"]["object"]
        response: dict = {"ok": True, "event": etype, "subscription_id": sub["id"]}
        if sub.get("customer"):
            response["customer_id"] = sub["customer"]
        if sub.get("status"):
            response["status"] = sub["status"]

        status = sub.get("status")
        action = None
        if status in ACTIVE_STATUSES:
            action = "activate"
        elif status in CANCELED_STATUSES:
            action = "deactivate"
        # past_due / incomplete keep the current state: a late payment should not
        # lock a customer out mid-period, only a real cancellation should.
        return response, action

    if etype == "invoice.paid":
        invoice = event["data"]["object"]
        return {
            "ok": True,
            "event": etype,
            "invoice_id": invoice.get("id"),
            "customer_id": invoice.get("customer"),
            "amount_paid": invoice.get("amount_paid"),
        }, None

    return {"ok": True, "ignored": etype}, None


def handle_stripe_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify and parse an event **without** tenant side effects.

    Kept for synchronous callers and tests. The HTTP endpoint uses
    :func:`handle_stripe_webhook_async`, which also activates the tenant.
    """
    event = _verify_event(payload, sig_header)
    response, _action = _dispatch(event)
    return response


async def handle_stripe_webhook_async(payload: bytes, sig_header: str) -> dict:
    """Verify an event and apply its tenant side effects.

    This is the entry point the API uses: activation happens in the same request
    as verification, so a subscription change is never acknowledged without being
    applied.
    """
    event = _verify_event(payload, sig_header)
    response, action = _dispatch(event)

    if action == "activate":
        response["tenant"] = await activate_tenant(response["customer_id"])
    elif action == "deactivate":
        response["tenant"] = await deactivate_tenant(response["customer_id"])

    return response
