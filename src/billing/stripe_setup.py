# -*- coding: utf-8 -*-
"""Create the Stripe products and prices Vishap sells (v6.4).

**Run manually.** Nothing in this module executes on application startup:

    python -m src.billing.stripe_setup

It creates the "Vishap Pro" product with a $29/month recurring price and prints
the price id to put into ``.env`` as ``STRIPE_PRICE_ID``. Re-running it creates a
new price each time (Stripe prices are immutable by design); deactivate the old
one in the Dashboard afterwards.
"""

from dotenv import load_dotenv
load_dotenv()

from src.billing.stripe_client import _stripe

PRO_PRODUCT_NAME = "Vishap Pro"
PRO_PRODUCT_DESCRIPTION = "500 analyses per month, all languages, GitHub App"
PRO_AMOUNT_CENTS = 2900
PRO_CURRENCY = "usd"
PRO_INTERVAL = "month"


def create_pro_plan() -> dict:
    """Create the Pro product and its monthly price. Returns the ids."""
    stripe = _stripe()
    product = stripe.Product.create(
        name=PRO_PRODUCT_NAME,
        description=PRO_PRODUCT_DESCRIPTION,
    )
    price = stripe.Price.create(
        product=product.id,
        unit_amount=PRO_AMOUNT_CENTS,
        currency=PRO_CURRENCY,
        recurring={"interval": PRO_INTERVAL},
    )
    return {
        "product_id": product.id,
        "price_id": price.id,
        "amount": PRO_AMOUNT_CENTS,
        "currency": PRO_CURRENCY,
    }


def list_prices() -> list[dict]:
    """Return the active Stripe prices, or ``[]`` when Stripe is not configured.

    Used by ``GET /billing/products``: a pricing page should render an empty
    list rather than a 500 when the deployment has no Stripe keys yet.
    """
    try:
        stripe = _stripe()
        prices = stripe.Price.list(active=True, limit=20, expand=["data.product"])
    except Exception:
        return []

    result: list[dict] = []
    for price in getattr(prices, "data", None) or []:
        product = getattr(price, "product", None)
        name = getattr(product, "name", None) or PRO_PRODUCT_NAME
        result.append(
            {
                "id": price.id,
                "name": name,
                "amount": getattr(price, "unit_amount", None),
                "currency": getattr(price, "currency", None),
            }
        )
    return result


def main() -> int:
    """CLI entry point: create the plan and print the env line."""
    try:
        plan = create_pro_plan()
    except Exception as exc:  # BillingError when STRIPE_SECRET_KEY is unset
        print(f"Stripe setup failed: {exc}")
        print("Set STRIPE_SECRET_KEY in .env and try again.")
        return 1

    print(f"Created product {plan['product_id']}")
    print(f"Created price   {plan['price_id']}  ({PRO_AMOUNT_CENTS / 100:.2f} {PRO_CURRENCY}/{PRO_INTERVAL})")
    print()
    print("Add this to your .env:")
    print(f"STRIPE_PRICE_ID={plan['price_id']}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
