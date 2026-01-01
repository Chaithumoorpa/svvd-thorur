---
description: Deploy to development environment
---

# Deploy to Development Environment

This workflow deploys the application to the development environment with full debugging enabled.

## Steps

// turbo-all

1. **Switch to development branch**
   ```bash
   git checkout development
   ```

2. **Pull latest changes**
   ```bash
   git pull origin development
   ```

3. **Stop existing containers**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
   ```

4. **Build and start services**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
   ```

5. **Wait for services to be ready**
   ```bash
   sleep 10
   ```

6. **Check service health**
   ```bash
   curl http://localhost:8000/health
   ```

7. **View logs**
   ```bash
   docker-compose logs --tail=50 backend
   ```

## Verification

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Dev banner should be visible on frontend

## Notes

- Development mode has verbose logging
- SQL queries are echoed to console
- Hot reload is enabled for code changes
- Multiple migration heads are allowed (but should be resolved)
