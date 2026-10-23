# -*- coding: utf-8 -*-
"""Enterprise invoice tests (v6.3) — Stripe is always mocked."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.billing import stripe_client
from src.billing.webhook import handle_stripe_webhook


def _fake_stripe(invoice_id="in_test", status="draft", hosted_url="https://pay.test/in_test"):
    s = MagicMock()
    s.InvoiceItem.create.return_value = MagicMock(id="ii_test")
    s.Invoice.create.return_value = MagicMock(id=invoice_id, status=status)
    s.Invoice.send_invoice.return_value = MagicMock(
        id=invoice_id, status="open", hosted_invoice_url=hosted_url
    )
    return s


def test_create_invoice():
    fake = _fake_stripe()
    with patch.object(stripe_client, "_stripe", return_value=fake):
        result = stripe_client.create_invoice("cus_1", "Vishap Enterprise, October", 4900)

    assert result["invoice_id"] == "in_test"
    assert result["status"] == "draft"
    fake.InvoiceItem.create.assert_called_once()
    kwargs = fake.Invoice.create.call_args.kwargs
    assert kwargs["collection_method"] == "send_invoice"
    assert kwargs["days_until_due"] == 30
    assert kwargs["auto_advance"] is False


def test_send_invoice():
    fake = _fake_stripe()
    with patch.object(stripe_client, "_stripe", return_value=fake):
        result = stripe_client.send_invoice("in_test")

    assert result["hosted_url"] == "https://pay.test/in_test"
    fake.Invoice.send_invoice.assert_called_once_with("in_test")


def test_webhook_invoice_paid(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    event = {
        "type": "invoice.paid",
        "data": {"object": {"id": "in_test", "customer": "cus_1", "amount_paid": 4900}},
    }
    with patch("src.billing.webhook.stripe.Webhook.construct_event", return_value=event):
        result = handle_stripe_webhook(b"{}", "sig")

    assert result["ok"] is True
    assert result["customer_id"] == "cus_1"
    assert result["amount_paid"] == 4900


def test_invoice_requires_auth():
    from src.main import app

    client = TestClient(app)
    response = client.post(
        "/billing/invoice",
        json={"customer_id": "cus_1", "description": "x", "amount_cents": 100},
    )
    assert response.status_code == 401


def test_invoice_invalid_amount():
    from src.auth.middleware import current_user
    from src.main import app

    client = TestClient(app)
    app.dependency_overrides[current_user] = lambda: {"user_id": "u1", "tenant_id": "t1"}
    try:
        response = client.post(
            "/billing/invoice",
            json={"customer_id": "cus_1", "description": "x", "amount_cents": 0},
        )
    finally:
        app.dependency_overrides.pop(current_user, None)

    assert response.status_code == 400
