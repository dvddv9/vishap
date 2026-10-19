# -*- coding: utf-8 -*-
"""Tests for the Stripe webhook handler (v6.1)."""
from unittest.mock import patch

import pytest

from src.billing import webhook


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_123")


def test_webhook_signature_valid():
    event = {"type": "invoice.paid", "data": {"object": {"id": "in_1"}}}
    with patch("stripe.Webhook.construct_event", return_value=event) as ce:
        result = webhook.handle_stripe_webhook(b"body", "sig")
    ce.assert_called_once_with(b"body", "sig", "whsec_123")
    assert result["ok"] is True


def test_webhook_ignored_event():
    event = {"type": "customer.created", "data": {"object": {"id": "cus_1"}}}
    with patch("stripe.Webhook.construct_event", return_value=event):
        result = webhook.handle_stripe_webhook(b"body", "sig")
    assert result == {"ok": True, "ignored": "customer.created"}


def test_webhook_subscription_updated():
    event = {
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_42"}},
    }
    with patch("stripe.Webhook.construct_event", return_value=event):
        result = webhook.handle_stripe_webhook(b"body", "sig")
    assert result == {
        "ok": True,
        "event": "customer.subscription.updated",
        "subscription_id": "sub_42",
    }
