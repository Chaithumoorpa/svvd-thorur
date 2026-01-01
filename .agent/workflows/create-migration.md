---
description: Create a new Alembic migration safely
---

# Create New Migration

This workflow creates a new Alembic migration with proper safety checks.

## Prerequisites

- [ ] Working in `development` branch
- [ ] Database models updated in code
- [ ] Development environment running

## Steps

// turbo

1. **Ensure you're in development branch**
   ```bash
   git checkout development
   ```

2. **Check current migration status**
   ```bash
   cd backend && alembic heads && cd ..
   ```

3. **If multiple heads exist, merge them first**
   
   If step 2 shows multiple heads:
   ```bash
   cd backend
   alembic merge <head1> <head2>
   cd ..
   ```

4. **Create new migration**
   ```bash
   cd backend
   alembic revision --autogenerate -m "descriptive_migration_name"
   cd ..
   ```

5. **Review the generated migration**
   
   Open the new migration file in `backend/alembic/versions/` and verify:
   - Upgrade operations are correct
   - Downgrade operations are present
   - No unintended changes

6. **Test the migration**
   ```bash
   cd backend
   alembic upgrade head
   cd ..
   ```

7. **Verify database state**
   
   Connect to database and verify changes:
   ```bash
   docker-compose exec postgres psql -U templeuser -d templedb
   ```

8. **Commit the migration**
   ```bash
   git add backend/alembic/versions/*.py
   git commit -m "db: descriptive migration message"
   ```

## Migration Naming Conventions

Use descriptive names that explain what changed:

- ✅ `add_phone_number_to_members`
- ✅ `create_donations_table`
- ✅ `add_index_to_announcements_date`
- ❌ `update_db`
- ❌ `changes`
- ❌ `migration_1`

## Testing Checklist

Before committing:

- [ ] Migration applies cleanly (`alembic upgrade head`)
- [ ] Migration can be rolled back (`alembic downgrade -1`)
- [ ] Application starts without errors
- [ ] Affected features still work
- [ ] No data loss

## Common Issues

### Autogenerate didn't detect changes

**Cause:** Model not imported in `alembic/env.py`

**Solution:** Ensure model is imported in `app/models/__init__.py`

### Multiple heads after creating migration

**Cause:** Concurrent development created conflicting migrations

**Solution:**
```bash
cd backend
alembic merge <head1> <head2>
alembic revision -m "merge migration heads"
cd ..
```

### Migration fails to apply

**Cause:** Database state doesn't match expected state

**Solution:**
1. Check current database schema
2. Manually fix inconsistencies
3. Recreate migration if needed

## Notes

- Always create migrations in `development` branch
- Test migrations before merging to `production`
- Multiple heads are allowed in development but must be merged before production
- Production will fail to start if multiple heads exist
