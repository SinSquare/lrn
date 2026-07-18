# Sample messages for `POST /process`

Paste each `message` value into the triage request body:

```json
{ "message": "..." }
```

Constraints: 10–2000 characters.

---

## 1. Student portal / MFA (high)

Good for severity calibration, multiple systems, and unknowns.

```
hey — since yesterday afternoon-ish our student portal login has been flaky. SSO works for staff but undergrads keep getting bounced back to the landing page after MFA. We thought it was just the new release but rollback didn’t help. Redis might be involved? saw elevated latency on cache nodes around 3pm CET. Support says ~40 tickets since this morning, mostly mobile Safari. Finance team says they can’t access invoices either but that might be unrelated. We hotfixed the session cookie path last night but no improvement. Can someone check if moodle sync is blocking auth? I’d call this pretty bad — registration opens Friday. Need a workaround for demo at 10am tomorrow and proper RCA.
```

---

## 2. Full production outage (critical)

Should not be scored as low/medium.

```
URGENT: checkout is completely down for all customers since 14:12 UTC. Payment API returns 503 on every request, status page is red for payments + order-service. Cart still loads but place-order hangs. Revenue impact is immediate — Black Friday weekend, roughly $18k/minute at current traffic. On-call page fired for payments, edge, and orders. Rollback of deploy payments-v2.4.1 is in progress but not confirmed yet. No workaround besides telling customers to wait. Need war room now.
```

---

## 3. Mild printer / office IT (low)

Should stay low; easy to over-escalate.

```
The 3rd-floor marketing printer (HP LaserJet near the kitchen) has been jamming on duplex jobs since this morning. Single-sided prints are fine. Only about 4 people complained. IT already ordered a new toner and roller kit which arrives Monday. No other systems affected.
```

---

## 4. Ambiguous / sparse report (medium, many unknowns)

Bad prompts invent systems and skip unknowns here.

```
Users are saying “the app is slow today.” Not sure which app. Started after lunch maybe? Some people on VPN, some not. A few said dashboards take forever. Nobody filed tickets with screenshots yet. Could be nothing.
```

---

## 5. Email delivery degradation (medium/high)

Severity depends on blast radius; unknowns should be captured.

```
Outbound email from our CRM started bouncing around 09:40. Marketing campaigns show ~35% soft bounces (421 deferrals from major providers). Transactional password-reset mail still seems fine according to two support agents. SPF/DKIM look unchanged from yesterday. We rotated the sending IP pool last night for warm-up. Customer success says demo invites aren’t arriving for prospects. Volume is elevated vs normal Tuesday morning but we don’t have exact numbers yet.
```

---

## 6. Internal tool only, limited blast radius (low/medium)

```
Our internal expense tool (Concur sync job) failed overnight. Finance can’t push last week’s reports to the ERP until it’s fixed. External customers are unaffected. The job log shows a timeout talking to SFTP at 02:14. Retrying manually failed twice. Not urgent for customers but payroll cutoff is Thursday.
```

---

## 7. Security-ish / account lockouts (high)

Tempting to invent root causes; keep hypotheses grounded.

```
Since ~08:00 we’ve had a spike in account lockouts for corporate SSO. Helpdesk reports ~120 lockouts in 2 hours vs usual ~10/day. Users report password prompts looping even with correct credentials. MFA push notifications arrive late or not at all for some. Identity provider status page shows no incident. We did enable a new conditional-access policy yesterday for “risky sign-ins.” Unclear if contractors on BYOD are hit harder. No confirmed breach, but security wants this treated seriously until ruled out.
```

---

## 8. Data pipeline / analytics (medium)

```
The nightly dbt run for the warehouse failed at the `fct_orders` model. Freshness SLAs for executive dashboards are breached — numbers are stuck on yesterday. Upstream Kafka lag on `orders.v1` looked normal at 01:00. Snowflake warehouse was resized last week. Only BI consumers are affected; product and checkout are fine. Data engineering is investigating; product analytics wants an ETA before the 11:00 leadership meeting.
```

---

