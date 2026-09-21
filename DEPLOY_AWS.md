# Deploying to AWS (cost-optimized for ~1-2k users)

This puts the whole stack — Postgres, backend, frontend, Nginx, TLS — on a
**single small EC2 instance**, using the `docker-compose.prod.yml` already in
this repo almost exactly as documented in `DEPLOYMENT.md`, plus an **S3
bucket** for gallery photos (uploaded straight from the admin panel). For
the traffic you described (1-2k users), one small instance is plenty, and it
avoids paying for separate managed services (RDS, ALB, ECS) that cost more
than they save you at this scale.

I can't do the AWS-console, IAM, or DNS-registrar parts myself — those need
your AWS account and access to whoever manages `svvdthorur.org`'s DNS
(OpenSRS, in your case — noted, not stored anywhere in this repo or
committed to git). What's in this branch:

- `deploy/aws/setup-ec2.sh` — bootstraps a fresh instance (Docker, Docker
  Compose plugin, Nginx, Certbot).
- `deploy/aws/nginx-svvdthorur.conf` — the reverse-proxy config, ready to
  drop in and hand to Certbot.
- Backend gallery-upload code (`backend/app/services/storage_service.py`,
  `POST /api/v1/gallery/upload-url`) and the matching admin UI (upload
  button on the Gallery page) — this issues a short-lived presigned S3 URL
  so the browser uploads the photo **directly to S3**, never through the
  backend. It's inert (returns 503) until `S3_BUCKET_NAME` is set, so it's
  safe even before you've created the bucket.

Everything below is what's left, done from the AWS Console, your terminal
(SSH), and OpenSRS (for DNS).

## Cost estimate

