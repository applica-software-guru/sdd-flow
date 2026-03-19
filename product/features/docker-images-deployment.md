---
title: "Docker Images Deployment"
status: synced
author: ""
last-modified: "2026-03-18T00:00:00.000Z"
version: "1.0"
---

# Docker Images Deployment

## Overview

SDD Flow can run directly from prebuilt container images published in Google Artifact Registry (GAR), without cloning code or building locally.

This feature explains a standard `docker-compose.yml` pattern to run backend + frontend using:

- `vX.Y.Z` for official release versions
- `latest` for the most recent stable publish
- `rev-<short-sha>` for a deterministic revision rollout/rollback

## Image Naming Convention

Images are published to:

- `europe-west1-docker.pkg.dev/s-dd-490608/sdd-flow/sdd-flow-backend:<tag>`
- `europe-west1-docker.pkg.dev/s-dd-490608/sdd-flow/sdd-flow-frontend:<tag>`

Supported tags:

- `vX.Y.Z` (release tags)
- `latest`
- `rev-<short-sha>` (example: `rev-19eb1e5`)

Version mapping contract:

- A single canonical `${VERSION}` is produced by `.github/workflows/docker-publish.yml` for each publish run.
- Backend and frontend images always share the same `${VERSION}`.
- `${VERSION}` precedence is: manual `image_tag` input -> git tag name (`v*`) -> `rev-<short-sha>`.

## Sample Docker Compose

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sddflow
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d sddflow"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    image: europe-west1-docker.pkg.dev/s-dd-490608/sdd-flow/sdd-flow-backend:${IMAGE_TAG:-latest}
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/sddflow
      JWT_SECRET: ${JWT_SECRET}
      FRONTEND_URL: ${FRONTEND_URL:-http://localhost:5173}
      ENABLE_GOOGLE_OAUTH: ${ENABLE_GOOGLE_OAUTH:-false}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:-}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET:-}
      GOOGLE_REDIRECT_URI: ${GOOGLE_REDIRECT_URI:-http://localhost:8000/api/v1/auth/google/callback}
      AUTH_COOKIE_SECURE: ${AUTH_COOKIE_SECURE:-false}
      AUTH_COOKIE_SAMESITE: ${AUTH_COOKIE_SAMESITE:-lax}
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"

  frontend:
    image: europe-west1-docker.pkg.dev/s-dd-490608/sdd-flow/sdd-flow-frontend:${IMAGE_TAG:-latest}
    environment:
      NGINX_SERVER_NAME: ${NGINX_SERVER_NAME:-_}
      BACKEND_UPSTREAM: ${BACKEND_UPSTREAM:-backend:8000}
      PUBLIC_APP_DOMAIN: ${PUBLIC_APP_DOMAIN:-}
    depends_on:
      - backend
    ports:
      - "5173:80"

volumes:
  db_data:
```

## Runtime Configuration

Required for production-like usage:

- `JWT_SECRET`
- `DATABASE_URL` (if not using the local `db` service)
- `FRONTEND_URL`

Optional OAuth:

- `ENABLE_GOOGLE_OAUTH=true`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

## Runbook

1. Create `.env` with runtime values (at minimum `JWT_SECRET`).
2. Choose the release tag:
  - `IMAGE_TAG=vX.Y.Z` for an official release
  - `IMAGE_TAG=latest` for most recent stable release
  - `IMAGE_TAG=rev-<short-sha>` for pinned revision
3. Start services:

```bash
docker compose up -d
```

4. Verify:

```bash
curl -s http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

## Rollback Strategy

To rollback, run the same compose file with a previous revision tag:

```bash
IMAGE_TAG=rev-19eb1e5 docker compose up -d
```

This keeps deployment immutable and reproducible.

## Notifications and Upgrade Awareness

Users can track new versions through:

1. GitHub Releases watch (recommended and always available)
2. Registry/repository notifications where organization settings allow it

When a new release is published, use the same version string in both release notes and image tags (for example `v1.3.0`) to avoid ambiguity.

## Agent Notes

- Keep production credentials in secret managers or CI/CD secret stores, not in committed `.env` files.
- Prefer `rev-<short-sha>` in staging/production for traceability.
- Prefer `vX.Y.Z` in production when following formal releases.
- Use `latest` for local demos and quick smoke tests.
