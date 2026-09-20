# Deployment Guide

## Overview

This guide covers deploying the Temple Management Platform in both **development** and **production** environments.

---

## Prerequisites

### All Environments

- Docker and Docker Compose installed
- Git repository cloned
- Appropriate branch checked out

### Production Only

- Secure server with Docker
- Domain name configured (e.g., `svvdthorur.org`)
- SSL/TLS certificates (for HTTPS)
- Secure environment variables set

---

## Development Deployment

### 1. Setup

```bash
# Clone repository
git clone <repository-url>
cd temple-platform

# Checkout development branch
git checkout development

# Copy environment example (if needed)
cp backend/.env.development backend/.env.local
```

### 2. Configure Environment

Edit `backend/.env.development` if needed:

```bash
ENV=development
DEBUG=true
DATABASE_URL=postgresql://templeuser:templepass@postgres:5432/templedb
SECRET_KEY=dev-secret-key-change-this-in-production-12345678
SQLALCHEMY_ECHO=true
LOG_LEVEL=DEBUG
ENABLE_DOCS=true
ALEMBIC_CONFIG=alembic.dev.ini
```

### 3. Start Services

```bash
# Build and start all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Or run in detached mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### 4. Verify Deployment

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Frontend:** http://localhost:3000
- **Health Check:** http://localhost:8000/health

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Database only
docker-compose logs -f postgres
```

### 6. Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop and remove volumes (WARNING: deletes database)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

---

## Production Deployment

### 1. Prepare Environment

```bash
# On production server
git clone <repository-url>
cd temple-platform

# Checkout production branch
git checkout production
```

### 2. Configure Environment

Create `backend/.env.production` with **SECURE** values:

```bash
ENV=production
DEBUG=false

# Database - USE STRONG PASSWORD
DATABASE_URL=postgresql://templeuser:STRONG_RANDOM_PASSWORD@postgres:5432/templedb
POSTGRES_DB=templedb
POSTGRES_USER=templeuser
POSTGRES_PASSWORD=STRONG_RANDOM_PASSWORD

# Security - GENERATE SECURE SECRET KEY
SECRET_KEY=GENERATE_A_SECURE_RANDOM_SECRET_KEY_HERE

# CORS - YOUR DOMAIN ONLY
CORS_ORIGINS=https://svvdthorur.org

# Database
SQLALCHEMY_ECHO=false
LOG_LEVEL=WARNING

# API Documentation - DISABLED
ENABLE_DOCS=false

# Alembic
ALEMBIC_CONFIG=alembic.prod.ini

# Security
ENABLE_SECURITY_HEADERS=true
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
```

**CRITICAL:** Generate secure values:

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

**The backend refuses to start in production** if `SECRET_KEY` is empty, shorter
than 32 characters, or one of the placeholder values that appear in this repo's
examples. That is intentional: a published key lets anyone forge admin tokens.

**Client IP / rate limiting.** Login, contact, booking and visitor-tracking limits
are keyed on the client IP, so the backend must know how many reverse proxies sit in
front of it:

```bash
# Nginx -> backend (the setup in section 6): 1   (default in docker-compose.prod.yml)
# Nginx -> Next.js -> backend (all traffic through Next's /api rewrite): 2
TRUSTED_PROXY_HOPS=1
```

