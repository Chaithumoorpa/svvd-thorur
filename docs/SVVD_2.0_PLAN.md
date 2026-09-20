# SVVD 2.0 Plan

Branch: `development`. Stack: Next.js 14 / React 18 / TS / Tailwind · FastAPI / SQLAlchemy 2 / PostgreSQL / Alembic · Docker.

## 1. Current architecture (audited)

- **Backend** – layered `api/v1 → services → repositories → models`, JWT (HS256, 60 min), argon2 hashes, roles stored as `users.roles` (Postgres `ARRAY`). Repos commit on their own; DI via `utils/dependencies.py`.
- **Frontend** – Next.js app router. `app/(public)` marketing pages, `app/admin/*` CRUD pages (client components), one axios client in `lib/api.ts`, token in `localStorage`.
- **Infra** – 3 compose files, entrypoint runs `alembic upgrade head` then uvicorn. Frontend proxies `/api/v1` to backend via Next rewrites.

## 2. Audit findings

### Broken / incomplete
| # | Finding | Severity |
|---|---|---|
| 1 | **Migration chain is unsafe.** Commit `26b0816` replaced 3 legacy revisions (`70f03626929a → b385f6d4d9e5 → c8f9a2b3d4e5`) with one `001_initial` that creates only 4 tables (users, temple_members, donors, announcements). Fresh DBs have no poojas/festivals/gallery/tickets/finance/contact/visitor tables; legacy DBs fail with "Can't locate revision". | P0 |
| 2 | **Donor model/schema/API drift.** `DonorCreate` has no `amount`, service reads `data.amount` (create always 500s); receipt endpoints use `donor.receipt_number` / `payment_mode` which don't exist on `Donor`; `Donation` back-populates a `donations` relationship `Donor` lacks (mapper error). | P0 |
| 3 | Ledger sort compares `datetime` with `date` → `TypeError`; end-date filter drops the last day. | P0 |
| 4 | Existing tests can't import (`get_db` missing in `core.database`); Postgres `ARRAY` blocks SQLite tests. | P0 |
| 5 | `Temple` model exists but has no API/service/UI; timings, contact, address are hardcoded in JSX. | P0 |
| 6 | Frontend/back-end contract drift: festival `date` vs `festival_date`; member `role` vs `position`; festivals have no update/delete endpoint though admin UI calls them. | P0 |
| 7 | `next.config` disables TS and ESLint during build; no lint config/script. | P1 |
| 8 | Dashboard "recent activity" is mocked. | P1 |

### Security
- Public `GET /announcements/?show_all=true` returns inactive/draft announcements.
- Public `GET /donors/{id}/receipt` (sequential id) leaks donor name/amount/PAN (IDOR).
- Public `GET /meta/stats` leaks donor/member counts.
- `core/security.py` reads `SECRET_KEY` from env with a hardcoded fallback, independent of `Settings`; compose default secret is guessable. Nothing prevents production boot with it.
- Docs/OpenAPI enabled by default in production; rate-limit/security headers default off in production; login limiter trusts spoofable `X-Forwarded-For`.
- Dev request logger dumps all headers (incl. `Authorization`).
- Registration allows unbounded public signups; no password policy; no audit trail.
- Frontend role checks read the JWT client-side (fine for UX only; backend does enforce, but `ADMIN` can create users? – no, only `SUPER_ADMIN`; keep).

### Data / performance
- Money is `Integer` everywhere (donors, donations, income/expense, tickets, poojas) → must be `Numeric(12,2)`.
- Most list queries lack `ORDER BY` (donors, festivals, poojas, gallery, users); no pagination on any list; ledger loads whole tables into Python.
- `donors` carries donation amount/purpose (denormalised); one donor = one donation.
- Committed `__pycache__`/`.pyc`, `reports/`, and a stray `.bundle` in the repo.
- Duplicate code: `get_*_service` defined both in `dependencies.py` and routers; `auth_service` has dead placeholder; three near-identical alembic ini files.

## 3. Target architecture

- Keep the layered structure; add **`core/rbac.py`** (role → permission matrix, `require_permission()` dependency) and **`services/audit_service.py`** (append-only `audit_logs`).
- One `Settings` object is the only source of secrets; production boot fails on weak/default `SECRET_KEY`, wildcard CORS, enabled docs.
- Public data is served through explicit **public schemas** (`/public/*` read models) that cannot contain private fields.
- Pagination on large lists via `page`/`page_size` with the total in `X-Total-Count` (bodies stay arrays for backward compatibility); deterministic `ORDER BY ..., id`.
- Frontend: typed API layer per module, shared `Loading/Error/Empty` states, temple content fed from API (temple info + timings), SEO metadata + sitemap/robots.

## 4. Database changes (all via Alembic)

