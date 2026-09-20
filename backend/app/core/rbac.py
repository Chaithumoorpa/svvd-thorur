"""
Role based access control - the single source of truth for who may do what.

Authorization is ALWAYS evaluated on the backend from the roles stored in the
database (never from the JWT payload or anything the frontend sends).
"""
from enum import Enum
from typing import Iterable, Set


class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TRUSTEE = "TRUSTEE"
    STAFF = "STAFF"
    GENERAL_USER = "GENERAL_USER"


class Permission(str, Enum):
    DASHBOARD_VIEW = "dashboard:view"
    CONTENT_WRITE = "content:write"        # announcements, festivals, poojas/sevas, gallery
    TEMPLE_WRITE = "temple:write"          # temple profile + timings
    MESSAGES_MANAGE = "messages:manage"    # contact messages
    TICKETS_MANAGE = "tickets:manage"      # seva tickets: create at counter, scan, list
    MEMBERS_READ = "members:read"
    MEMBERS_WRITE = "members:write"
    DONORS_READ = "donors:read"
    DONORS_WRITE = "donors:write"
    DONATIONS_READ = "donations:read"
    DONATIONS_WRITE = "donations:write"
    FINANCE_READ = "finance:read"
    FINANCE_WRITE = "finance:write"
    USERS_MANAGE = "users:manage"
    AUDIT_READ = "audit:read"


_P = Permission

_ADMIN: Set[Permission] = {
    _P.DASHBOARD_VIEW, _P.CONTENT_WRITE, _P.TEMPLE_WRITE, _P.MESSAGES_MANAGE, _P.TICKETS_MANAGE,
    _P.MEMBERS_READ, _P.MEMBERS_WRITE, _P.DONORS_READ, _P.DONORS_WRITE,
    _P.DONATIONS_READ, _P.DONATIONS_WRITE, _P.FINANCE_READ, _P.FINANCE_WRITE,
}

ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN.value: set(Permission),
    Role.ADMIN.value: _ADMIN,
    Role.TRUSTEE.value: {
        _P.DASHBOARD_VIEW, _P.MEMBERS_READ, _P.DONORS_READ, _P.DONATIONS_READ, _P.FINANCE_READ,
    },
    Role.STAFF.value: {
        _P.DASHBOARD_VIEW, _P.CONTENT_WRITE, _P.MESSAGES_MANAGE, _P.TICKETS_MANAGE,
    },
    Role.GENERAL_USER.value: set(),
}


def permissions_for(roles: Iterable[str] | None) -> Set[Permission]:
    """Union of the permissions of every role the user holds (unknown roles grant nothing)."""
    granted: Set[Permission] = set()
    for role in roles or []:
        granted |= ROLE_PERMISSIONS.get(str(role), set())
    return granted


def has_permission(roles: Iterable[str] | None, permission: Permission) -> bool:
    return permission in permissions_for(roles)
