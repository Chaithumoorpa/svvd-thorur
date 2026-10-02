# Serverless production: Vercel + AWS Lambda + Amazon RDS

Target architecture for the `production` branch:

```
browser ──► svvdthorur.org        Vercel (Next.js, region bom1)
   │              │ server-side rendering fetches
   ▼              ▼
api.svvdthorur.org ──► API Gateway (HTTP API) ──► Lambda alias "live" (FastAPI via Mangum)
                                                     │
EventBridge Scheduler ──{"task": ...}──────────────►─┤
GitHub Actions ─────────{"task": "migrate"}────────►─┘
                                                     ▼
                                     Amazon RDS for PostgreSQL 15 (TLS, verify-full)
```

`development` and the current EC2 deployment are untouched until you cut over
(step 8). Everything below assumes region **ap-south-1** (Mumbai, where the
EC2 instance and the S3 bucket already live) and these names - change them
consistently if you prefer others:

| Thing | Name used here |
|---|---|
| Lambda function | `svvd-api` (alias `live`) |
| ECR repository | `svvd-api` |
| RDS instance | `svvd-db` |
| API domain | `api.svvdthorur.org` |

Placeholders: `ACCOUNT_ID` (12-digit AWS account id), `RDS_ENDPOINT`
(shown on the RDS instance page once created).

---

## 0. Read first: cost and trade-offs

| Item | Approx. monthly cost after free tier |
|---|---|
| Vercel Hobby | $0 (see the warning below) |
| Lambda (1 GB, ~100k requests) | ~$0 (inside the permanent free tier) |
| API Gateway HTTP API | ~$0.10 (about $1 per million requests) |
| RDS `db.t4g.micro` + 20 GB gp3, single-AZ | ~$15-18 |
| RDS public IPv4 address | ~$3.60 |
| ECR (keep last 5 images) | ~$0.10-0.50 |
| **Total** | **~$19-23/month** |

These figures are estimates; confirm them in the AWS Pricing Calculator for
ap-south-1. Note that this is **more** than today's single EC2 instance
(~$8-11/month): RDS alone costs more than the instance that currently runs
everything. What you get for it: no server to patch, managed backups with
point-in-time restore, compute that scales to zero, and frontend, API and
database that fail and deploy independently. If the bill is the deciding
factor, the backend config accepts any Postgres through the same `DB_*`
variables (e.g. a serverless Postgres free tier), so RDS can be swapped
without code changes.