| Revision | Change |
|---|---|
| `001_initial` | unchanged |
| `002_reconcile` | idempotent: create any table missing from legacy/fresh DBs, add missing columns (never drops/alters data). Legacy revision ids are re-stamped to `001_initial` by the entrypoint so legacy DBs upgrade cleanly. |
| `003_v2_core` | `donations` (Numeric money, receipt no.), copy legacy donor amounts into it; money columns → `Numeric(12,2)`; `audit_logs`; `temple_timings`; extra `temples` fields (address, map, hero, social); `temple_members.show_on_website/sort_order/photo_url`; festival `end_date/location/image_url`; pooja and gallery `sort_order`; index additions. |

## 5. API changes

- Public (no auth, whitelisted fields): `GET /public/home` (one call for the landing page), `/public/committee`, `/temple/`, `/temple/timings`, existing announcements/poojas/festivals/gallery (active only), `POST /contacts/`, `POST /seva-tickets/`.
- Admin: temple info `PUT /temple/`, timings CRUD (`/temple/timings*`), `GET .../admin/all` for announcements/festivals/poojas/gallery, festivals PUT/DELETE, donations CRUD + receipts (authenticated), `GET /audit-logs`, paginated lists.
- Removed exposure: `show_all` requires admin, `/meta/stats` requires admin, receipts require trustee+, activity feed from audit log.

## 6. RBAC

| Role | Capability |
|---|---|
| SUPER_ADMIN | everything, user management, audit logs |
| ADMIN | all content + donors/donations/finance write, messages |
| TRUSTEE | read donors/donations/finance/members/reports, download receipts |
| STAFF | content editing (announcements, poojas, festivals, gallery), seva tickets, messages |
| GENERAL_USER | no admin access |

Enforced only on the backend via `require_permission`; the frontend hides UI from `/auth/verify` output (never from the JWT).

## 7. Implementation order

1. Foundation: settings/secret hardening, test infra, migrations 002/003, model fixes.
2. RBAC + audit log + closing public leaks.
3. Temple info, timings, announcements, members (public committee), dashboard.
4. Festivals, poojas/sevas, gallery, messages.
5. Donors + donations + finance (Numeric, pagination, receipts).
6. Frontend: contract fixes, lint/tsc enabled, public site polish, admin UX, SEO.
7. Verify each phase: pytest · migrations on Postgres · `tsc` · lint · `next build`.

## 8. Status (end of the 2.0 implementation session)

### Completed

**Foundation & security (P0)**
- Migrations: `002_reconcile` (idempotent, brings fresh *and* legacy databases to the pre-v2 schema without touching data) and `003_v2_core`. Legacy revision ids are re-stamped by `app/core/legacy_stamp.py` (run by `entrypoint.sh`). Verified on PostgreSQL 17 from three starting points: fresh, `001_initial`, and a database built by the deleted legacy chain with seeded data (legacy donor gifts copied into `donations`, legacy pooja amounts preserved). Upgrade -> downgrade -> upgrade round-trip checked.
- Config: one `Settings` object; production refuses a weak/default `SECRET_KEY` and wildcard CORS; docs, rate limiting and security headers default correctly per environment; the client IP used for rate limiting only trusts `X-Forwarded-For` behind configured proxy hops (right-most entry, spoof-resistant).
- RBAC (`core/rbac.py`): role -> permission matrix and `require_permission(...)` on every protected route; roles are read from the database on each request (a demoted or disabled user loses access immediately). `/auth/verify` returns effective permissions for the UI.
- Public leaks closed: unpublished announcements (`show_all`), donor receipt IDOR, `/meta/stats`, `/health` details, member phone/email (new `/public/committee` exposes name/position/photo only), public seva booking could set its own price/payment status (now derived server-side; paid sevas are counter-only).
- Audit log (`audit_logs`, append-only) written on every mutation and on login/password change; secrets are redacted; readable by SUPER_ADMIN (`/audit-logs`; the dashboard activity feed replaces the mocked one).
- Auth: password policy, unique email, timing-equalised login failures, user management (`PATCH /auth/admin/users/{id}`, last-Super-Admin and self-lockout guards), public registration off by default and role-less when on.
- Tests: 78 backend tests (RBAC matrix over every protected route, privacy, auth, content, donations/finance, config) and 14 frontend unit tests.

**Modules (DB -> migration -> repo/service -> API -> authz -> UI -> validation -> loading/error/empty -> tests)**
- Temple information and darshan timings (new; admin-editable; drive header, footer, contact, About, JSON-LD).
- Announcements (date-window publishing, admin list including drafts, soft delete).
- Temple members (public-committee flag, order, photo; contact details stay private).
- Festivals (full CRUD, multi-day, location, image, upcoming filter), Poojas/Sevas (Decimal fee, ordering, soft delete because tickets reference them), Gallery (safe URLs, categories, ordering, paginated), Messages (pagination, honeypot, rate limit, status workflow), Seva tickets (counter tickets, scan, pagination, no HTML injection in printed tickets, race-safe numbering).
- Donors and **Donations** (new model: one donor -> many donations, sequential receipt numbers, PDF, receipts now authenticated, PAN masked for read-only roles, each gift posts to the finance ledger in the same transaction).
- Finance: Numeric money everywhere, SQL aggregates, paginated ledger, fixed the `datetime`/`date` sort crash and the exclusive end-date bug, CSV formula-injection guard.
- Every list endpoint has a deterministic `ORDER BY ..., id`; large lists are paginated (`page`, `page_size`, `X-Total-Count`).

