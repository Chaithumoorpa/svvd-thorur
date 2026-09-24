# SVVD Thorur

Temple management platform for **Sri Varasidhi Vinayaka Swamy Devasthanam**, Thorur, Andhra Pradesh — a public site (darshan timings, poojas, festivals, gallery, online seva booking) plus an admin panel for temple staff (donors & donations, finance ledger, seva tickets, members, content management).

Live at [svvdthorur.org](https://svvdthorur.org).

## Tech stack

- **Backend:** FastAPI (Python), SQLAlchemy + Alembic, PostgreSQL
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, [next-intl](https://next-intl.dev) for i18n
- **Infra:** Docker Compose, deployed on a single AWS EC2 instance behind Let's Encrypt TLS, S3 for gallery/ticket/receipt storage, SES for transactional email
- **CI/CD:** GitHub Actions — backend + frontend tests gate every deploy to `development`

## Features

- **Public site:** temple info, darshan timings, poojas/sevas, festivals, announcements, gallery, donation info, contact form — in English, Telugu, Tamil, Kannada and Hindi
- **Online seva booking:** email-OTP verified (no account needed), auto-confirmed by email
- **Admin panel:** role-based access (Super Admin / Admin / Trustee / Staff), donor & donation records with receipt PDFs, finance ledger auto-synced from seva tickets and donations, member directory, content management (announcements, festivals, poojas, gallery), audit log
- **Auth:** JWT sessions, forced password change for new accounts, self-service password reset via emailed link, admin user management
- **Notifications:** SES-backed email for password resets, new-account welcome, contact-form replies, booking confirmations, and admin alerts (new bookings/donations/contact messages, CI/CD failures)
- **SEO:** per-locale canonical + hreflang tags, sitemap.xml, JSON-LD structured data

## Repo structure

```
backend/    FastAPI app (app/api, app/services, app/models, app/schemas, alembic/ migrations, tests/)
frontend/   Next.js app (app/, components/, lib/, messages/ translations)
deploy/     EC2 provisioning + deploy scripts
docs/       Design/planning docs
```

## Local development

Requires Docker.

```bash
git clone <repo-url>
cd svvd-thorur
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

- Backend: http://localhost:8000 (API docs at `/docs`)
- Frontend: http://localhost:3000
- Postgres: exposed on `5432` for local tools

Database migrations run automatically on backend startup (`alembic upgrade head`).

## Running tests

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
pytest

# Frontend
cd frontend
npm ci
npm run typecheck
npm run lint
npm run test
npm run build
```

CI runs all of the above on every push; `development` only deploys if they pass.

## Deployment

Production runs on AWS EC2 via Docker Compose, deployed automatically on push to `development`. See [DEPLOY_AWS.md](./DEPLOY_AWS.md) for infrastructure setup, environment variables, and the CI/CD pipeline. See [BRANCHING_STRATEGY.md](./BRANCHING_STRATEGY.md) for the branching model.

## License

Proprietary — see [LICENSE](./LICENSE). All rights reserved.
