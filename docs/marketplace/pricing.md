# Marketplace pricing

Three plans. Limits are per account and reset on the first day of the month.

| Plan | Price | Limits |
| --- | --- | --- |
| **Free** | $0 | 10 analyses/month, Python only |
| **Pro** | $29/mo | 500 analyses, all languages, GitHub App |
| **Enterprise** | Contact | Unlimited, SSO, SLA, dedicated support |

## What each plan includes

| | Free | Pro | Enterprise |
| --- | --- | --- | --- |
| Analyses / month | 10 | 500 | Unlimited |
| Languages | Python only | All supported | All supported |
| GitHub App (PR comments) | — | ✓ | ✓ |
| SARIF / SBOM export | ✓ | ✓ | ✓ |
| CLI + API access | ✓ | ✓ | ✓ |
| Audit-trail export (CSV/JSON) | — | ✓ | ✓ |
| Multi-tenant isolation (RLS) | ✓ | ✓ | ✓ |
| SSO (SAML) | — | — | ✓ |
| DPA + SLA with service credits | — | — | ✓ |
| Support | Community | Email, 2 business days | Dedicated, P1 in 1 hour |

## Notes

- **Overage.** Pro is soft-capped: analyses beyond 500 are rejected with `429`
  rather than billed, until you upgrade. No surprise invoices.
- **Billing.** Subscriptions are handled by Stripe. Enterprise invoices are
  issued as Stripe invoices with 30-day payment terms.
- **Annual.** Pro is available annually at $290/year (two months free). Contact
  `billing@vishap.dev` to switch.
- **Trials.** 14 days of Pro on signup, no card required.
- **Refunds.** Prorated refunds on annual plans within 30 days, pro rata for the
  unused period; monthly plans are not refunded mid-period.
- **Non-profit / education.** 50% off Pro on request.

Prices are in USD and exclude VAT/sales tax where applicable.