**Frontend**
- Server-rendered public site (data cached 60 s), one aggregate call for the home page, temple-style design system (maroon/saffron/cream, serif headings, ornament dividers), mobile-first navigation, skip link, accessible dialogs and forms, sitemap, robots, canonical redirects for duplicate URLs, JSON-LD (`HinduTemple`, `Event`), Open Graph.
- New admin screens: permission-aware navigation, dashboard, Temple Info, Timings, Donations, Audit Log. All other admin pages were rewritten against the new API with loading / error / empty states, confirmations and inline validation.
- `typescript.ignoreBuildErrors` and `eslint.ignoreDuringBuilds` removed; `npm run lint`, `npm run typecheck`, `npm test` and `npm run build` all pass.

### Verification run at the end
`pytest` 78 passed - migrations on PostgreSQL 17 (fresh / `001_initial` / legacy) - real-app smoke test against PostgreSQL (fresh and legacy-migrated) - `npm run lint` clean - `tsc --noEmit` clean - `vitest` 14 passed - `next build` OK - manual browser check of home, poojas (mobile), login, admin dashboard and the announcement dialog (which exposed and fixed a modal focus/re-render bug).

### Remaining work
| Area | Item |
|---|---|
| Auth | Move the JWT from `localStorage` to an httpOnly cookie (needs a cookie endpoint + CSRF handling); add refresh tokens / a revocation list |
| Rate limiting | In-memory limiters are per process (4 uvicorn workers = 4x the limit); move to Redis if traffic grows |
| Payments | Online payment gateway for paid sevas and online donations (currently counter-only) |
| Notifications | Notification architecture (email/SMS/WhatsApp on booking, message reply, receipt): interface only, no provider chosen |
| Multilingual | i18n routing and Telugu content fields (the schema can gain `*_te` columns; UI strings are English only) |
| Reporting | Donor statements, batch 80G receipts, year-end reports, charts on the finance page |
| Files | Real image uploads (S3/MinIO) instead of pasting image links |
| Data | Migration `004`: drop the legacy `donors.amount/donated_for/donated_on/receipt_*/payment_mode` columns once the copy into `donations` is confirmed; optionally backfill ledger entries for legacy gifts |
| Ops | CI pipeline (pytest + lint + build + migration check), backup/restore runbook, container health checks, error reporting |
| UX | Edit/void for finance transactions (append-only by design today), seva ticket cancellation UI, bulk actions |

### Important technical decisions
1. **Reconcile instead of rewrite**: the migration history had been squashed, stranding old databases. `002` is idempotent and `legacy_stamp` re-stamps the three known legacy revisions.
2. **Backend-only authorization**: the frontend only hides UI using `/auth/verify`; every request re-reads roles from the database and the JWT carries no roles.
3. **Money = `Numeric(12,2)` / `Decimal`**, serialised as JSON numbers for the browser (`MoneyOut`).
4. **A donor no longer holds a gift**: `donations` is the source of truth; the legacy columns stay in place (unmapped) for one release.
5. **Soft delete** for content other rows reference (poojas, festivals, announcements, donors, members); hard delete only for gallery photos, timings and contact messages.
6. **Pagination keeps arrays**: list endpoints still return a JSON array with `X-Total-Count`, so existing clients keep working.
7. **Server components for the public site**: data comes from the backend with a short cache; `force-dynamic` at the root stops empty pages from being frozen at Docker build time when the API is down.
8. **Public registration is off by default** because the site has no devotee-account features.
9. **Session length 8 h** (`ACCESS_TOKEN_EXPIRE_MINUTES`) since revocation is immediate (roles and `is_active` are read per request).

### Known issues / needs business input
- **Temple address/state was inconsistent in the old code** (`Andhra Pradesh` on the site, `Telangana - 506163` on receipts). The seed uses Andhra Pradesh (what visitors saw); please confirm and correct it in Admin -> Temple Info. Phone, WhatsApp and social links were placeholders and stay empty until entered.
- **Legal pages** (privacy, terms, refund) still contain placeholder text; the trustees must supply the real wording.
- Historical donation pages (`/donations/archive`, `/old-donors`, `/trustees-history`) are static archives and were left untouched.
- `public/logo.png` has a baked-in checkerboard "transparent" background; a proper transparent PNG/SVG is needed.
- Timestamps are stored as naive local time; run the backend and Postgres containers with the same `TZ` (compose defaults to `Asia/Kolkata`).
- Legacy gifts copied into `donations` are not in `income_transactions`, so Finance totals only include gifts recorded after the upgrade.
- The frontend Dockerfile still uses Node 18 (past its support window); moving to Node 20 was not attempted.
- PostgreSQL was validated with a local PostgreSQL 17 instance because Docker was unavailable in the authoring environment, so `docker compose up` itself has not been exercised.