**Vercel Hobby is for personal, non-commercial use.** Vercel's fair-use rules
count requesting or processing payments from visitors as commercial use. A
temple site is fine on Hobby today, but move to Vercel Pro **before**
Razorpay donations go live (or re-check Vercel's current terms).

**Known Lambda limitations of this codebase** (fine at this site's traffic,
worth knowing):
- Rate limits (login, OTP, booking) and the 45-second content cache live in
  process memory, so each concurrently running Lambda container keeps its own
  copy. Limits are looser under concurrency, and an admin edit can take up to
  45 s to show on another container. Turnstile still protects every form.
  Moving the limiters to a shared store (a Postgres table or DynamoDB) is the
  fix if this ever matters.
- Cold starts: the first request after a few idle minutes takes roughly 2-4 s.
- API Gateway caps a request at 30 s and Lambda caps a response at 6 MB. The
  ticket/receipt PDFs are far below both.

---

## 1. Git: a clean `production` branch

`production` already exists on GitHub but is 66 commits behind `development`
(and 0 ahead), so it is fast-forwarded rather than recreated:

```bash
git fetch origin
git switch production               # first time: creates a local branch tracking origin/production
git merge --ff-only origin/development
git push origin production
git switch development              # back to where you work day to day
```

`--ff-only` refuses to run (rather than creating a merge commit) if
`production` ever gains commits of its own. Then in GitHub → **Settings →
Branches → Add rule** for `production`: require a pull request and require
the **CI** checks. CI now runs on PRs into `production` too.

Open a PR **into `production`** from the branch carrying this migration. Do
not merge it into `development` before cutover: it removes the frontend's
Docker setup that the current EC2 deploy (`deploy.yml` → `deploy/aws/deploy.sh`)
still builds.

Release flow afterwards: work on `development` → PR `development` →
`production` → merging deploys the backend (GitHub Actions) and the frontend
(Vercel).

---

## 2. Database: Amazon RDS for PostgreSQL

RDS console → **Create database**:

- Engine **PostgreSQL 15** (same major version as today's container)
- Template **Free tier** if offered, otherwise **Dev/Test**, **Single-AZ**
- Identifier `svvd-db`; master username `templeuser`; **Auto generate password**
  (save it in your password manager, it becomes `DB_PASSWORD`)
- Instance `db.t4g.micro`, storage 20 GB gp3, storage autoscaling off
- Connectivity: **Don't connect to an EC2 compute resource**, default VPC,
  **Public access: Yes**, new security group `svvd-db-sg`
- Additional configuration: initial database name `templedb`, backup
  retention **7 days**, **deletion protection on**

Then:

1. Security group `svvd-db-sg` → inbound rule PostgreSQL 5432 from
   `0.0.0.0/0`. Lambda runs outside a VPC here and has no fixed IP, so the
   database is protected by TLS (`verify-full`, enforced by the image) plus a
   long random password, the same model hosted-Postgres providers use. The
   private alternative (Lambda in a VPC, RDS not public) also needs a NAT
   gateway, at ~$33/month or more, because the API must reach Cloudflare
   Turnstile and SES on the internet.
2. Confirm TLS is mandatory: **Parameter groups** → the instance's group →
   `rds.force_ssl` = `1` (the default on PostgreSQL 15+).

RDS automated backups replace `deploy/aws/backup-db.sh` and its crontab line.

---

## 3. Container registry and first image

```bash
aws ecr create-repository --repository-name svvd-api --region ap-south-1 \
  --image-scanning-configuration scanOnPush=true
aws ecr put-lifecycle-policy --repository-name svvd-api --region ap-south-1 \
  --lifecycle-policy-text '{"rules":[{"rulePriority":1,"description":"keep last 5","selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":5},"action":{"type":"expire"}}]}'
```

The first image has to be pushed by hand, because the function can't be
created without one. From any machine with Docker:

```bash
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com
cd backend
docker buildx build --platform linux/amd64 --provenance=false -f Dockerfile.lambda \
  -t ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/svvd-api:initial --push .
```

---

## 4. Lambda function

**Execution role** (IAM → Roles → Create → AWS service: Lambda), name
`svvd-api-role`:
- managed policy `AWSLambdaBasicExecutionRole` (CloudWatch logs)
- inline policy: the same S3 statements as the EC2 role in
  `DEPLOY_AWS.md` (step 6d), plus
  `{"Effect":"Allow","Action":["ses:SendEmail","ses:SendRawEmail"],"Resource":"*"}`

**Function**: Lambda → Create function → **Container image** → image
`svvd-api:initial`, architecture **x86_64**, role `svvd-api-role`. Then
Configuration →
- General: memory **1024 MB** (more memory also means more CPU, so faster
  cold starts), timeout **60 s** (migrations and daily jobs; HTTP requests
  are still capped at 30 s by API Gateway)
- Environment variables (copy the values from the EC2 host's
  `backend/.env.production` / `.env`):

| Variable | Value |
|---|---|
| `DB_HOST` | `RDS_ENDPOINT` |
| `DB_NAME` | `templedb` |
| `DB_USER` | `templeuser` |
| `DB_PASSWORD` | the RDS password |
| `SECRET_KEY` | the **current** production value (a new one signs everyone out) |
| `TURNSTILE_SECRET_KEY` | current value |
| `CORS_ORIGINS` | `https://svvdthorur.org,https://www.svvdthorur.org` |
| `FRONTEND_BASE_URL` | `https://svvdthorur.org` |
| `S3_BUCKET_NAME` | `svvd-thorur-gallery` |
| `SES_FROM_EMAIL`, `ADMIN_NOTIFICATION_EMAIL`, `ALLOW_PUBLIC_REGISTRATION` | current values |

Already set by the image, so leave them out: `ENV=production`, `TZ`,
`DB_SSLMODE=verify-full`, `DB_SSLROOTCERT`, pool sizes, and the docs,
security-header and rate-limit flags. `AWS_REGION` is set by Lambda itself to
the function's region, so the S3 bucket and SES identity must be in
ap-south-1, which is where they are today. Keep `TRUSTED_PROXY_HOPS` unset (0):
API Gateway passes the real client IP to the app.

**Alias**: Versions → **Publish new version** (version 1) → Aliases → Create
alias `live` → version 1. API Gateway and the schedules always target `live`;
deploys move the alias.

**Logs**: CloudWatch → Log groups → `/aws/lambda/svvd-api` → retention
**1 month** (the default "never expire" accumulates cost).

Smoke-test the database connection and create the schema:

```bash
aws lambda invoke --function-name svvd-api --qualifier live \
  --cli-binary-format raw-in-base64-out --payload '{"task":"migrate"}' out.json && cat out.json
# {"task": "migrate", "ok": true, "revision": "023_..."}
```

(Skip this if you're about to restore the EC2 data in step 7; the restore
brings the schema with it, and `migrate` runs afterwards anyway.)

---

## 5. API Gateway and the `api.` domain

1. **ACM** (in **ap-south-1**): request a public certificate for
   `api.svvdthorur.org`, validate it with the DNS record ACM shows.
2. **API Gateway → Create API → HTTP API** → integration **Lambda**,
   function `svvd-api`, **alias `live`** (paste the alias ARN
   `arn:aws:lambda:ap-south-1:ACCOUNT_ID:function:svvd-api:live`), route
   `ANY /{proxy+}` and stage `$default` with auto-deploy. Don't configure CORS
   in API Gateway: FastAPI already answers preflights (`CORS_ORIGINS`), and
   two layers doing CORS conflict. Answer **Yes** when the console asks to add
   invoke permission to the alias.
3. **Custom domain names → Create** `api.svvdthorur.org` with the ACM
   certificate → **API mappings** → this API, stage `$default`.
4. DNS: `CNAME api` → the custom domain's **API Gateway domain name**
   (`d-xxxx.execute-api.ap-south-1.amazonaws.com`).

```bash
curl https://api.svvdthorur.org/health      # {"status":"ok"}
```

---

## 6. Daily jobs: EventBridge Scheduler (replaces the EC2 crontab)

Create a role `svvd-scheduler-role` that EventBridge Scheduler
(`scheduler.amazonaws.com`) can assume, with
`{"Effect":"Allow","Action":"lambda:InvokeFunction","Resource":"arn:aws:lambda:ap-south-1:ACCOUNT_ID:function:svvd-api:live"}`.
Then:

```bash
FN=arn:aws:lambda:ap-south-1:ACCOUNT_ID:function:svvd-api:live
ROLE=arn:aws:iam::ACCOUNT_ID:role/svvd-scheduler-role

aws scheduler create-schedule --name svvd-festival-announcements --region ap-south-1 \
  --schedule-expression "cron(0 6 * * ? *)" --schedule-expression-timezone Asia/Kolkata \
  --flexible-time-window Mode=OFF \
  --target "{\"Arn\":\"$FN\",\"RoleArn\":\"$ROLE\",\"Input\":\"{\\\"task\\\":\\\"generate_festival_announcements\\\"}\"}"

aws scheduler create-schedule --name svvd-occasion-greetings --region ap-south-1 \
  --schedule-expression "cron(5 6 * * ? *)" --schedule-expression-timezone Asia/Kolkata \
  --flexible-time-window Mode=OFF \
  --target "{\"Arn\":\"$FN\",\"RoleArn\":\"$ROLE\",\"Input\":\"{\\\"task\\\":\\\"send_occasion_greetings\\\"}\"}"
```

Both jobs are idempotent, so a retried or repeated run never double-posts or
double-sends. Only principals allowed `lambda:InvokeFunction` can trigger a
task; a web request always arrives as an API Gateway event and is routed to
the app, never to a job (`app/lambda_handler.py`).

---

## 7. GitHub Actions: deploys on push to `production`

`.github/workflows/deploy-serverless.yml` runs the backend tests, builds and
pushes the image, publishes a new Lambda version, runs `migrate` **on that
version**, and only then moves the `live` alias. A failed migration leaves
the old version serving traffic. The job log prints a one-line rollback
command (it moves the alias back).

One-time setup, no stored AWS keys (GitHub OIDC):

1. IAM → Identity providers → Add → OpenID Connect, URL
   `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
2. IAM → Roles → Create → Web identity → that provider, audience
   `sts.amazonaws.com`, GitHub organization `Chaithumoorpa`, repository
   `svvd-thorur`, branch left empty; name it `svvd-github-deploy`. Then edit
   its trust policy so the `sub` condition is exactly
   `repo:Chaithumoorpa/svvd-thorur:environment:production` (only the
   `production` environment's jobs can assume it).
3. Inline policy on that role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*"},
    {"Effect": "Allow", "Action": [
       "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
       "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:BatchGetImage",
       "ecr:GetDownloadUrlForLayer", "ecr:GetRepositoryPolicy", "ecr:SetRepositoryPolicy"],
     "Resource": "arn:aws:ecr:ap-south-1:ACCOUNT_ID:repository/svvd-api"},
    {"Effect": "Allow", "Action": [
       "lambda:UpdateFunctionCode", "lambda:GetFunction", "lambda:GetFunctionConfiguration",
       "lambda:PublishVersion", "lambda:GetAlias", "lambda:UpdateAlias", "lambda:InvokeFunction"],
     "Resource": ["arn:aws:lambda:ap-south-1:ACCOUNT_ID:function:svvd-api",
                  "arn:aws:lambda:ap-south-1:ACCOUNT_ID:function:svvd-api:*"]}
  ]
}
```

4. GitHub → Settings → **Secrets and variables → Actions → Variables**:

| Variable | Value |
|---|---|
| `AWS_REGION` | `ap-south-1` |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::ACCOUNT_ID:role/svvd-github-deploy` |
| `ECR_REPOSITORY` | `svvd-api` |
| `LAMBDA_FUNCTION` | `svvd-api` |
| `API_BASE_URL` | `https://api.svvdthorur.org` |

Until these exist, a push to `production` gives a red run that fails at
"Check repository variables" and changes nothing.

---

## 8. Frontend on Vercel

1. vercel.com → **Add New → Project** → import `Chaithumoorpa/svvd-thorur`.
2. **Root Directory: `frontend`**. Next.js is detected automatically, and
   `frontend/vercel.json` pins server-side rendering to Mumbai (`bom1`), next
   to the API and database.
3. Environment variables, set for **Production and Preview**:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://api.svvdthorur.org` |
| `NEXT_PUBLIC_SITE_URL` | `https://svvdthorur.org` |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | current value |

   The build fails on purpose if `NEXT_PUBLIC_API_URL` is missing; otherwise
   every page would quietly render its empty state. Preview deployments
   (`*.vercel.app`) render pages server-side fine, but the API's CORS policy
   blocks their in-browser calls by design.
4. Settings → Git → **Production Branch: `production`**.
5. Deploy, then open the `*.vercel.app` production URL and check that pages
   show real temple data (that proves the server-side calls reach the API).

---

## 9. Cutover (about 15-30 minutes of read-only time)

1. Lower the TTL of the `svvdthorur.org` / `www` DNS records to 300 s a day
   ahead.
2. On the EC2 host, stop writes and dump:
   ```bash
   cd /home/ubuntu/svvd-thorur
   docker compose -f docker-compose.yml -f docker-compose.prod.yml stop backend
   docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres \
     pg_dump -U templeuser -d templedb -Fc --no-owner --no-acl > svvd-cutover.dump
   ```
3. Restore into RDS (from the same host; it can reach RDS over the internet):
   ```bash
   docker run --rm -i -e PGPASSWORD='<RDS password>' -e PGSSLMODE=require postgres:15 \
     pg_restore -h RDS_ENDPOINT -U templeuser -d templedb --no-owner --no-acl < svvd-cutover.dump
   ```
4. Run `migrate` (step 4's invoke command). It should report the same
   revision the EC2 database was on.
5. Vercel → Domains → add `svvdthorur.org` and `www.svvdthorur.org`, then
   point DNS at the records Vercel shows.
6. Check: home page data, admin login (Turnstile + OTP email), one test seva
   booking with its PDF, a gallery upload.
7. GitHub → Actions → **Deploy to production** (the EC2 workflow) →
   **Disable workflow**, so pushes to `development` stop redeploying the
   retired instance. Then merge `production` back into `development` once,
   so both branches share the new layout.
8. Keep the EC2 instance **stopped, not terminated**, for two weeks.

**Rollback**: point DNS back at the EC2 instance's IP and
`docker compose ... start backend`. Writes made on the new stack after
cutover are not on the EC2 database. If they matter, dump RDS and restore it
onto EC2 the same way as step 3, in reverse.

---

## Local development after this change

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d   # Postgres + backend on :8000
cd frontend && npm run dev                                             # http://localhost:3000, proxies /api/v1 to :8000
```

To try the Lambda image locally, the AWS base image includes the Lambda
Runtime Interface Emulator:

```bash
cd backend
docker build -f Dockerfile.lambda -t svvd-api .
docker run --rm -p 9000:8080 -e DATABASE_URL=postgresql://... -e DB_SSLMODE=disable \
  -e SECRET_KEY=... -e TURNSTILE_SECRET_KEY=... svvd-api
curl -XPOST localhost:9000/2015-03-31/functions/function/invocations -d '{"task":"migrate"}'
```
