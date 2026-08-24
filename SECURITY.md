# Security Policy

## Supported version

Security fixes are applied to the latest commit on `main` while the project is in MVP development.

## Reporting a vulnerability

Do not disclose vulnerabilities, exposed credentials, private event links, participant images, or biometric templates in a public issue.

Report privately to the repository owner with:

- affected commit and deployment,
- reproduction steps,
- expected and actual behavior,
- impact and any known data exposure,
- suggested mitigation when available.

Please remove real participant photographs, access codes, session cookies, API keys, Stripe secrets, encryption keys, and signed media URLs from reports.

## Privacy and product boundary

PhotoMatch Studio is designed only for consent-based matching inside an organizer-controlled event gallery. Reports are especially welcome for failures involving:

- cross-event or cross-tenant result leakage,
- selfie or embedding persistence beyond the documented lifecycle,
- unauthorized media access,
- weak deletion or retention enforcement,
- bypasses of event access codes, rate limits, or CSRF protection,
- webhook signature or credit-accounting errors.

Public-web crawling, social-profile identification, and unrestricted person tracking are outside the supported product scope.
