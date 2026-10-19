# Going live with Stripe

Checklist for switching Vishap from Stripe test mode to live payments. Do it
once, in order — every step below has burned someone before.

## 1. Business details

**Stripe Dashboard → Settings → Business settings.**

- Legal entity name, address, tax ID.
- Statement descriptor (what appears on the customer's card statement) —
  something recognisable, max 22 characters, e.g. `VISHAP`.
- Support email and phone: Stripe's review team may call.
- **Public details → Terms of Service and Privacy Policy URLs.** Stripe will not
  approve live payments without both, and they must return 200 without a login.

## 2. Identity verification

**Settings → Business settings → Verification.**

You need: a government ID for the account owner, proof of address (bank
statement or utility bill, less than 6 months old), and sometimes a company
registration document. Review usually takes minutes to 2 days; a mismatch between
the ID name and the account name is the most common rejection.

## 3. Products and prices — recreate them in live mode

**Test-mode price ids do not exist in live mode.** The most common "checkout
works in test, 500 in production" cause.

```bash
# with STRIPE_SECRET_KEY set to sk_live_... in the environment
python -m src.billing.stripe_setup
# prints: STRIPE_PRICE_ID=price_...
```

Put that id into `.env` as `STRIPE_PRICE_ID`, then restart the API. Verify:

```bash
curl -sS https://api.example.com/billing/products
# [{"id": "price_...", "name": "Vishap Pro", "amount": 2900, "currency": "usd"}]
```

## 4. Webhook

**Developers → Webhooks → Add endpoint** (or edit the test one).

| Field | Value |
| --- | --- |
| URL | `https://api.example.com/webhook/stripe` |
| Events | `customer.subscription.updated`, `invoice.paid`, `invoice.payment_failed` |

Copy the **live** signing secret (`whsec_...`) into `.env` as
`STRIPE_WEBHOOK_SECRET` and restart:

```bash
systemctl restart vishap
```

Test it from the dashboard: **Send test webhook** → expect `200`. A `400` means
the secret is wrong; a `500` means the secret is missing entirely.

See [WEBHOOK.md](WEBHOOK.md) for the full flow and the Stripe CLI path.

## 5. Keys

| Key | Where |
| --- | --- |
| `sk_live_...` | `.env` → `STRIPE_SECRET_KEY` |
| `pk_live_...` | only used by a hosted checkout page, not by this API |
| `whsec_...` | `.env` → `STRIPE_WEBHOOK_SECRET` |

Never commit them. `.env` is gitignored; the deployment copies it to `/opt/vishap/.env`.

Keep the test keys in a comment or a password manager — you will want test mode
again.

## 6. Test a real payment

**Test cards do not work in live mode** (`4242 4242 4242 4242` will be declined).

The cheapest safe verification: create a one-off invoice for a small amount and
pay it with your own card, then refund it from the dashboard.

```bash
# 1. create the invoice (Clarks auth required)
curl -sS -X POST https://api.example.com/billing/invoice \
  -H "Authorization: Bearer <clerk-jwt>" -H 'Content-Type: application/json' \
  -d '{"customer_id": "cus_live_...", "description": "Live smoke test", "amount_cents": 100}'

# 2. send it, then pay the hosted link from the response
```

What to check afterwards:

- Payment appears in **Dashboard → Payments** with status `Succeeded`.
- **Webhook deliveries** show a `200` for `invoice.paid`.
- The customer receives the Stripe receipt (if receipts are enabled).
- Refund the charge, and confirm the refund does not break anything — Vishap does
  not react to `charge.refunded`, so no action is needed.

## 7. Go-live checklist

- [ ] Business details complete, statement descriptor set
- [ ] Terms and Privacy URLs return 200 from a private window
- [ ] Verification approved (dashboard shows "Payments enabled")
- [ ] Live product + price created, `STRIPE_PRICE_ID` updated
- [ ] Live webhook endpoint created, `STRIPE_WEBHOOK_SECRET` updated
- [ ] `sk_live_...` in `.env`, container restarted
- [ ] One real payment made, refunded, webhook verified
- [ ] Customer portal enabled (so customers can cancel → `customer.subscription.updated`)
- [ ] Payout account connected, otherwise money sits in the Stripe balance

## Common failures

| Symptom | Cause |
| --- | --- |
| Checkout 500 with a price error | `STRIPE_PRICE_ID` still from test mode |
| Webhook `400 Invalid signature` | `whsec_` belongs to a different endpoint |
| Payment succeeds, tenant never activates | `tenants` row has no `stripe_customer_id`, or the webhook never arrived |
| "Your account cannot currently make live charges" | verification incomplete |
| Card declined on a test card | test cards do not exist in live mode |
