# API conventions

## Exploring the API

The backend serves interactive Swagger docs at `/docs` (and ReDoc at
`/redoc`) - but **only when `settings.docs_url` is enabled**, which is true
in development and disabled in production (see BRANCHING_STRATEGY.md's
dev/production differences). Run the backend locally and open
`http://localhost:8000/docs` rather than guessing endpoint shapes from the
code.

Every route lives under `/api/v1/...`; `app/api/v1/api.py` is the single
place all the per-resource routers get mounted.

## Pagination

List endpoints that can grow large take `PageParams` (`page`, `page_size`)
via the `page_params` dependency, and reply with `paginate(query, params)` +
`set_total(response, total)`, which sets an `X-Total-Count` response header.
The frontend's `page<T>()` helper (`lib/api.ts`) expects exactly this shape -
match it rather than inventing a different pagination style.

## Standard request lifecycle

```python
@router.post("/things", response_model=ThingOut, status_code=201)
def create_thing(
    payload: ThingCreate,
    service: ThingService = Depends(get_thing_service),
    audit: AuditContext = Depends(get_audit),
    user: User = Depends(require_permission(Permission.THINGS_WRITE)),
):
    thing = service.create(payload, user.id)
    audit.log("CREATE", "thing", thing.id, f"Created thing '{thing.name}'")
    return thing
```

- Validation lives in the Pydantic schema (`app/schemas/thing.py`), not the
  route function. Shared validators (mobile numbers, money bounds, safe
  URLs, blank-string-to-None) live in `app/schemas/common.py` - reuse them
  rather than re-deriving a regex.
- Business rules (can this be deleted? does this field freeze once some
  other thing happens?) live in the service, and raise `HTTPException`
  with the status code the situation calls for (`400` bad input, `404` not
  found, `409` conflict with current state, `503` a transient
  infrastructure failure like "S3 isn't configured").
- The router itself stays a thin composition of: call the service, log the
  audit entry, optionally send an email, return the result. If a route
  function is doing real decision-making, that logic almost always belongs
  one layer down in the service instead.

## Recipe: adding DELETE to an existing resource

This exact pattern was used to add user, donation, and (earlier) seva
ticket deletion - copy it rather than reinventing:

1. **Service**: add a `delete(...)` method. Decide up front: hard delete,
   or "unlink and delete" (keep rows that have independent value - e.g. a
   seva ticket keeps its own devotee name/mobile/email even after the
   booking user's account is deleted; a member row keeps its own data with
   `user_id` set to `NULL`)? Block the delete (`409`) if some later action
   already depends on the record staying immutable (a receipt already
   issued, a receipt-frozen donation amount, etc.) - check for an existing
   guard like this on the resource's `update()` method first, since a
   delete guard usually mirrors it.
2. **Router**: `DELETE /{id}`, gated by the resource's own `*_WRITE`/`*_MANAGE`
   permission (never a broader one), `audit.log("DELETE", "<entity_type>", id, ...)`
   after the service call succeeds.
3. **Tests**: happy path, permission denied, the specific guard(s) from
   step 1, and (if the entity links to something else) that the link is
   unlinked/cleaned up rather than left dangling.
4. **Frontend**: `deleteX(id)` in `lib/api.ts`, a delete button + the shared
   `ConfirmDialog` component (see `admin/users/page.tsx` or
   `admin/donations/page.tsx` for the pattern), gated on the same
   permission via `useAuth().can('resource:action')`.

## Email conventions

- Every outbound email goes through `EmailService` (`send` for a specific
  recipient, `notify_admin` for the temple's own inbox) - never call SES
  directly from a router or service.
- A mail failure is logged, never raised - the action that triggered the
  email must succeed regardless of whether the email actually sent.
- When adding a new "notify devotees" trigger (a new content type that
  should announce itself), reuse `notify_devotees()`
  (`app/services/notification_service.py`) rather than writing a new
  "who counts as a devotee" query - that's the one place that decision is
  made, and it should stay that way.
