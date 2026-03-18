---
title: "CI Pipeline"
status: synced
author: ""
last-modified: "2026-03-17T00:00:00.000Z"
version: "1.1"
---

# CI Pipeline

## Overview

GitHub Actions runs frontend and backend tests on every push to `main` and on all pull requests. The two test suites run as **parallel jobs** for fast feedback.

A separate publish workflow builds and pushes immutable backend/frontend images to a container registry, while runtime parameters are injected only at deployment time.

## Workflow File

- `.github/workflows/ci.yml` (tests)
- `.github/workflows/docker-publish.yml` (container publish)

### Triggers

- Push to `main` branch
- All pull requests

For `.github/workflows/docker-publish.yml`:

- Push to `main` (publish branch/sha tags)
- Version tags `v*` (publish release tags)
- `workflow_dispatch` (manual runs with parameters)

## Jobs

### `backend-tests`

| Setting | Value |
|---------|-------|
| Runner | `ubuntu-latest` |
| Python | 3.12 |
| Package manager | `uv` |
| Test runner | `pytest` |
| Database | PostgreSQL service container |

Steps:
1. Checkout code
2. Set up Python 3.12
3. Install `uv`
4. Install backend dependencies via `uv sync`
5. Run `pytest` with `DATABASE_URL` pointing to the PostgreSQL service container

### `frontend-tests`

| Setting | Value |
|---------|-------|
| Runner | `ubuntu-latest` |
| Node.js | LTS |
| Package manager | `npm` |
| Test runner | Vitest |

Steps:
1. Checkout code
2. Set up Node.js (LTS)
3. Install frontend dependencies via `npm ci`
4. Run `npx vitest run` (single-run mode)

## Container Publish Workflow

### Inputs and parameters

- `REGISTRY` (for example `ghcr.io`, `docker.io`)
- `IMAGE_NAMESPACE`
- `IMAGE_NAME_BACKEND` (default `sdd-flow-backend`)
- `IMAGE_NAME_FRONTEND` (default `sdd-flow-frontend`)
- `IMAGE_TAG` (single tag) or metadata-driven multi-tag policy (`latest`, sha, semver)
- `PUSH_IMAGES` toggle (dry-run builds for PR or manual validation)

Image reference format:

`${REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}`

### Publish jobs

1. Authenticate to registry using secrets (`REGISTRY_USERNAME` + `REGISTRY_PASSWORD` or token).
2. Generate tags and labels using `docker/metadata-action`.
3. Build/push backend image from `backend/Dockerfile`.
4. Build/push frontend image from `frontend/Dockerfile`.
5. Use BuildKit cache (`cache-from`/`cache-to`) to reduce build time.

### Runtime configuration boundary

- CI builds immutable images.
- Environment-specific values (domain, OAuth credentials, JWT secret, DB URL, upstreams) are injected at runtime by deployment tooling.
- CI validates that parameter documentation/templates are complete, but does not store production secrets.

### Required runtime parameters (deployment)

Backend:

- `DATABASE_URL`
- `JWT_SECRET`
- `FRONTEND_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- Optional: `AUTH_COOKIE_SECURE`, `AUTH_COOKIE_SAMESITE`

Frontend (container runtime):

- `NGINX_SERVER_NAME`
- `BACKEND_UPSTREAM`
- Optional: `PUBLIC_APP_DOMAIN`

### Safety checks

- Fail fast on missing required runtime variables at startup (`validate-env` step/entrypoint).
- Never pass secrets via Dockerfile default args.
- Do not commit real secrets in `.env` files; use `.env.example` placeholders only.