| Item | Cost |
|---|---|
| EC2 `t3.micro` or `t4g.micro` (1 vCPU/AWS Graviton, 1GB RAM) | **Free** for 12 months on a new AWS account (750 hrs/month), then ~$6-8/month (`t4g.micro` is cheaper than `t3.micro` — Graviton/ARM). Since our Docker images (`python:3.11-slim`, `node:18-alpine`) build fine on ARM, `t4g.micro` is the better long-term default. |
| EBS storage (20-30GB gp3) | Free tier covers 30GB for 12 months, then ~$2-3/month |
| Elastic IP | Free while attached to a running instance |
| Data transfer | First 100GB/month outbound free (Always Free); at 1-2k users you won't get near this |
| TLS certificate (Let's Encrypt via Certbot) | Free |
| S3 (gallery photos) | **Free** for 12 months (5GB storage, 20k GET + 2k PUT requests/month). After that: S3 is not part of AWS's permanent Always Free tier — but at temple-gallery scale (a few hundred photos, a couple GB) it's roughly $0.05-0.50/month, not literally $0. If you want a hard $0 forever instead, see the note at the end of the S3 section below. |

**Total: $0 for the first 12 months, then roughly $8-11/month** (EC2 +
storage; S3 adds well under $1/month at this scale). Compare that to
Railway's per-service metered billing for the same always-on pieces, which
usually lands higher. No managed RDS here — Postgres runs in the same
docker-compose stack on the instance, which is both simpler and avoids
RDS's separate (and pricier) billing.

## 1. Launch the instance

AWS Console → EC2 → **Launch instance**:

- **Name**: `svvd-thorur-prod`
- **AMI**: Amazon Linux 2023 (the setup script targets its package manager,
  `dnf`)
- **Instance type**: `t4g.micro` (Free Tier eligible; if you'd rather stay
  on x86, `t3.micro` is also Free Tier eligible)
- **Key pair**: create/select one — you'll need it to SSH in
- **Network settings** → Edit security group, allow:
  - SSH (22) from your IP only (not `0.0.0.0/0`)
  - HTTP (80) from anywhere
  - HTTPS (443) from anywhere
- **Storage**: 30GB gp3 (fits in the free tier)

Launch it, then **Elastic IPs** (left sidebar) → Allocate → Associate it
with this instance, so the public IP survives a stop/start.

## 2. Point DNS at it

`svvdthorur.org` is managed at OpenSRS (manage.opensrs.net). I don't have a
browser/login tool in this session, so I can't sign in there myself — this
is a couple of clicks for you once you have the Elastic IP from step 1:

1. Log into https://manage.opensrs.net with your domain's credentials.
2. Find `svvdthorur.org` → its DNS Zone / DNS management page (OpenSRS
   sometimes calls this "Advanced DNS" or "Zone Editor" — if you don't see
   DNS management directly, it may be delegated to OpenSRS's own
   nameservers already, which is the common default; if instead the domain
   points at someone else's nameservers, you'd manage records there
   instead — check the "Nameservers" field first if DNS options are
   missing).
3. Add/edit these records:
   - `A` record, host `@` (or blank — means the bare domain), value = the
     Elastic IP → `svvdthorur.org`
   - `A` record, host `www`, value = the same Elastic IP → `www.svvdthorur.org`
4. Save. Propagation is usually fast (minutes) but can take a few hours.

Verify from your own terminal before moving on:

```bash
dig +short svvdthorur.org
dig +short www.svvdthorur.org
# both should print the Elastic IP
```

Don't issue the TLS certificate (step 5) until both resolve correctly —
Let's Encrypt validates ownership by connecting to the domain over HTTP.

## 3. Bootstrap the instance

```bash
ssh -i /path/to/your-key.pem ec2-user@<elastic-ip>

git clone <this-repo-url> svvd-thorur
cd svvd-thorur
git checkout claude/aws-cost-optimized-deploy   # or production/main once merged

sudo bash deploy/aws/setup-ec2.sh
# log out and back in so your user can run docker without sudo
exit
ssh -i /path/to/your-key.pem ec2-user@<elastic-ip>
cd svvd-thorur
```

## 4. Configure secrets and start the stack

`docker-compose.prod.yml` reads `POSTGRES_PASSWORD`, `SECRET_KEY`,
`CORS_ORIGINS`, and `TRUSTED_PROXY_HOPS` from a root `.env` file (not
committed — create it on the server):

```bash
cat > .env <<'EOF'
POSTGRES_DB=templedb
POSTGRES_USER=templeuser
POSTGRES_PASSWORD=REPLACE_WITH_OUTPUT_OF_secrets.token_urlsafe(16)
SECRET_KEY=REPLACE_WITH_OUTPUT_OF_secrets.token_urlsafe(32)
CORS_ORIGINS=https://svvdthorur.org,https://www.svvdthorur.org
TRUSTED_PROXY_HOPS=1
EOF

python3 -c "import secrets; print(secrets.token_urlsafe(16))"   # -> POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # -> SECRET_KEY
# edit .env with those two values, then:
chmod 600 .env
```

Bring up the stack (builds the images locally on the instance — a
`t4g.micro`/`t3.micro` has enough RAM for this, it's just slow, ~5-10 min):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose logs -f backend   # watch migrations run, then Ctrl-C once it's healthy
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3000
```

## 5. Nginx + TLS

```bash
sudo cp deploy/aws/nginx-svvdthorur.conf /etc/nginx/conf.d/svvdthorur.conf
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d svvdthorur.org -d www.svvdthorur.org
# follow the prompts (email for renewal notices, agree to terms)
```

Certbot edits `/etc/nginx/conf.d/svvdthorur.conf` in place to add the HTTPS
server block and the HTTP->HTTPS redirect, and sets up auto-renewal via a
systemd timer (`systemctl list-timers | grep certbot` to confirm).

## 6. Gallery photos on S3

### 6a. Create the bucket

AWS Console → S3 → **Create bucket**:

- **Name**: something globally unique, e.g. `svvd-thorur-gallery`
- **Region**: same region you're using for EC2
- **Block Public Access**: leave "Block *all* public access" checked at the
  account/bucket level for ACLs, but you'll add a narrow bucket *policy*
  below that only opens read access to the `gallery/` prefix — so uncheck
  just **"Block public access to buckets and objects granted through new
  public bucket or access point policies"** (the other three ACL-related
  boxes can stay checked).

### 6b. Bucket policy (public read, gallery photos only)

Bucket → **Permissions** → **Bucket policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGalleryPhotos",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::svvd-thorur-gallery/gallery/*"
    }
  ]
}
```

(Replace the bucket name if you picked a different one.) This makes
uploaded photos publicly viewable — which is what you want for a public
gallery — without opening the whole bucket or allowing writes.

### 6c. CORS (lets the browser upload directly)

Same bucket → **Permissions** → **Cross-origin resource sharing (CORS)**:

```json
[
  {
    "AllowedOrigins": ["https://svvdthorur.org", "https://www.svvdthorur.org", "http://localhost:3000"],
    "AllowedMethods": ["POST", "GET"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"]
  }
]
```

Drop the `localhost:3000` entry once you're done testing locally, if you'd
rather not leave it in.

### 6d. IAM role so the backend can sign uploads

The backend never holds AWS access keys — it uses whatever role is attached
to the EC2 instance (boto3's default credential chain finds this
automatically). Create one:

1. IAM → **Roles** → **Create role** → trusted entity: **AWS service** →
   use case: **EC2**.
2. Skip attaching a managed policy for now; you'll add an inline one.
3. Name it e.g. `svvd-thorur-backend-role`, create it.
4. Open the role → **Add permissions** → **Create inline policy** → JSON:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "s3:PutObject",
         "Resource": "arn:aws:s3:::svvd-thorur-gallery/gallery/*"
       }
     ]
   }
   ```

5. EC2 Console → select your instance → **Actions → Security → Modify IAM
   role** → attach `svvd-thorur-backend-role`.

That's the whole point of using an instance role instead of access keys:
nothing secret to generate, rotate, or accidentally commit.

### 6e. Point the backend at the bucket

```bash
# on the instance, in svvd-thorur/.env
echo "S3_BUCKET_NAME=svvd-thorur-gallery" >> .env
echo "AWS_REGION=<your-bucket-region>" >> .env

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d backend
```

Now the Gallery admin page's "Upload photo" button works: it asks the
backend for a presigned URL, uploads the file straight to S3, and saves the
resulting `https://svvd-thorur-gallery.s3.<region>.amazonaws.com/gallery/...`
URL as the photo's `image_url`. Before this is configured, uploads fail
with a clear message and admins can still paste an external image link
instead — nothing breaks either way.

