# Developer documentation

This folder is the starting point for anyone working on the SVVD Thorur
codebase. It's repo-only reference material for developers — not published
anywhere on svvdthorur.org.

## Start here

- [../README.md](../README.md) — what the project is, tech stack, local setup with Docker, running tests
- [ARCHITECTURE.md](./ARCHITECTURE.md) — how the backend and frontend are put together, request flow, background jobs
- [RBAC_AND_PERMISSIONS.md](./RBAC_AND_PERMISSIONS.md) — roles, permissions, the audit log, why Finance is handled differently
- [API_CONVENTIONS.md](./API_CONVENTIONS.md) — how routers/services/schemas are structured, and the recipe for adding a new admin CRUD resource
- [RELEASE_PROCESS.md](./RELEASE_PROCESS.md) — how a release actually gets cut and deployed

## Deployment and infrastructure

These live at the repo root, not here, since they're referenced from CI and
ops scripts by path:

- [../BRANCHING_STRATEGY.md](../BRANCHING_STRATEGY.md) — the `development` → `production` branch model
- [../DEPLOY_AWS.md](../DEPLOY_AWS.md) — the current production infrastructure (single EC2 instance, Docker Compose, S3, SES) and how `deploy.yml` deploys it
- [../DEPLOYMENT.md](../DEPLOYMENT.md) / [../DEPLOY_RAILWAY.md](../DEPLOY_RAILWAY.md) — earlier/alternative deployment notes, kept for reference
- [../CHANGELOG.md](../CHANGELOG.md) — what shipped in each release

## History

- [SVVD_2.0_PLAN.md](./SVVD_2.0_PLAN.md) — the design plan for the SVVD 2.0 rebuild (RBAC, audit log, donations, the rebuilt public site and admin panel). Historical; the codebase has moved on since, but it explains *why* several foundational decisions were made.
