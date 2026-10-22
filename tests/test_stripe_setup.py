# -*- coding: utf-8 -*-
"""Stripe plan setup tests (v6.4) — Stripe is mocked, nothing hits the network."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.billing import stripe_setup
from src.billing.stripe_client import BillingError


def _fake_stripe() -> MagicMock:
    s = MagicMock()
    s.Product.create.return_value = MagicMock(id="prod_test")
    s.Price.create.return_value = MagicMock(id="price_test")
    return s


def test_create_pro_plan():
    fake = _fake_stripe()
    with patch.object(stripe_setup, "_stripe", return_value=fake):
        plan = stripe_setup.create_pro_plan()

    assert plan["product_id"] == "prod_test"
    assert plan["price_id"] == "price_test"
    assert plan["amount"] == 2900

    product_kwargs = fake.Product.create.call_args.kwargs
    assert product_kwargs["name"] == stripe_setup.PRO_PRODUCT_NAME

    price_kwargs = fake.Price.create.call_args.kwargs
    assert price_kwargs["unit_amount"] == 2900
    assert price_kwargs["currency"] == "usd"
    assert price_kwargs["recurring"] == {"interval": "month"}


def test_list_prices_returns_empty_without_stripe():
    """No STRIPE_SECRET_KEY means an empty pricing list, never a 500."""
    with patch.object(stripe_setup, "_stripe", side_effect=BillingError("STRIPE_SECRET_KEY not set")):
        assert stripe_setup.list_prices() == []


def test_products_endpoint():
    from src.main import app

    payload = [{"id": "price_1", "name": "Vishap Pro", "amount": 2900, "currency": "usd"}]
    with patch("src.main.list_prices", return_value=payload):
        response = TestClient(app).get("/billing/products")

    assert response.status_code == 200
    assert response.json() == payload