## 9. Conflicting / noisy report (tests hallucination resistance)

```
Someone in Slack said the “entire cloud is down” but AWS status looks green. Another person said only staging API gateway in eu-west-1 is returning 502. A third person pasted an old screenshot from last month’s outage. I’m on mobile and can’t verify. Maybe related to the cert renewal ticket? Or not. Please triage whatever this is.
```

---

## 10. Mobile app crash after release (high)

```
iOS app 6.2.0 (released yesterday) is crashing on launch for users on iOS 16. Support volume: ~200 tickets in 6 hours, Crashlytics shows SIGABRT in `SessionManager.start()` affecting ~8% of sessions. Android is fine. We can pull the release from the App Store but review lag means a fix build won’t be live until tomorrow earliest. Paying subscribers can’t open the app to cancel or manage billing. Feature flag to skip the new session code exists but needs a config push from the backend team.
```

---

## 11. CDN / static assets (medium)

```
Product pages are loading without CSS/JS for a chunk of EU users since ~16:20 CET. HTML comes through fine but static assets from cdn.example.com return 403 intermittently. US traffic looks normal. We rotated CDN signing keys this afternoon as part of a security ticket. Support has ~25 screenshots of broken layout. Checkout still works if you know the URLs. Marketing site on the same CDN is also half-broken. Not a full outage but looks terrible and a partner demo is in 90 minutes.
```

---

## 12. Database connection pool exhaustion (high)

```
API p99 latency spiked from 180ms to 4.2s starting 11:03 UTC. Error rate ~12% with “remaining connection slots are reserved” from Postgres. Primary CPU is only at 40%. We shipped orders-api v3.1.0 an hour ago which added a new reporting query. Read replicas look healthy. Connection pool max is 100 and Grafana shows all checked out. Some customers report failed order submissions; others just see spinners. On-call is restarting pods as a stopgap but connections refill within minutes.
```

---

## 13. Single-user / local workstation (low)

```
My laptop can’t connect to the office Wi‑Fi on the 2nd floor only. 1st and 3rd floors work. IT already reset my password and it still fails with “incorrect password” even though VPN from home is fine. Nobody else on my team has this issue. Meeting in 20 minutes — can someone check if my MAC was blocked after the guest-network incident last week?
```

---

## 14. Kubernetes node pressure (high)

```
Several production deployments are stuck in Pending. Cluster autoscaler isn’t adding nodes; three nodes show MemoryPressure and kubelet is evicting pods including checkout-worker and notifications. Started after a batch job for year-end reports was scheduled into the prod pool by mistake (should have been batch-pool). HPA is thrashing. Customer-facing API is degraded — roughly 30% 502s at the ingress. We can cordon the noisy nodes but need capacity first. Blackout window for infra changes ends in 40 minutes.
```

---

## 15. Third-party IdP outage (critical)

```
Okta is partially down according to their status page (EU cell). Our workforce SSO and customer login that federates through Okta both fail with timeout after MFA. Started ~07:55 UTC. Internal tools (Jira, GitHub, Slack SSO) are affected so engineers can’t easily dig in. Customer support chat is overwhelmed — estimate 60% of logins failing. We have a break-glass local admin path for staff but not for end customers. No ETA from Okta yet. Treat as critical until IdP recovers or we cut over to backup IdP (untested in prod).
```

---

## 16. Search relevance / not an outage (low/medium)

```
Since the search ranking change on Tuesday, users complain that “obvious” products don’t show up on the first page. Conversion on search-driven sessions is down ~8% vs last week. No errors in logs; latency is fine. Merchandising says synonyms for winter SKUs look wrong. Only web search is affected — mobile app search uses the old ranker. Not down, but growth and category managers are escalating hard before the seasonal campaign Friday.
```

---

## 17. Disk full on logging hosts (medium)

```
Central logging (ELK) stopped receiving shipping from ~half of prod hosts after 02:30. Those hosts show disk 100% on /var/log because the logrotate cron was disabled during an audit last month and never re-enabled. App metrics still green; this is observability only — until someone needs logs for an incident. Security also can’t pull auth logs for the quarterly review due today. Need disk cleanup + restore shipping; apps themselves aren’t crashing.
```

