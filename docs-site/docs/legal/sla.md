{/* DRAFT: This document is a technical template. Must be reviewed by a qualified lawyer before publication. */}

# Service Level Agreement

**Effective date:** October 18, 2026
**Provider:** dvddv9 (Individual Entrepreneur) ("Vishap")
**Customer:** [Customer Legal Name]
**Contact:** dvddvd9h@outlook.com

This Service Level Agreement ("SLA") describes the availability commitment, support
response times and service credits applicable to the Vishap hosted service. It
supplements the Terms of Service; where this SLA and the Terms conflict on service
levels, this SLA prevails.

## 1. Service Commitment

1.1. Vishap targets **99.9% monthly uptime** for the analysis API and the web
application, measured per calendar month.

1.2. **Monthly uptime** is calculated as:

```
uptime % = (total minutes in month - excluded minutes - unavailable minutes)
           / (total minutes in month - excluded minutes) x 100
```

1.3. **Unavailable** means a request to the health endpoint
(`GET /health`) fails, returns a 5xx response, or exceeds a 30-second response
time, for two or more consecutive probe intervals from at least two independent
monitoring locations.

1.4. **Measurement.** Availability is measured by the Prometheus metrics and
Grafana recording rules operated by Vishap (`vishap_http_requests_total` and the
synthetic health probe). Measurement data is retained for 30 days and is the
authoritative record for credit calculations.

1.5. 99.9% monthly uptime corresponds to approximately **43 minutes** of permitted
unavailability in a 30-day month, excluding the events in Section 2.

## 2. Exclusions

The following do not count as unavailability and are excluded from the uptime
calculation:

2.1. **Scheduled maintenance.** Announced at least 48 hours in advance, within the
window described in Section 6.

2.2. **Emergency maintenance.** Security patches or fixes required to prevent
imminent harm, announced as soon as practicable; Vishap uses reasonable efforts to
keep such windows under 60 minutes per month.

2.3. **Force majeure.** Events beyond reasonable control, including natural
disasters, war, civil unrest, widespread internet or power failures, and
government action.

2.4. **Customer-side causes.** Invalid payloads exceeding documented limits,
revoked or expired API keys and JWTs, exceeding rate limits, customer network or
DNS problems, or customer infrastructure.

2.5. **Third-party dependencies.** Outages of Clerk, Stripe or GitHub, or of the
local DSH harness where the failure originates outside Vishap and there is no
reasonable workaround.

2.6. **Beta and preview features.** Features explicitly labelled beta or preview
are provided without an availability commitment.

2.7. **Suspension for cause.** Service suspension under the Terms of Service for
non-payment or breach of acceptable use.

## 3. Support Response Times

3.1. Support is available by email at dvddvd9h@outlook.com, **Monday to Friday,
09:00–18:00** in the Provider's local time zone, excluding public holidays.

3.2. **Response time** means the time from ticket receipt to a substantive human
response — not to resolution.

| Severity | Description | Response Time |
| --- | --- | --- |
| P1 (Critical) | Service unavailable, or a security incident | 1 hour |
| P2 (High) | Major feature broken, no workaround; analyses fail for all users | 4 hours |
| P3 (Medium) | Feature degraded, workaround available; isolated job failures | 1 business day |
| P4 (Low) | Cosmetic issues, questions, documentation requests | 3 business days |

3.3. P1 issues may be reported outside business hours and are triaged on call, but
response within 1 hour applies only during business hours as defined in 3.1
unless the Customer has a written 24x7 support agreement.

3.4. The Customer must provide a reproducible description, affected job or session
identifiers, and timestamps. Vishap may reclassify severity in mutual agreement
with the Customer.

## 4. Service Credits

4.1. If monthly uptime falls below 99.9%, the Customer is entitled to a credit
against the monthly fee for the affected month:

| Monthly uptime | Service credit |
| --- | --- |
| 99.0% – 99.9% | 10% of the monthly fee |
| 95.0% – 99.0% | 25% of the monthly fee |
| Below 95.0% | 50% of the monthly fee |

4.2. **Calculation basis.** Credits are calculated on the recurring monthly fee
actually paid for the affected month, excluding usage-based charges, taxes and
third-party pass-through costs.

4.3. **Cap.** Total credits for any single month will not exceed **30%** of that
month's recurring fee.

4.4. **Claim procedure.** The Customer must request a credit within **30 days**
after the end of the affected month, providing the observed outage window and any
supporting evidence. Vishap verifies the claim against its monitoring data and
issues credits within 30 days.

4.5. **Sole remedy.** Service credits are the Customer's sole and exclusive remedy
for failure to meet the availability commitment, except where law provides
otherwise.

4.6. Credits are applied to future invoices and are not paid out in cash. Credits
are not granted for accounts suspended for cause.

## 5. Monitoring and Reporting

5.1. **Shared dashboard.** Enterprise customers receive access to a read-only
Grafana dashboard showing availability, request rate, error rate, job throughput
and pipeline duration.

5.2. **Monthly report.** On request, Vishap provides a monthly availability report
containing uptime percentage, excluded windows, and a list of incidents with
durations and root-cause summaries.

5.3. **Status page.** Planned maintenance and incidents are announced on the
public status page.

5.4. **Data minimisation.** Dashboards and reports expose aggregate operational
metrics only; they never contain other customers' data or analysed material.

## 6. Maintenance Windows

6.1. **Standard window.** The first Sunday of each calendar month,
**02:00–04:00 UTC**.

6.2. **Notice.** Scheduled maintenance is announced at least **48 hours** in
advance by email and on the status page, with the expected duration and impact.

6.3. **Overrun.** If maintenance overruns its announced window, the excess time
counts as unavailability and is not excluded, unless caused by an event in
Section 2.

6.4. **Emergency work.** Security patches may be applied outside the standard
window to address an actively exploited vulnerability; notice is given as soon as
practicable.

## 7. Term and Termination

7.1. This SLA applies for the term of the Customer's subscription.

7.2. Either party may terminate the SLA or the underlying subscription with
**30 days'** written notice, effective at the end of the then-current billing
period.

7.3. Vishap may terminate this SLA immediately if the Customer breaches the
acceptable use provisions of the Terms of Service.

7.4. **Effect of termination.** Credits accrued before termination are applied to
the final invoice. Sections 4.5 (sole remedy), 8 (contact) and any provisions that
by their nature survive, continue to apply.

7.5. Vishap may revise this SLA with 30 days' notice; changes apply from the next
renewal period. Continued use constitutes acceptance.

## 8. Contact

- **Support and P1 escalation:** dvddvd9h@outlook.com
- **Security incidents:** see SECURITY.md in the project repository
- **Billing and credits:** billing@vishap.dev
- **Postal address:** Remote — Yerevan, Armenia
