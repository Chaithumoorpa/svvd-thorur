# Deploying to AWS (cost-optimized for ~1-2k users)

This puts the whole stack — Postgres, backend, frontend, Nginx, TLS — on a
**single small EC2 instance**, using the `docker-compose.prod.yml` already in
this repo almost exactly as documented in `DEPLOYMENT.md`. For the traffic
you described (1-2k users), one small instance is plenty, and it avoids
paying for separate managed services (RDS, ALB, ECS) that cost more than
they save you at this scale.

I can't do the AWS-console or DNS-registrar parts myself — those need your
AWS account and access to whoever manages `svvdthorur.org`'s DNS. What's in
this branch:

- `deploy/aws/setup-ec2.sh` — bootstraps a fresh instance (Docker, Docker
  Compose plugin, Nginx, Certbot).
- `deploy/aws/nginx-svvdthorur.conf` — the reverse-proxy config, ready to
  drop in and hand to Certbot.

Everything below is what's left, done from the AWS Console, your terminal
(SSH), and your DNS provider.

## Cost estimate

| Item | Cost |
|---|---|
| EC2 `t3.micro` or `t4g.micro` (1 vCPU/AWS Graviton, 1GB RAM) | **Free** for 12 months on a new AWS account (750 hrs/month), then ~$6-8/month (`t4g.micro` is cheaper than `t3.micro` — Graviton/ARM). Since our Docker images (`python:3.11-slim`, `node:18-alpine`) build fine on ARM, `t4g.micro` is the better long-term default. |
| EBS storage (20-30GB gp3) | Free tier covers 30GB for 12 months, then ~$2-3/month |
| Elastic IP | Free while attached to a running instance |
| Data transfer | First 100GB/month outbound free (Always Free); at 1-2k users you won't get near this |
| TLS certificate (Let's Encrypt via Certbot) | Free |

**Total: $0 for the first 12 months, then roughly $8-11/month.** Compare
that to Railway's per-service metered billing for the same three
always-on pieces (Postgres + backend + frontend), which usually lands
higher for an always-on setup. No managed RDS here — Postgres runs in the
same docker-compose stack on the instance, which is both simpler and
avoids RDS's separate (and pricier) billing.

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

At whichever registrar/DNS provider manages `svvdthorur.org` (I don't have
access to that account):

- `A` record: `svvdthorur.org` → the Elastic IP
- `A` record (or `CNAME`): `www.svvdthorur.org` → the Elastic IP (or
  `svvdthorur.org` if your provider allows a CNAME-like ALIAS at the apex)

Wait for propagation (`dig svvdthorur.org` should return the Elastic IP)
before issuing the TLS certificate in step 5 — Let's Encrypt validates
ownership by connecting to the domain.

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

## 6. Verify

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