---

## 18. Payment webhook backlog (high)

```
Stripe webhooks are queuing — delivery attempts succeed to our endpoint but our worker lag is at 45 minutes and growing. Customers are charged but order status stays “pending payment” so fulfillment doesn’t start. Started after we enabled a new `invoice.paid` handler that does a slow ERP sync inline. Dashboard shows ~14k pending events. Support is manually marking orders paid for VIP accounts. Finance is worried about reconciliation. Can we disable the new handler and drain the queue before evening peak?
```

---

## 19. DNS misconfiguration after migration (critical)

```
After cutting www to the new DNS provider at 18:00 UTC, roughly half the world resolves to the old IPs which we already decommissioned. Dig from US-East shows new records; dig from APAC still sees old ones with TTL 3600 we forgot to lower. Site is intermittently unreachable, email SPF might be wrong too — mail team hasn’t confirmed. Certificate on the new LB is valid. This is our main marketing + app domain. Need emergency TTL/provider fix and possibly bring old IPs back temporarily.
```

---

## 20. CI/CD blocked, no prod impact yet (low)

```
GitHub Actions runners for our org are failing with “no available runners” for private repos since this morning. Developers can’t merge or run tests. Production is unaffected. Self-hosted runner VMs show docker disk full. We can buy more GitHub-hosted minutes as a workaround. Release train for Thursday is at risk if this isn’t fixed by EOD Wednesday.
```

---

## 21. Chat / messaging degradation (medium/high)

```
In-app chat messages send but arrive 2–10 minutes late for users in US-West. EU seems fine. WebSockets reconnect loops in the browser console. Redis pub/sub CPU on the US cluster is pegged after a traffic spike from a livestream event. Push notifications still fast. Support tickets ~90 in an hour, mostly creators who can’t moderate live. Not fully down but unusable for real-time. Scaling the Redis cluster needs an approval we don’t have yet in the change window.
```

---

## 22. Backup / restore test failure (medium)

```
Quarterly DR restore drill failed: the latest RDS snapshot restored but application migrations won’t apply — schema dump is missing three tables added in November. Backups still “succeed” nightly according to the job, so we may have been blind for months. Production is healthy right now. Compliance deadline for evidence of successful restore is next Friday. Need a working restore path and to verify binlog/PITR options. Please don’t treat as a customer outage but severity for readiness is real.
```

---

## 23. Rate limiting false positive (medium)

```
A bunch of legitimate API customers started getting HTTP 429 from the public API around noon. WAF rules were tightened yesterday to block a scraper. Looks like the new rule keys on /v2/* without exempting partners on dedicated API keys. About 15 enterprise integrations broken including our biggest retail partner’s inventory sync. Internal traffic and the website are fine. Partner success is on a bridge call. Can we roll back the WAF rule or add allowlist entries ASAP?
```

---

## 24. Clock skew / certificate validity (high)

```
A subset of service-to-service calls fail with TLS handshake errors “certificate is not yet valid.” Affected pods were rescheduled onto a node pool where NTP is broken — system clock is ~6 hours behind. Started after we drained the old node group. Anything talking to those pods fails; traffic that lands on healthy nodes is fine. Roughly 20% of payments-auth calls error. Fixing chrony on the pool and bouncing pods should help but we need to confirm no data corruption from skewed timestamps in audit logs.
```

---

## 25. Feature flag gone wrong (high)

```
We flipped `new_checkout_flow` to 100% globally by accident during a 5% experiment bump (wrong environment dropdown in the flag UI). Error rate on checkout jumped to ~22% — the new flow still depends on a backend endpoint only partially rolled out. Reverting the flag is in progress but CDN-cached HTML might still reference the new bundle for some users. Revenue dip is visible in the realtime dashboard. Mobile native apps are unaffected. Need confirmation the flag is off everywhere and a purge of the edge cache for /checkout*.
```
