# End-to-end tests (Playwright)

`full-workflow.spec.ts` drives a real browser against a real backend +
Postgres database - no mocking. It proves the full stack (browser →
Next.js → FastAPI → Postgres → back to the browser) actually works: sign
in, edit content in the admin panel, and confirm the change is genuinely
live on the public site (and vice versa for logout).

## One-time setup

```bash
cd frontend
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install
```

This sandbox pre-installs Chromium outside the usual Playwright cache;
`playwright.config.ts` points every browser launch at it directly
(`executablePath`), so `npx playwright install` is never needed. If you're
running this somewhere else, remove that `executablePath` override and
run `npx playwright install chromium` once instead.

## Stand up the stack

You need a Postgres database, the backend, and the frontend all running
locally, pointed at each other. Pick any ports/db name; the ones below
match what the spec defaults to.

```bash
# 1. Database
createdb e2edb   # or: psql -c "CREATE DATABASE e2edb"

# 2. Migrate + seed one SUPER_ADMIN user (no email - single-factor login)
cd backend
export DATABASE_URL=postgresql://<user>:<pass>@localhost:5432/e2edb
export SECRET_KEY=e2e-only-throwaway-secret-key-0123456789abcdef
export ENV=development
alembic -c alembic.dev.ini upgrade head
PYTHONPATH=. python e2e/seed_admin.py   # E2E_ADMIN_USERNAME/PASSWORD to override

# 3. Backend
uvicorn app.main:app --host 127.0.0.1 --port 8100

# 4. Frontend (separate terminal) - do NOT pass -H/--hostname to `next dev`;
#    binding it explicitly breaks next-intl's locale redirect on `/` in dev
#    mode (an infinite-redirect Next.js quirk, not an app bug).
cd frontend
INTERNAL_API_BASE_URL=http://127.0.0.1:8100/api/v1 npm run dev -- -p 3100
```

## Run the suite

```bash
cd frontend
E2E_BASE_URL=http://127.0.0.1:3100 \
E2E_ADMIN_USERNAME=e2eadmin \
E2E_ADMIN_PASSWORD=E2ePassword123 \
npm run test:e2e
```

`E2E_BASE_URL` defaults to `http://127.0.0.1:3100`; the admin credential
vars default to the values `seed_admin.py` uses if you don't override them.

A view of what ran: `npx playwright show-report` (opens the HTML report
from the last run).

## Why some steps take a while

The public homepage and Announcements page fetch temple/announcement data
with `next: { revalidate: 60 }` (see `lib/server-api.ts`) - a deliberate
cache so ordinary traffic doesn't hit the database on every request. That
means a change made in the admin panel can take up to a minute to appear
on the public site, for a real visitor and for this test alike. Rather
than race that, the spec polls (reload + re-check) for up to 75s after
each admin edit before asserting it's visible - this is why the full run
takes roughly 1.5 minutes even though the actual interactions are instant.
