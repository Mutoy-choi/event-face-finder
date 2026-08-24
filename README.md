# PhotoMatch Studio

[한국어 문서](README.ko.md) · English

A production-oriented MVP for **consent-based event photo selfie search**. Organizers create a private event, upload photos they are authorized to process, and share an optional access code. A participant uploads one selfie; the server searches only that event and returns possible photo matches. The application does not persist the selfie to its database or object storage.

This is intentionally **not** an open-web reverse face search engine. It has no crawler, URL ingestion, name lookup, social-profile lookup, or cross-customer search.

## Product preview

![PhotoMatch Studio landing page](docs/screenshots/landing.png)

| Organizer dashboard | Participant selfie search |
|---|---|
| ![Organizer dashboard](docs/screenshots/dashboard.png) | ![Participant search](docs/screenshots/public-search.png) |

## What is included

- FastAPI + Jinja responsive web product
- Email/password accounts and Argon2id hashing
- Private events, access codes, configurable retention, immediate deletion
- JPEG/PNG/WebP validation, EXIF/GPS stripping, thumbnails
- OpenCV YuNet detection + SFace 128D embeddings
- AES-256-GCM encryption for biometric templates at rest
- Event-scoped cosine search with conservative configurable threshold
- One-face-only selfie queries with no application-level persistence
- Free credits, one-off event pack, monthly studio plan, Stripe Checkout/webhooks
- Local SQLite/media mode and PostgreSQL + S3-compatible production mode
- Abuse/removal reports, audit records, CSRF, rate limiting, security headers
- Pinned model downloader with SHA-256 verification
- Docker, Compose, GitHub Actions, tests, operator CLI

## Quick start

```bash
cp .env.example .env
uv sync --extra dev
uv run photomatch generate-secrets   # copy both values into .env
uv run photomatch download-models
uv run photomatch init-db
uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

Or run PostgreSQL + MinIO locally:

```bash
docker compose up --build
```

The MinIO console is exposed at `http://localhost:9001` for local development only.

## Model choices and licenses

The default engine uses the official OpenCV model repositories:

- YuNet detector: MIT-licensed model directory
- SFace recognizer: Apache-2.0-licensed model directory

`photomatch download-models` downloads fixed filenames and rejects unexpected checksums. See `THIRD_PARTY_NOTICES.md`.

The application uses a default cosine threshold of `0.45`, deliberately higher than a permissive verification threshold. This is still only a starting point: calibrate false-match and miss rates on a representative, consented validation set before selling the service.

## Stripe setup

Create three Stripe Prices and set:

```dotenv
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_EVENT_PACK=price_...
STRIPE_PRICE_STUDIO_MONTHLY=price_...
STRIPE_PRICE_SEARCH_TOPUP=price_...
```

Register `POST /billing/webhook` for at least:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `invoice.paid`
- `customer.subscription.deleted`

One-time products grant credits after a verified checkout event. Monthly credits are granted from paid invoices, using unique ledger references to prevent duplicate fulfillment.

## Operator commands

```bash
uv run photomatch doctor
uv run photomatch purge-expired --dry-run
uv run photomatch purge-expired
uv run photomatch generate-secrets
```

Schedule `purge-expired` at least hourly in production. A deletion failure must alert an operator rather than silently retaining data.

## Architecture

```text
Browser
  ├─ Organizer account → event → authorized photos
  └─ Participant → event code → one-face selfie
                         │
FastAPI/Jinja ── image validation and EXIF removal
                         │
                  YuNet detection
                         │
                  SFace 128D vector
                         │
             AES-GCM encrypted templates
                         │
         event_id-scoped cosine similarity
                         │
              signed private media links

PostgreSQL: metadata, encrypted templates, credits, audits
Private S3: normalized photos and thumbnails
Stripe: Checkout and verified webhooks
```

See `docs/ARCHITECTURE.md` for trust boundaries and scaling notes.

## Privacy and launch constraints

Face templates can be regulated biometric information. A commercial operator must determine the lawful basis, consent wording, required notices, processing agreements, overseas-transfer disclosures, deletion procedures, child-data rules, and incident obligations for each market. The included policy pages are implementation placeholders, not legal advice.

The product enforces several non-negotiable constraints:

- search only inside one organizer-controlled event;
- no public-web crawling or person/name lookup;
- no persistent query selfie or query embedding;
- results described as possible matches, never identity confirmation;
- no use for surveillance or consequential decisions;
- organizer attestation and participant notice;
- configurable expiration and immediate erasure controls.

Review `docs/PRIVACY_LAUNCH_CHECKLIST.md` and obtain qualified legal review before processing real users.

## Monetization

The recommended initial buyer is the **organizer or photographer**, not the attendee:

1. Free: 100 indexed photos / 50 searches to prove the workflow.
2. Event Pack: one-off credit bundle for a race, conference, school event, or corporate event.
3. Studio Monthly: recurring credits for photographers and event agencies.
4. Later: branded galleries, bulk export, team seats, API access, or organizer-controlled photo sales.

The prices shown in the UI are hypotheses, not hard-coded Stripe amounts. See `docs/BUSINESS_MODEL.md` for a validation plan and unit-economics formula.

## Tests

```bash
uv run ruff check .
uv run pytest --cov=app
```

## GitHub publishing

After creating an empty repository in your GitHub account:

```bash
git init
git add .
git commit -m "feat: launch consent-based event selfie search MVP"
git branch -M main
git remote add origin git@github.com:Mutoy-choi/event-face-finder.git
git push -u origin main
```

## License

Application code: MIT. Model files retain their upstream licenses and are downloaded separately.
