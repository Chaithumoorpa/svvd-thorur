# Roles, permissions, and the audit trail

## Roles

Defined in `backend/app/core/rbac.py`. A `User.roles` is a list (usually one
role, but the model allows more) - permissions are the union of every role
held.

| Role | Can do |
|---|---|
| `SUPER_ADMIN` | Everything, including user management and the audit log |
| `ADMIN` | All temple content, donors/donations, finance, members, messages, tickets - everything except managing other users |
| `TRUSTEE` | Read-only: dashboard, members, donors, donations, finance |
| `STAFF` | Content (announcements/festivals/poojas/gallery), contact messages, seva tickets (counter sales, scanning) |
| `GENERAL_USER` | No admin access at all - this is a self-registered devotee account, used only for "My Bookings" and self-service account deletion |

## Permissions

Each `Permission` (`content:write`, `members:write`, `donations:write`,
`finance:write`, `users:manage`, `audit:read`, ...) is checked independently
at the route level via the `require_permission(Permission.X)` FastAPI
dependency - never inferred from a role name in application code. This
means adding a new role, or changing what a role can do, is a one-line
change in `ROLE_PERMISSIONS` and nothing else needs to change.

**Why Finance is handled differently:** `finance:write` exists as its own
permission, separate from `content:write`/`members:write`/etc., and only
`ADMIN`/`SUPER_ADMIN` hold it - `STAFF` does not. Manual finance entries
(as opposed to the automatic income postings from paid tickets/donations)
are deliberately kept out of the general "give everyone CRUD" delegation,
since they're the one place a mistake or a bad actor directly misstates
money the temple has actually received or spent. When extending CRUD
coverage to a new resource, default to the same instinct: read access can
usually be generous, but a *write* permission on money movement should stay
narrow and explicit.

## The audit log

Every mutating admin action is logged via `AuditContext.log(...)`
(a thin wrapper the router calls right after the service method succeeds) or
directly via `AuditService.record(...)` for actions that don't have a
"current admin user" in the usual sense (e.g. a devotee deleting their own
account). Fields: actor, action (`CREATE`/`UPDATE`/`DELETE`/...), entity
type + id, a human-readable summary, and an optional `changes` dict (field
names only for anything containing personal data - see the members example
below).

Two things worth knowing when adding a new audited action:

1. **`actor_id` is nullable and survives the actor's own deletion.** When a
   user deletes their own account, the audit entry is written with
   `actor=None, actor_username=<captured before deletion>` - the row (and
   the username it names) stays queryable in the audit log forever, even
   though the account is gone.
2. **A burst of deletions by the same actor triggers an alert.** `AuditLog`
   entries with `action in {"DELETE", "DELETE_ACCOUNT"}` are counted per
   actor over a rolling window; crossing the threshold emails every active
   Super Admin with an email on file, exactly once per burst (not once per
   deletion past the threshold). This is generic - it fires for *any*
   entity type, so a new delete endpoint gets this protection for free as
   long as it logs with `action="DELETE"`.

Never log a raw password, token, or other secret in `summary` or `changes` -
`AuditService` redacts a fixed set of key names (`password`, `token`,
`qr_token`, ...) but that's a safety net, not a substitute for not passing
them in the first place. For anything containing personal data (a member's
phone/email, say), log which *fields* changed, not their values - see
`update_member`'s audit call for the pattern.