Too high and the header can be spoofed to dodge limits; too low and every visitor
shares one bucket (the proxy's IP) and can lock each other out. Limits are held in
memory per worker process, so keep `--workers` small (the prod compose uses 2) and
expect them to reset on restart.

### 3. Check Migrations

```bash
# CRITICAL: Ensure single migration head
cd backend
alembic -c alembic.prod.ini heads

# If multiple heads, merge them first in development!
```

### 4. Build and Deploy

```bash
# Build images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor startup
docker-compose logs -f backend
```

### 5. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Verify /docs is disabled (should return 404)
curl http://localhost:8000/docs

# Check frontend
curl http://localhost:3000
```

### 6. Setup Reverse Proxy (Nginx)

Example Nginx configuration for HTTPS:

```nginx
server {
    listen 80;
    server_name svvdthorur.org;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name svvdthorur.org;

    ssl_certificate /etc/ssl/certs/svvdthorur.org.crt;
    ssl_certificate_key /etc/ssl/private/svvdthorur.org.key;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`docker-compose.yml` publishes the backend and frontend on `127.0.0.1` only, so the
proxy is the only way in from the internet. Do not change these to `0.0.0.0`.

---

## Running the Backend Tests

Tests need a real PostgreSQL (the schema uses ARRAY and native enum types, so SQLite
will not work). They build the schema with `alembic upgrade head`, so a missing
migration fails the suite.

```bash
cd backend
pip install -r requirements-dev.txt
# Optional; default is postgresql://templeuser:templepass@localhost:5432/templedb_test
export TEST_DATABASE_URL=postgresql://templeuser:templepass@localhost:5432/templedb_test
pytest
```

---

## Database Migrations

### Development

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current revision
alembic current

# Check migration heads
alembic heads
```

> **Existing databases:** revision `002_remaining_schema` creates the tables that were
> previously missing from the migration history (contact messages, festivals, poojas,
> temples, visitor logs, income/expense, gallery, seva tickets) and adds receipt
> columns to `donors`. It skips anything that already exists, but take a backup
> (`pg_dump`) before the first upgrade on a live database.

### Production

```bash
# ALWAYS test migrations in development first!

# On production server
cd backend

# Check current state
alembic -c alembic.prod.ini current

# Check for multiple heads (CRITICAL)
alembic -c alembic.prod.ini heads

# Apply migrations
alembic -c alembic.prod.ini upgrade head

# Restart services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart backend
```

---

## Updating Production

### Standard Update (No Breaking Changes)

```bash
# On production server
cd temple-platform

# Pull latest from production branch
git checkout production
git pull

# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Monitor logs
docker-compose logs -f backend
```

### Update with Migrations

```bash
# Pull latest code
git checkout production
git pull

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Apply migrations manually (safer)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backend alembic -c alembic.prod.ini upgrade head

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Verify
docker-compose logs -f backend
```

---

## Rollback Procedures

### Rollback Code

```bash
# Find the previous tag
git tag -l

# Checkout previous version
git checkout v1.0.0

# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Rollback Database Migration

```bash
# Check current revision
alembic -c alembic.prod.ini current

# Rollback to specific revision
alembic -c alembic.prod.ini downgrade <revision_id>

# Or rollback one step
alembic -c alembic.prod.ini downgrade -1

# Restart services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart backend
```

---

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f backend
```

### Check Service Status

```bash
# List running containers
docker-compose ps

# Check resource usage
docker stats
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U templeuser -d templedb

# Backup database
docker-compose exec postgres pg_dump -U templeuser templedb > backup.sql

# Restore database
docker-compose exec -T postgres psql -U templeuser -d templedb < backup.sql
```

---

## Troubleshooting

### Backend Won't Start

**Check logs:**
```bash
docker-compose logs backend
```

**Common issues:**
- Migration validation failed (multiple heads)
- Database connection failed
- Missing environment variables
- Port already in use

### Frontend Can't Connect to Backend

**Check:**
1. Backend is running: `curl http://localhost:8000/health`
2. CORS configuration in `.env.production`
3. Network connectivity between containers

### Database Connection Failed

**Check:**
1. PostgreSQL is running: `docker-compose ps postgres`
2. Database credentials in `.env.production`
3. Database is healthy: `docker-compose exec postgres pg_isready`

### Migration Validation Failed

**Error:** "Multiple migration heads detected"

**Solution:**
```bash
# In development
git checkout development
cd backend
alembic heads
alembic merge <head1> <head2>
git add .
git commit -m "db: merge migration heads"

# Merge to production
git checkout production
git merge development
```

---

## Security Checklist

### Before Production Deployment

- [ ] Changed `SECRET_KEY` to secure random value (32+ characters; the app won't start otherwise)
- [ ] `TRUSTED_PROXY_HOPS` matches your proxy chain (default `1`)
- [ ] Backend/frontend ports not reachable from outside the server (only Nginx on 80/443)
- [ ] Changed `POSTGRES_PASSWORD` to strong password
- [ ] Set `DEBUG=false`
- [ ] Set `ENABLE_DOCS=false`
- [ ] Configured strict `CORS_ORIGINS`
- [ ] Enabled security headers
- [ ] Enabled rate limiting
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured
- [ ] Regular backups scheduled

---

## Quick Reference

| Task | Development | Production |
|------|-------------|------------|
| Start | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up` | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d` |
| Stop | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml down` | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml down` |
| Logs | `docker-compose logs -f` | `docker-compose logs -f` |
| Rebuild | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build` | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` |
| Migrations | `alembic upgrade head` | `alembic -c alembic.prod.ini upgrade head` |

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review troubleshooting section above
3. Check `BRANCHING_STRATEGY.md` for workflow guidance
4. Verify environment variables are set correctly
