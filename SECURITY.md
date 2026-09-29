# Security Policy

## Supported Versions

This is a continuously deployed web application, not a versioned library - there's no numbered release history to speak of. Security fixes go into the `development` branch and deploy to [svvdthorur.org](https://svvdthorur.org) automatically (see `.github/workflows/deploy.yml`). Only the version currently live in production is supported; there's nothing older to backport a fix to.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for a security vulnerability.

Instead, use GitHub's private vulnerability reporting for this repository:

1. Go to the [Security tab](https://github.com/Chaithumoorpa/svvd-thorur/security).
2. Click **Report a vulnerability**.

This sends the report privately to the repository maintainer without exposing it publicly while it's being fixed.

If you'd rather not use GitHub, email the temple office at the address listed on [svvdthorur.org/contact](https://svvdthorur.org/contact) and ask for it to be forwarded to the developer.

### What to expect

This is a small project run by a single maintainer for a temple's own site, not a company with a dedicated security team - please treat response times as best-effort, not a guaranteed SLA:

- **Acknowledgement:** aim for within a few days.
- **Triage:** confirming the issue and its severity, typically within a week of acknowledgement.
- **Fix:** timeline depends on severity - a report affecting devotee accounts, payments, or donation/financial records is treated as urgent; a lower-impact issue may wait for a regular update.

If a report turns out not to be a vulnerability (e.g. expected behavior, or already mitigated), you'll get an explanation rather than silence. Please give us a reasonable time to ship a fix before disclosing publicly.

### Scope

In scope: the code in this repository (`backend/`, `frontend/`) and its deployment configuration (`deploy/`, `.github/workflows/`).

Out of scope: third-party services this project depends on (AWS, Cloudflare, Razorpay, etc.) - please report those directly to the provider.
