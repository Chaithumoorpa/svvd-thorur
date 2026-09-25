# Architecture

A short tour of how the pieces fit together. For "how do I run this locally",
see the root [README.md](../README.md).

## The two apps

```
backend/    FastAPI (Python 3.11), SQLAlchemy + Alembic, PostgreSQL
frontend/   Next.js 14 (App Router), TypeScript, Tailwind, next-intl for i18n
```

They talk over a plain REST API (`/api/v1/...`); the frontend never touches
the database directly. In production both run as separate containers behind
one nginx reverse proxy on a single EC2 instance (see
[../DEPLOY_AWS.md](../DEPLOY_AWS.md)).

## Backend layout

```
app/
  api/v1/        One router module per resource (auth, seva_tickets, donors,
                  temple, announcement, contact, gallery, members, finance,
                  festival, pooja, audit, stats, public, meta).
                  Routers stay thin: parse/validate the request, call one
                  service method, log an audit entry, shape the response.
  services/       Business logic and orchestration. Where the actual rules
                  live (e.g. a receipt can't be edited once issued, a PENDING
                  ticket can't be scanned in, a repeated-deletion burst
                  alerts a Super Admin).
  repositories/   Thin data-access layer - one per aggregate, wraps the
                  SQLAlchemy queries a service needs. Services depend on
                  repositories, never on the ORM session directly, except
                  where a service legitimately needs to compose several
                  repositories in one transaction (donations + the finance
                  ledger, for example).
  models/         SQLAlchemy models - the source of truth for the schema.
                  Every model is imported by app/models/__init__.py so
                  Alembic's autogenerate sees it.
  schemas/        Pydantic request/response models. Validation (mobile
                  number format, money bounds, safe URLs, blank-to-None
                  normalization) lives here, in app/schemas/common.py where
                  it's shared.
  core/           Settings (environment-aware: dev vs production behaves
                  differently - see rbac.py, config.py, middleware.py),
                  the RBAC permission table, DB session setup, the
                  migration-validator that runs at startup.
  utils/          FastAPI dependencies (get_db, get_current_user,
                  require_permission, get_audit, ...) and the rate limiter.
  cli/            One-off management commands run via
                  `python -m app.cli.<name>` (e.g. the daily festival
                  announcement generator - see its own docstring for the
                  crontab line).
alembic/versions/ Migrations, numbered sequentially (001, 002, ...). Always
                  chain from the current head - see RELEASE_PROCESS.md for
                  why a single head matters in production.
tests/            pytest, one file per feature/endpoint group. Every backend
                  change in this repo's history has shipped with tests
                  alongside it - follow that pattern.
```

### Request flow

A typical write request: `router` → `require_permission(...)` dependency
(RBAC gate) → `service` method (validates business rules, talks to one or
more `repository` instances, commits) → `audit.log(...)` (see
[RBAC_AND_PERMISSIONS.md](./RBAC_AND_PERMISSIONS.md)) → best-effort email via
`EmailService` if the action warrants one → response shaped by a Pydantic
`schemas` model.

### Cross-cutting services worth knowing about

- **`EmailService`** (`app/services/email_service.py`) - all outbound email
  goes through this. Every call is best-effort: a mail failure never blocks
  the action that triggered it. Uses AWS SES; a no-op if SES isn't
  configured (so tests and local dev don't need real credentials).
- **`OtpService`** - shared helpers back both the booking-email verification
  flow and the login two-factor flow, using the same `EmailOtp` table with a
  `purpose` column to keep the two uses from colliding.
- **`StorageService`** - issues presigned S3 POST uploads so the browser
  uploads a photo directly to S3 (no file traffic through the backend).
  Gallery and member photos share the bucket's public-read `gallery/*`
  prefix (member photos live under a nested `gallery/members/` key); ticket
  and receipt PDFs use a separate private-by-default upload path.
- **`AuditService`** - append-only audit log for every mutating admin
  action. Also watches for repeated deletions by the same actor in a short
  window and alerts every Super Admin by email when a burst crosses the
  threshold - see `_maybe_alert_on_repeated_deletions`.
- **`notify_devotees`** (`app/services/notification_service.py`) - the one
  place that decides "who counts as a devotee to email" (an active user
  with an email on file who isn't staff, a trustee, or an admin). Reused
  wherever a devotee-facing change should go out by email (darshan timing
  changes, new announcements).

### Background/scheduled work

There's no task queue - the one recurring job (festival auto-announcements)
runs as a plain CLI command from cron on the host, once a day. If a second
recurring job is ever needed, follow that same pattern rather than adding
new infrastructure, unless the workload genuinely outgrows cron.

## Frontend layout

```
app/            Next.js App Router pages. app/[locale]/(public)/... is the
                public, translated site; app/admin/... is the admin panel
                (English-only, behind login).
components/     Shared UI. components/admin/ (AdminPage, AuthContext,
                ConfirmDialog, ...) and components/public/ (BookSeva, ...)
                are the two main groups.
lib/            api.ts (every backend call, one function per endpoint),
                types.ts (the TypeScript shape of every API request/response
                - keep in sync with the backend Pydantic schemas by hand),
                format.ts (shared formatting/validation helpers).
hooks/          useLoad (data fetching + loading/error state) and useAction
                (mutation + busy/success/error state) - almost every admin
                page is built from these two.
messages/       next-intl translation JSON, one file per locale
                (en, te, ta, kn, hi).
```

The admin panel is permission-aware: `useAuth()` exposes `can('resource:action')`,
and pages hide/disable actions the signed-in user's role doesn't grant -
but that's a UX convenience only. The backend enforces every permission
independently; never rely on the frontend hiding a button as the real gate.

## Data model at a glance

- **User** - login identity (username/password, optional email/phone,
  `roles: string[]`). A GENERAL_USER is a self-registered devotee account;
  ADMIN/STAFF/TRUSTEE/SUPER_ADMIN are staff/admin roles created by a
  Super Admin.
- **Member** vs **User** - a committee member (name/photo/position shown on
  the public site, optionally) is a separate `Member` row from a login
  `User`. They can be linked (`Member.user_id`) but usually aren't.
- **SevaTicket** - one booked seva. `payment_status` is `FREE`, `PENDING`
  (a paid seva booked online, fee collected in person - there's no payment
  gateway yet), or `PAID`. `booked_by_user_id` links it to a signed-in
  devotee's account for "My Bookings"; anonymous bookings and counter
  tickets leave it null.
- **Donor** / **Donation** - a donor's personal details live once on
  `Donor`; each gift is its own `Donation` row. Every donation posts an
  `IncomeTransaction` in the same transaction, and the two stay in sync
  (edit/delete propagates to the ledger entry) - see
  `DonationService` for the exact rules.
- **IncomeTransaction** / **ExpenseTransaction** - the finance ledger.
  Income entries are either posted automatically (from a paid seva ticket
  or a donation) or entered manually by staff; the two paths use a
  `source_type` column to stay distinguishable.
- **AuditLog** - one row per mutating admin action, `actor_id` nullable so
  the trail survives the actor's own account being deleted (see
  RBAC_AND_PERMISSIONS.md).
