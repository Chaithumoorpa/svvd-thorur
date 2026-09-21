# Deploying to Railway + svvdthorur.org

This repo is a monorepo with two deployable services (`backend`, a FastAPI API,
and `frontend`, a Next.js app) plus PostgreSQL. Railway deploys each service
from its own root directory and Dockerfile, and offers a managed Postgres
plugin — there's no single "docker-compose up" button, so each piece below is
its own step in the Railway dashboard.

I can't complete this deployment myself: it needs your Railway account login,
billing/plan decisions, and access to whoever manages DNS for
`svvdthorur.org`. What I *did* do in this branch:

- Made the backend's port configurable (`backend/Dockerfile` now honors
  `$PORT`, which Railway assigns per service — it fell back to a hardcoded
  8000 before, which Railway can't route to).
- Added `backend/railway.toml` and `frontend/railway.toml` so Railway builds
  each service from its Dockerfile with a health check.

Everything below is what's left, done from railway.app and your domain
registrar's dashboard.

## 1. Heads up on "free"

Railway no longer has an indefinite free tier. New accounts get a one-time
trial credit; after that it's the Hobby plan (~$5/month usage credit,
card required) or pay-as-you-go. A always-on API + frontend + Postgres will
likely exceed the trial credit within days. If you want something that stays
free indefinitely (with cold-start delays), Render's free web services +
90-day free Postgres is the closer fit — same Dockerfiles would work there
too. Decide which trade-off you want before spending time wiring up DNS.

## 2. Create the project

1. https://railway.app → sign up / log in (GitHub login is easiest since
   this repo is on GitHub) → **New Project**.
2. **Deploy from GitHub repo** → pick `chaithumoorpa/svvd-thorur` → branch
   `claude/eloquent-fermi-jb0h7j` (or `main`/`production` once this is merged).
   Railway will try to auto-detect a service from the repo root; delete that
   guess — you'll add the three services explicitly below.

## 3. Add PostgreSQL

**New** → **Database** → **Add PostgreSQL**. Railway provisions it and
exposes connection info as service variables (`PGHOST`, `PGPORT`, `PGUSER`,
`PGPASSWORD`, `PGDATABASE`, and a ready-made `DATABASE_URL`).

## 4. Add the backend service

**New** → **GitHub Repo** → same repo → in service **Settings**:

- **Root Directory**: `backend`
- **Builder**: Dockerfile (should auto-detect `backend/railway.toml`)

**Variables** (Settings → Variables). Reference the Postgres plugin's URL
with Railway's variable-reference syntax so it stays in sync:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `SECRET_KEY` | generate with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` — 32+ random chars, the app refuses to boot without it |
| `ENV` | `production` |
| `DEBUG` | `false` |
| `ENABLE_DOCS` | `false` |
| `ENABLE_SECURITY_HEADERS` | `true` |
| `ENABLE_RATE_LIMITING` | `true` |
| `ALEMBIC_CONFIG` | `alembic.prod.ini` |
| `TRUSTED_PROXY_HOPS` | `2` (Railway's edge proxy, then the Next.js rewrite in front of this service — see `DEPLOYMENT.md`) |
| `CORS_ORIGINS` | `https://svvdthorur.org,https://www.svvdthorur.org` |

Deploy. Once it's up, open **Settings → Networking → Generate Domain** to get
a temporary `*.up.railway.app` URL and confirm `https://<that-url>/health`
returns `{"status":"ok"}`.

## 5. Add the frontend service

**New** → **GitHub Repo** → same repo again → **Settings**:

- **Root Directory**: `frontend`
- **Builder**: Dockerfile

**Variables**:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `/api/v1` |
| `INTERNAL_API_BASE_URL` | `http://backend.railway.internal:8000/api/v1` (Railway's private network — use the backend service's actual private name, shown on its Settings page, if it differs from `backend`) |
| `NEXT_PUBLIC_SITE_URL` | `https://svvdthorur.org` |
| `NEXT_PUBLIC_ENV` | `production` |
| `NEXT_PUBLIC_ENABLE_DEBUG_BANNER` | `false` |
| `NEXT_PUBLIC_ENABLE_API_LOGGING` | `false` |

Also set `NEXT_PUBLIC_API_BASE_URL=/api/v1` as a **build-time** variable
(Settings → Variables lets you mark it available at build) since
`frontend/Dockerfile` bakes it in via `ARG`/`ENV` during `npm run build`.

Deploy, then **Generate Domain** here too and confirm the temporary URL loads
the site and that pages hitting `/api/v1/...` work (proves the private
network link to the backend is correct).

## 6. Point svvdthorur.org at it

1. On the **frontend** service → **Settings → Networking → Custom Domain** →
   enter `svvdthorur.org` (and again for `www.svvdthorur.org`).
2. Railway shows you the exact DNS record(s) to add for each — usually a
   `CNAME` for `www`, and either a `CNAME` (if your registrar supports CNAME
   flattening/ALIAS at the apex) or an `A`/`ANAME` record for the bare
   `svvdthorur.org` root. **Use the values Railway's dashboard shows you at
   that moment** rather than any older or third-party guide — Railway's edge
   IPs/targets aren't guaranteed to stay the same over time.
3. Add those records at whichever registrar/DNS provider manages
   `svvdthorur.org` (Namecheap, GoDaddy, Cloudflare, Route53, etc. — I don't
   have access to that account either).
4. Wait for DNS propagation (usually minutes, can take up to 24h) — Railway's
   domain settings page shows a green check once it verifies. TLS is issued
   automatically.
5. Update backend `CORS_ORIGINS` (step 4) to match the final domain(s) if you
   change what you point at the site.

## 7. Verify

- `https://svvdthorur.org/health` is proxied through the frontend? No —
  hit the backend's own Railway domain directly for `/health`, or
  `https://svvdthorur.org/api/v1/...` for an actual API route through the
  frontend rewrite.
- `https://svvdthorur.org/docs` → should 404 (`ENABLE_DOCS=false`).
- Log in as a SUPER_ADMIN and fill in **Temple Info**/**Timings** per the
  "Upgrading to SVVD 2.0" section of `DEPLOYMENT.md` — the public site pulls
  that content from the database, not hard-coded values.

## Ongoing deploys

Once wired up, Railway auto-deploys each service on every push to the branch
you connected. Migrations run automatically — `backend/entrypoint.sh` runs
`alembic upgrade head` before starting uvicorn on every boot.
