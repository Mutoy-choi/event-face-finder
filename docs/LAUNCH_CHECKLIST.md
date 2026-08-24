# PhotoMatch Studio launch checklist

This checklist defines the minimum gate for charging organizers for consent-based event photo matching. Do not enable a public production signup until every P0 item is complete.

## P0 — production safety

- [ ] Generate unique production values for `SECRET_KEY` and `EMBEDDING_ENCRYPTION_KEY`; store them only in the deployment secret manager.
- [ ] Run PostgreSQL in production and verify migrations, connection limits, backups, and point-in-time recovery.
- [ ] Configure a private S3-compatible bucket with public access blocked, lifecycle rules enabled, and signed URL expiry tested.
- [ ] Terminate TLS at the production domain and verify secure cookies, HSTS, CSP, CSRF protection, and trusted proxy settings.
- [ ] Run `photomatch download-models` and `photomatch doctor`; record the model filenames and checksum results used in production.
- [ ] Confirm that query selfies are never persisted to the application database, object storage, logs, traces, error reports, or analytics.
- [ ] Verify that every vector lookup is constrained by `event_id` and that tests fail when cross-event results are introduced.
- [ ] Exercise participant deletion, organizer deletion, event expiry, media deletion, and encrypted embedding deletion end to end.
- [ ] Configure upload, login, event-code, search, media, and abuse-report rate limits against the production proxy topology.
- [ ] Remove debug mode, sample accounts, development databases, test Stripe keys, and placeholder domains.

## P0 — face matching quality

- [ ] Build a consented validation set representative of the intended Korean event conditions: group photos, stage lighting, masks, glasses, pose, blur, age variation, and camera distance.
- [ ] Measure genuine and impostor score distributions separately for each major condition.
- [ ] Select the production threshold from a documented false-match target rather than copying the default development threshold.
- [ ] Report precision, recall, false-match rate, false-non-match rate, failure-to-enrol rate, and no-face/multi-face rejection rate.
- [ ] Add a low-confidence band that returns no result instead of forcing a match.
- [ ] Keep the product wording at “similar candidates”; never state that a result proves identity.
- [ ] Add a human-visible reporting path for an incorrect result and measure correction turnaround time.

## P0 — consent and privacy

- [ ] Obtain legal review for the intended jurisdictions, biometric processing, processor relationships, retention, deletion, children, and international transfers.
- [ ] Publish organizer terms, participant privacy notice, consent language, retention period, subprocessors, contact channel, and deletion procedure.
- [ ] Require organizers to confirm that they have the right to upload every event gallery.
- [ ] Show the event scope, organizer name, retention deadline, and search purpose before accepting a participant selfie.
- [ ] Prevent indexing of private event and media pages and prohibit public-web crawling, social-profile identification, and cross-event person tracking.
- [ ] Verify that backups and replicas follow the same deletion schedule as the primary stores.
- [ ] Document incident response and notification responsibilities before processing real participant photos.

## P0 — Stripe and accounting

- [ ] Create separate test and live Stripe products and prices for Event Pack, Studio subscription, and search-credit top-up.
- [ ] Register the production webhook endpoint and verify its signature using the raw request body.
- [ ] Replay duplicate and out-of-order webhook events and confirm idempotent credit accounting.
- [ ] Test successful payment, delayed payment, failed payment, refund, dispute, renewal, cancellation, and customer-portal flows.
- [ ] Reconcile Stripe sessions, invoices, internal credit grants, refunds, and consumption in an operator report.
- [ ] Confirm tax, invoicing, refund, and consumer-disclosure requirements with an accountant or counsel before live sales.

## P1 — operations

- [ ] Add structured logs with automatic redaction for cookies, event codes, signed URLs, email addresses, Stripe secrets, and uploaded-image metadata.
- [ ] Monitor error rate, search latency, queue depth, storage growth, model failures, false-result reports, deletion failures, and payment-webhook lag.
- [ ] Run image ingestion and embedding as retry-safe background jobs with idempotency keys and dead-letter handling.
- [ ] Load-test concurrent uploads and searches using synthetic or consented data; do not use scraped faces.
- [ ] Add database and object-store restore drills and record recovery time and recovery point results.
- [ ] Prepare an operator runbook for model outage, storage outage, leaked event link, abusive organizer, incorrect match, and deletion request.

## Paid-pilot gate

Start with five small organizer-led events before broad self-service launch. Record:

- organizer activation and first-gallery completion,
- participant search completion,
- median and p95 search latency,
- useful-result rate and incorrect-result report rate,
- storage and inference cost per event,
- support time per event,
- Event Pack conversion and repeat-event intent.

A paid pilot is ready only when the P0 checklist is complete, the selected threshold meets the documented false-match target, deletion is proven end to end, Stripe reconciliation balances, and an operator can handle an incident using the runbook.