**On "0 cost":** S3 storage/requests are free for 12 months, then billed
(see the cost table above — realistically pennies to under $1/month for a
temple gallery). If you want a deployment that is contractually $0 forever
rather than "free for a year, then negligible," the alternative is skipping
S3 and serving gallery images from the EC2 instance's own disk instead
(e.g. a bind-mounted `frontend/public/uploads` directory) — that's free for
as long as the instance itself is, but ties image storage to that one
server (no CDN, and you'd lose photos if you ever rebuild the instance from
scratch without backing that folder up). Say the word if you'd rather have
that instead — it's a smaller change than the S3 wiring already on this
branch.

## 7. Verify

- `https://svvdthorur.org` loads the site
- `https://svvdthorur.org/health` → `{"status":"ok"}`
- `https://svvdthorur.org/docs` → 404 (`ENABLE_DOCS` isn't set, defaults to
  off in production)
- Log in as SUPER_ADMIN and fill in **Temple Info**/**Timings** — see the
  "Upgrading to SVVD 2.0" section of `DEPLOYMENT.md`

## Updating the deployed site

```bash
ssh -i /path/to/your-key.pem ec2-user@<elastic-ip>
cd svvd-thorur
git pull origin production   # or whichever branch you deploy from
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Migrations run automatically on backend startup (`backend/entrypoint.sh`).

## Backups

Nothing backs up the database automatically on a bare EC2 instance. Cheapest
option: a small cron job that `pg_dump`s to an S3 bucket (S3 Free Tier: 5GB
for 12 months, then pennies/month at this data size).

```bash
# crontab -e (on the instance)
0 3 * * * cd /home/ec2-user/svvd-thorur && docker compose exec -T postgres pg_dump -U templeuser templedb | gzip > /home/ec2-user/backups/$(date +\%F).sql.gz
```

Set up an S3 lifecycle rule or `aws s3 sync` in the same cron job if you
want it off-instance too.
