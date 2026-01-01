---
description: Deploy to production environment
---

# Deploy to Production Environment

This workflow deploys the application to the production environment with security hardening.

## Prerequisites

- [ ] All changes tested in development
- [ ] Migration heads merged (single head only)
- [ ] Release tagged
- [ ] Environment variables configured in `.env.production`

## Steps

1. **Switch to production branch**
   ```bash
   git checkout production
   ```

2. **Pull latest changes**
   ```bash
   git pull origin production
   ```

3. **Verify migration heads (CRITICAL)**
   ```bash
   cd backend && alembic -c alembic.prod.ini heads && cd ..
   ```
   
   **STOP if multiple heads detected!** Merge them in development first.

4. **Backup database**
   ```bash
   docker-compose exec postgres pg_dump -U templeuser templedb > backup-$(date +%Y%m%d-%H%M%S).sql
   ```

5. **Stop existing containers**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
   ```

6. **Build production images**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
   ```

7. **Start services**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

8. **Wait for services to be ready**
   ```bash
   sleep 15
   ```

9. **Check service health**
   ```bash
   curl http://localhost:8000/health
   ```

10. **Verify /docs is disabled**
    ```bash
    curl -I http://localhost:8000/docs
    ```
    
    Should return 404 Not Found

11. **Monitor logs for errors**
    ```bash
    docker-compose logs --tail=100 backend
    ```

## Verification

- [ ] Health check returns OK
- [ ] /docs returns 404 (disabled)
- [ ] Frontend loads correctly
- [ ] No errors in backend logs
- [ ] Database migrations applied
- [ ] CORS working for production domain

## Rollback (if needed)

If deployment fails:

```bash
# Stop new containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Checkout previous tag
git checkout <previous-tag>

# Restore database
docker-compose exec -T postgres psql -U templeuser -d templedb < backup-<timestamp>.sql

# Restart with previous version
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Notes

- Production mode has minimal logging (WARNING level)
- /docs and /redoc are disabled for security
- Security headers are enabled
- Rate limiting is active
- Multiple migration heads will cause startup failure
