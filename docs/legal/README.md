<!-- DRAFT: This document is a technical template. Must be reviewed by a qualified lawyer before publication. -->

# Legal Documents

- [Terms of Service](./TERMS.md)
- [Privacy Policy](./PRIVACY.md)
- [Data Processing Agreement (DPA)](./DPA.md)
- [Service Level Agreement (SLA)](./SLA.md)

⚠️ **These are technical templates.** Must be reviewed by a lawyer before publication.

## What is here

| File | Purpose |
| --- | --- |
| [`TERMS.md`](./TERMS.md) | Terms of Service — 11 sections, required by Stripe before payments can be approved. |
| [`PRIVACY.md`](./PRIVACY.md) | Privacy Policy — 8 sections, GDPR-oriented, documents sub-processors and retention. |
| [`DPA.md`](./DPA.md) | Data Processing Agreement — 10 sections, GDPR Article 28 processor terms, sub-processor table, SCCs, audit rights. Required by most enterprise buyers. |
| [`SLA.md`](./SLA.md) | Service Level Agreement — 8 sections: 99.9% monthly uptime, P1–P4 support response times, service credits. |

## How to use these templates

1. **Replace the placeholders.** Search for `[` in every file:

   | Placeholder | Replace with |
   | --- | --- |
   | `[Effective Date]` | Date the documents go live |
   | `[Company Legal Name]` | Registered legal entity name |
   | `[Customer Legal Name]` | Counterparty name (DPA, SLA) |
   | `[Your Country]` | Jurisdiction governing the Terms |
   | `[Company Postal Address]` | Registered address |
   | `[Representative Name and Address]` | EU/UK representative, if required |
   | `support@vishap.dev` | Real support address |
   | `privacy@vishap.dev` | Real privacy/DPO address |
   | `billing@vishap.dev` | Real billing address (SLA credits) |

2. **Verify the factual claims.** Sections that describe the implementation — Fernet
   encryption, HMAC webhook verification, JWT sessions, PII redaction, row-level
   security, audit-trail hashes, observability stack, retention windows, the
   `GET /health` probe — must match what actually ships. Re-read them after any
   change to the pipeline or infrastructure.

3. **Get legal review.** These are engineering drafts, not legal advice. A qualified
   lawyer in your jurisdiction must review them before publication.

4. **Publish.** Copy all four files into `docs-site/docs/legal/` as `terms.md`,
   `privacy.md`, `dpa.md` and `sla.md` (the Docusaurus mirrors), register them in
   `docs-site/sidebars.ts` under the `Legal` category, and link them from the
   landing page footer.

5. **Register with Stripe.** In the Stripe Dashboard go to
   **Settings → Public Details** and add the public URLs of the documents you
   publish. Stripe will not approve live payments without Terms of Service and a
   Privacy Policy; DPA and SLA are what enterprise procurement asks for.

## Known gaps (TODO before launch)

- `GET /api/me/data` and `DELETE /api/me/delete` — self-service export/deletion
  endpoints referenced by the Privacy Policy and the DPA are **not implemented yet**.
- Governing law and jurisdiction are placeholders — must be chosen deliberately.
- No EU/UK representative has been appointed, although the DPA refers to SCCs.
- The DPA describes sub-processor locations (US/CN/EU) that must be confirmed
  against where the deployment actually sends data.
- The 90-day material retention window and the 14-day trace retention are policy
  statements; confirm the storage layer actually enforces them.
- The SLA promises 99.9% uptime and a shared Grafana dashboard — neither is
  measured or provisioned automatically today. The 2-hour monthly maintenance
  window is also large relative to the 43-minute monthly error budget (it is
  excluded, but a lawyer may ask why it is that long).
- DPA and SLA are not linked from the landing page footer — only Terms and Privacy
  are.

## Mirrors

`docs/legal/` is the editable source. `docs-site/docs/legal/` holds the copies that
Docusaurus renders at `/docs/legal/terms`, `/docs/legal/privacy`,
`/docs/legal/dpa` and `/docs/legal/sla`. They differ only in relative link targets
(`./PRIVACY.md` vs `./privacy`), so **edit both** — or delete the mirror and
generate it if the duplication becomes a burden.
