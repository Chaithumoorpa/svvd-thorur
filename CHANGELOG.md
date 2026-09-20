# CHANGELOG

## [Unreleased]

### SVVD 2.0 (see docs/SVVD_2.0_PLAN.md)
- Security: RBAC permission matrix, audit log, closed public data leaks, production config guards, spoof-resistant rate limiting.
- Data: migrations `002_reconcile`/`003_v2_core`, `donations` table, Numeric money, temple profile and timings, public committee.
- Frontend: server-rendered temple-style public site, rebuilt permission-aware admin, SEO (sitemap, robots, JSON-LD), lint/typecheck enforced in the build.
- Tests: 78 backend + 14 frontend.

### Fixed

#### Backend: Announcements and Members Data Ordering (2026-01-05)

**Issue:** Announcements and Members not aligned properly on UI

**Root Cause:**
- `AnnouncementRepository.get_all_active()` had no ORDER BY clause
- `AnnouncementRepository.get_all()` had no ORDER BY clause
- `MemberRepository.get_all()` had no ORDER BY clause
- Database returned results in random order on each request
- Frontend received unstable data causing UI misalignment and layout issues

**Fix Implemented:**
- Added `order_by(Announcement.created_at.desc())` to announcements queries
  - Newest announcements appear first
  - Consistent with other repositories (seva_tickets, finance, contact)
- Added `order_by(Member.position.asc(), Member.name.asc())` to members query
  - Groups members by role (Trustee → Staff → Volunteer)
  - Alphabetical order within each role group

**Files Changed:**
- `backend/app/repositories/announcement_repo.py`
- `backend/app/repositories/member_repo.py`

**Impact:**
- Frontend now receives data in stable, predictable order
- UI grid/flex layouts calculate correctly
- No more jumping or misaligned content on page refresh
- No schema changes required (uses existing fields)
- No frontend changes needed (problem was backend data)

**Verification:**
```bash
# Test announcements ordering stability
curl http://localhost:8000/api/v1/announcements/ | jq '.[] | {id, created_at}'
# Expected: Same order on multiple requests, newest first

# Test members ordering and grouping
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/temple-members/ | jq '.[] | {position, name}'
# Expected: Grouped by position, alphabetical within groups
```

**Git Branch:** `fix/announcements-members-data-ordering`
**Commit:** `fix(backend): add stable ordering to announcements and members queries`
