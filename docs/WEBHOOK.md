# Stripe webhook setup

The webhook is how a payment turns into access. Without it Stripe takes the
money and Vishap keeps the tenant on the free plan — nothing on the Vishap side
notices the subscription change.

Endpoint: `POST /webhook/stripe`. It is intentionally **not** behind
`X-API-Key`: Stripe cannot send one. Authentication is the signature in the
`Stripe-Signature` header, verified against `STRIPE_WEBHOOK_SECRET`.

## 1. Create the endpoint

**Stripe Dashboard → Developers → Webhooks → Add endpoint.**

| Field | Value |
| --- | --- |
| Endpoint URL | `https://<your-domain>/webhook/stripe` |
| Description | Vishap production |
| Events | `customer.subscription.updated`, `invoice.paid`, `invoice.payment_failed` |

The URL must be public HTTPS. `http://localhost` will not work from Stripe's
servers; use the Stripe CLI for local testing (§5).

## 2. Copy the signing secret

After saving, the endpoint page shows a **Signing secret** starting with
`whsec_`. Click *Reveal* and copy it.

```bash
ssh root@<vps>
cd /opt/vishap
# add or replace the line
sed -i '/^STRIPE_WEBHOOK_SECRET=/d' .env
echo "STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxx" >> .env
systemctl restart vishap
```

Each endpoint has its own secret. Rotating it means updating `.env` — no
restart of the image, only the container.

## 3. What Vishap does with each event

| Event | Behaviour |
| --- | --- |
| `customer.subscription.updated` with `active` / `trialing` | `activate_tenant(customer_id)` |
| … with `canceled` / `unpaid` / `incomplete_expired` | `deactivate_tenant(customer_id)` |
| … with `past_due` | no change — a late payment should not lock a customer out mid-period |
| `invoice.paid` | recorded in the response (`invoice_id`, `customer_id`, `amount_paid`); accounting hook |
| anything else | acknowledged and ignored (`{"ok": true, "ignored": "<type>"}`) |

Successful responses are `200` with a JSON body. Failures:

| Status | Meaning |
| --- | --- |
| `400` | signature mismatch, or the body was altered in transit |
| `500` | `STRIPE_WEBHOOK_SECRET` is not set on the server |

> **Tenant activation is currently a stub.** `src/api/tenants.py` logs the
> transition and returns the intended state; it does not persist anything yet.
> The webhook is wired correctly, but a paid subscription does not yet change
> what `/analyze/secure` allows. That join (`stripe_customer_id` → Clerk
> `org_id`) is the next piece of work.

## 4. Verify a delivery

**Stripe Dashboard → Developers → Webhooks → your endpoint → Recent deliveries.**

A `200` with a body like `{"ok": true, "event": "customer.subscription.updated",
"subscription_id": "sub_...", "customer_id": "cus_...", "status": "active",
"tenant": {...}}` means signature verification and dispatch both worked.

Common failures:

| Response | Cause |
| --- | --- |
| `400 Invalid payload` | a proxy rewrote the body; forward it untouched |
| `400 Invalid signature` | wrong `whsec_` for this endpoint |
| `500 STRIPE_WEBHOOK_SECRET not set` | variable missing from `.env` |
| timeout | endpoint not reachable from the internet |

## 5. Test locally with the Stripe CLI

```bash
stripe login
stripe listen --forward-to http://localhost:5001/webhook/stripe
# the CLI prints a temporary whsec_... — put it in .env
```

Then trigger an event in another terminal:

```bash
stripe trigger customer.subscription.updated
```

The CLI shows the response code and body. Restart the API after changing
`STRIPE_WEBHOOK_SECRET` so the new value is picked up.

## 6. Also configure, outside the webhook

- **Stripe Dashboard → Settings → Public Details:** Terms of Service and Privacy
  Policy URLs. Stripe will not approve live payments without them.
- **Customer portal:** enable it so customers can cancel, which produces the
  `canceled` event this webhook reacts to.
