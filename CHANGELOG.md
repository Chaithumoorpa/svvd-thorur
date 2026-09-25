# CHANGELOG

## [1.0.1] - 2026-09-25

Devotee-facing account features, payment-flow hardening, and the remaining
admin CRUD gaps, all merged since v1.0.0:

### Devotee accounts and booking
- Self-service devotee registration/login, linked to their own seva
  bookings ("My Bookings"); self-service account deletion (unlinks rather
  than orphans their existing tickets), with a Super Admin alert on any
  actor's repeated deletions in a short window
- Email OTP two-factor login for every account with an email on file
  (accounts with none fall back to single-factor, so nobody is locked out)
- 30-minute idle session timeout, with silent activity-based refresh
- A paid seva can now be booked online and paid at the temple counter
  instead of requiring counter-only booking (`PENDING` payment status);
  the scan/check-in flow refuses to admit a ticket with payment still
  pending, and staff can collect payment (recording it to the finance
  ledger) right from the scan screen
- Optional occasion tagging (a birthday, a wedding anniversary, ...) on a
  seva booking or a donation, which sends a personal blessing email once
  the transaction is actually paid for
- Sankashti Chaturthi dates and auto-generated festival announcements
- Devotee email/mobile required at registration; corrected temple name
  spelling (Varasiddhi → Varasidhi) throughout the codebase and emails

### Compliance and communication
- DPDPA-aligned privacy policy, linked from every outbound email and
  printed on the back of every ticket alongside temple conduct rules
- Devotees are emailed when darshan timings change or a new announcement
  is posted (never staff/trustees/admins); the contact-message auto-reply
  now fires on Closed as well as Resolved, using staff's own internal
  notes as the reply body when present

### Admin panel
- Full CRUD everywhere except Finance (deliberately excluded - see
  docs/RBAC_AND_PERMISSIONS.md): Super Admins can delete any user account;
  donations can be deleted (blocked once a receipt has been issued); a
  photo upload button on the Member edit form

### Developer documentation
- New `docs/` developer guide: architecture, RBAC/permissions model, API
  conventions (including the "add a CRUD resource" recipe this release's
  own features followed), and the release process this entry follows

## [Unreleased]

### SVVD 2.0 (see docs/SVVD_2.0_PLAN.md)
- Security: RBAC permission matrix, audit log, closed public data leaks, production config guards, spoof-resistant rate limiting.
- Data: migrations `003_reconcile`/`004_v2_core`, `donations` table, Numeric money, temple profile and timings, public committee.
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
