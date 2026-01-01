# Git Branching Strategy

## Overview

This project uses a **two-branch strategy** to separate development and production environments:

- **`development`** - Active development, debugging, experimentation
- **`production`** - Stable, production-ready code only

This strategy ensures:
- ✅ Bugs are caught early in development
- ✅ Production remains stable and predictable
- ✅ Alembic migration conflicts are prevented
- ✅ Clear separation of debug tools and production hardening

---

## Branch Structure

```
development (default branch)
    ↓
    ↓ (merge after testing & tagging)
    ↓
production (deployment branch)
```

### Development Branch

**Purpose:** All active development work happens here.

**Characteristics:**
- Debug mode enabled
- Verbose logging (DEBUG level)
- SQLAlchemy echo enabled
- `/docs` and `/redoc` available
- Relaxed CORS (localhost allowed)
- Request/response logging
- SQL query timing
- Multiple Alembic heads allowed (but should be resolved)

**When to use:**
- Feature development
- Bug fixes
- Experimentation
- Migration creation
- Testing

### Production Branch

**Purpose:** Stable, production-ready code only.

**Characteristics:**
- Debug mode disabled
- Minimal logging (WARNING level)
- SQLAlchemy echo disabled
- `/docs` and `/redoc` **DISABLED**
- Strict CORS (domain-only)
- Security headers enabled
- Rate limiting enabled
- **Single Alembic head enforced** (startup fails if multiple heads)

**When to use:**
- Deployments
- Releases
- Hotfixes (with special care)

---

## Workflow

### 1. Daily Development

```bash
# Always work in development branch
git checkout development

# Create feature branch (optional)
git checkout -b feature/my-feature

# Make changes, commit regularly
git add .
git commit -m "feat: add new feature"

# Merge back to development
git checkout development
git merge feature/my-feature
```

### 2. Testing Before Production

```bash
# In development branch
git checkout development

# Test with development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Verify:
# - All features work
# - Migrations apply cleanly
# - No errors in logs
# - Announcements & Members CRUD works
```

### 3. Creating a Release

```bash
# Ensure development is clean
git checkout development
git status

# Check for multiple migration heads
alembic heads

# If multiple heads exist, merge them:
alembic merge <head1> <head2>
alembic revision -m "merge migration heads"

# Tag the release
git tag -a v1.0.0 -m "Release v1.0.0"

# Merge to production
git checkout production
git merge development

# Push both branches and tags
git push origin development production --tags
```

### 4. Deploying to Production

```bash
# On production server
git checkout production
git pull

# Deploy with production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose logs -f backend
```

### 5. Hotfixes (Emergency Production Fixes)

```bash
# Create hotfix branch from production
git checkout production
git checkout -b hotfix/critical-bug

# Fix the bug
git add .
git commit -m "fix: critical production bug"

# Merge to production
git checkout production
git merge hotfix/critical-bug

# Deploy immediately
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# IMPORTANT: Merge back to development
git checkout development
git merge hotfix/critical-bug
```

---

## Commit Discipline

Use **semantic commit prefixes** to maintain clear history:

### Required Prefixes

- `feat:` - New features
- `fix:` - Bug fixes
- `db:` - Database migrations or schema changes
- `dev:` - Development-only tooling
- `prod:` - Production hardening
- `chore:` - Infrastructure, Docker, dependencies
- `docs:` - Documentation updates
- `refactor:` - Code refactoring (no behavior change)
- `test:` - Test additions or modifications

### Examples

```bash
git commit -m "feat: add member search functionality"
git commit -m "fix: resolve announcements CRUD network issue"
git commit -m "db: add temple_members table migration"
git commit -m "dev: add request logging middleware"
git commit -m "prod: enable security headers"
git commit -m "chore: update Docker Compose for dev/prod split"
```

### Rules

❌ **DO NOT:**
- Commit directly to `production`
- Mix multiple concerns in one commit
- Use vague messages like "fix stuff" or "updates"
- Commit broken code to `development`

✅ **DO:**
- Commit frequently with clear messages
- Keep commits focused on one thing
- Test before committing
- Use descriptive commit messages

---

## Migration Management

### Development

```bash
# Create new migration
alembic revision --autogenerate -m "add new field to members"

# Check migration heads (multiple allowed in dev)
alembic heads

# Apply migrations
alembic upgrade head
```

### Before Production

```bash
# CRITICAL: Ensure single migration head
alembic heads

# If multiple heads exist:
alembic merge <head1> <head2>
alembic revision -m "merge migration heads"

# Test the merged migration
alembic upgrade head
```

### Production

- **Startup will fail** if multiple migration heads exist
- Always merge migration branches before deploying
- Test migrations in development first

---

## Environment Variables

### Development

Located in `backend/.env.development`:
- `ENV=development`
- `DEBUG=true`
- `SQLALCHEMY_ECHO=true`
- `ENABLE_DOCS=true`

### Production

Located in `backend/.env.production`:
- `ENV=production`
- `DEBUG=false`
- `SQLALCHEMY_ECHO=false`
- `ENABLE_DOCS=false`
- `ENABLE_SECURITY_HEADERS=true`
- `ENABLE_RATE_LIMITING=true`

**IMPORTANT:** Never commit `.env.development` or `.env.production` to Git!

---

## Troubleshooting

### Multiple Migration Heads in Production

**Symptom:** Production startup fails with "Multiple migration heads detected"

**Solution:**
```bash
# In development
git checkout development
alembic heads  # See the heads
alembic merge <head1> <head2>
alembic revision -m "merge migration heads"
alembic upgrade head

# Test, then merge to production
git add .
git commit -m "db: merge migration heads"
git checkout production
git merge development
```

### CORS Errors in Production

**Symptom:** Frontend can't connect to backend in production

**Solution:**
- Ensure `CORS_ORIGINS` in `.env.production` includes your domain
- Example: `CORS_ORIGINS=https://svvdthorur.org`

### /docs Not Available

**Development:** Should be available at `http://localhost:8000/docs`

**Production:** Intentionally disabled for security. Use development environment for API exploration.

---

## Quick Reference

| Task | Command |
|------|---------|
| Switch to development | `git checkout development` |
| Switch to production | `git checkout production` |
| Start dev environment | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up` |
| Start prod environment | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d` |
| Check migration heads | `alembic heads` |
| Create migration | `alembic revision --autogenerate -m "description"` |
| Apply migrations | `alembic upgrade head` |
| Tag release | `git tag -a v1.0.0 -m "Release v1.0.0"` |
| Merge to production | `git checkout production && git merge development` |

---

## Summary

1. **All work happens in `development`**
2. **Test thoroughly before merging to `production`**
3. **Always resolve migration conflicts before production**
4. **Use semantic commit messages**
5. **Tag releases before deploying**
6. **Never commit directly to `production`**

Following this strategy will keep your codebase clean, your deployments safe, and your production environment stable.
