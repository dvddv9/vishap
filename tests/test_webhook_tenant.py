# -*- coding: utf-8 -*-
"""Tenant activation from Stripe subscription events (v6.4).

Stripe is mocked in every test — nothing here touches the network or a database.
"""
from unittest.mock import AsyncMock, patch

import pytest

from src.billing import webhook


def _event(status: str, customer: str = "cus_1", sub_id: str = "sub_1") -> dict:
    return {
        "type": "customer.subscription.updated",
        "data": {"object": {"id": sub_id, "customer": customer, "status": status}},
    }


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")


@pytest.mark.asyncio
async def test_subscription_active_activates_tenant():
    with patch("stripe.Webhook.construct_event", return_value=_event("active")), \
         patch.object(webhook, "activate_tenant", AsyncMock(
             return_value={"ok": True, "customer_id": "cus_1", "status": "active"}
         )) as activate, \
         patch.object(webhook, "deactivate_tenant", AsyncMock()) as deactivate:
        result = await webhook.handle_stripe_webhook_async(b"body", "sig")

    activate.assert_awaited_once_with("cus_1")
    deactivate.assert_not_called()
    assert result["status"] == "active"
    assert result["customer_id"] == "cus_1"
    assert result["tenant"]["status"] == "active"


@pytest.mark.asyncio
async def test_subscription_canceled_deactivates_tenant():
    with patch("stripe.Webhook.construct_event", return_value=_event("canceled")), \
         patch.object(webhook, "activate_tenant", AsyncMock()) as activate, \
         patch.object(webhook, "deactivate_tenant", AsyncMock(
             return_value={"ok": True, "customer_id": "cus_1", "status": "canceled"}
         )) as deactivate:
        result = await webhook.handle_stripe_webhook_async(b"body", "sig")

    deactivate.assert_awaited_once_with("cus_1")
    activate.assert_not_called()
    assert result["status"] == "canceled"
    assert result["tenant"]["status"] == "canceled"


@pytest.mark.asyncio
async def test_past_due_keeps_tenant_state():
    """A late payment must not lock a customer out mid-period."""
    with patch("stripe.Webhook.construct_event", return_value=_event("past_due")), \
         patch.object(webhook, "activate_tenant", AsyncMock()) as activate, \
         patch.object(webhook, "deactivate_tenant", AsyncMock()) as deactivate:
        result = await webhook.handle_stripe_webhook_async(b"body", "sig")

    activate.assert_not_called()
    deactivate.assert_not_called()
    assert result["status"] == "past_due"
    assert "tenant" not in result
