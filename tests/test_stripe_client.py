# -*- coding: utf-8 -*-
"""Tests for the Stripe billing client (v6.1)."""
from unittest.mock import MagicMock, patch

import pytest

from src.billing import stripe_client


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("STRIPE_PRICE_ID", "price_123")


def test_create_checkout_session():
    session = MagicMock()
    session.id = "cs_test_1"
    session.url = "https://checkout.stripe.com/cs_test_1"
    with patch("stripe.checkout.Session.create", return_value=session) as create:
        result = stripe_client.create_checkout_session(
            "a@b.c", "https://ok", "https://cancel"
        )
    assert result == {
        "session_id": "cs_test_1",
        "url": "https://checkout.stripe.com/cs_test_1",
    }
    create.assert_called_once()


def test_get_customer():
    cust = MagicMock()
    cust.id = "cus_123"
    listing = MagicMock()
    listing.data = [cust]
    with patch("stripe.Customer.list", return_value=listing):
        result = stripe_client.get_customer("a@b.c")
    assert result == {"customer_id": "cus_123"}


def test_record_usage():
    rec = MagicMock()
    rec.identifier = "mbur_123"
    with patch("stripe.billing.MeterEvent.create", return_value=rec) as create:
        result = stripe_client.record_usage("cus_123", quantity=2)
    assert result == {"usage_record_id": "mbur_123"}
    _, kwargs = create.call_args
    assert kwargs["payload"]["value"] == "2"
    assert isinstance(kwargs["timestamp"], int)
    assert kwargs["timestamp"] is not None
