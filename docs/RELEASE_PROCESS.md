# Cutting a release

This is the concrete checklist. For the *why* behind the two-branch model
(what's different between `development` and `production`, dev-only
middleware, single-Alembic-head enforcement in production, etc.), see
[../BRANCHING_STRATEGY.md](../BRANCHING_STRATEGY.md) - this file is the
short version you actually run through.

## What deploys, and from where

Only pushes to `development` trigger anything (`.github/workflows/deploy.yml`):
backend pytest + frontend typecheck/test run first, and only on success does
the workflow SSH into the EC2 host and redeploy. Pushing to `production`
does **not** independently trigger a deploy - `production` is a
record-keeping branch marking what's actually live, kept in sync with
`development` at release time. If that ever needs to change (e.g. a real
blue/green setup), update this file and `deploy.yml` together.

## Steps

1. **Land the work on `development` first**, the normal way: a short-lived
   `feature/...` branch, merged `--no-ff`, with the full backend pytest
   suite and the frontend typecheck/lint/test/build sequence run on the
   merge result before pushing (see the root README's "Running tests"
   section for the exact commands). Push `development` - this is what
   actually goes live.
2. **Check the deploy succeeded** (GitHub Actions on the push, or `curl
   https://svvdthorur.org/health`) before cutting a release from it - never
   tag a commit whose deploy you haven't confirmed.
3. **Check for multiple Alembic heads**:
   ```bash
   cd backend && alembic heads
   ```
   Production enforces a single head at startup - if this prints more than
   one, merge them (`alembic merge <head1> <head2>`) before continuing.
4. **Tag the release** on `development`, following existing tags
   (`v1.0.0`, `v1.0.1`, ...) - semantic-ish, but this project hasn't needed
   to distinguish major/minor/patch strictly yet, so use judgment:
   ```bash
   git tag -a v1.0.1 -m "Release v1.0.1"
   ```
5. **Fast-forward `production` to match `development`**:
   ```bash
   git checkout production
   git merge --ff-only development
   git checkout development
   ```
   This should always be a plain fast-forward - `production` never carries
   commits `development` doesn't have. If it doesn't fast-forward cleanly,
   stop and figure out why before forcing anything; `production` having
   diverged history is a sign something happened outside this process
   (e.g. a hotfix committed directly to `production` - see
   BRANCHING_STRATEGY.md's hotfix flow for how to reconcile that).
6. **Push everything**:
   ```bash
   git push origin development production --tags
   ```
7. **Update [../CHANGELOG.md](../CHANGELOG.md)** with what shipped, under a
   new version heading.
8. Optionally, cut a GitHub Release from the tag for a durable, user-facing
   summary (the CHANGELOG entry is a good starting point for the release
   notes).

## Hotfixes

If something in production needs an emergency fix that can't wait for the
next `development` → `production` cycle, follow BRANCHING_STRATEGY.md's
hotfix flow: branch from `production`, fix, merge to `production` directly
and deploy manually, then **immediately** merge the same hotfix branch into
`development` too, so the fix isn't silently lost on the next regular
release. This should be rare - the norm is always "land on `development`
first."
