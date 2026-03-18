---
title: "Parametric Docker images with runtime configuration and registry publish"
status: applied
author: "user"
created-at: "2026-03-17T00:00:00.000Z"
---

# CR-008: Parametric Docker Images with Runtime Config and Registry Publish

## Summary

Introduce a parameter-driven container strategy that covers both:

1. Build and publish backend/frontend images to a Docker-compatible registry (Docker Hub, GHCR, or private registry).
2. Runtime configuration injection so the same image can run across environments by passing parameters (for example: domain name, OAuth settings, API URLs, and secrets).

## Motivation

Current deployment workflows rely on local `docker-compose` and manual image handling. This CR defines a standard way to produce reproducible, versioned images, publish them to a registry, and run them in any environment through explicit runtime parameters instead of rebuilding per environment.

## Requirements

### Functional requirements

1. Build backend and frontend images from `code/backend/Dockerfile` and `code/frontend/Dockerfile`.
2. Parameterize image publishing via environment variables or workflow inputs:
   - `REGISTRY` (example: `ghcr.io`, `docker.io`, `registry.company.com`)
   - `IMAGE_NAMESPACE` (example: `org-or-user`)
   - `IMAGE_NAME_BACKEND` (default: `sdd-flow-backend`)
   - `IMAGE_NAME_FRONTEND` (default: `sdd-flow-frontend`)
   - `IMAGE_TAG` (example: `latest`, `main-<sha>`, release tag)
3. Support both single-tag and multi-tag publishing (`latest`, commit SHA, semantic version).
4. Publish images only when credentials are available and branch/tag conditions match policy.
5. Keep local development workflow with `docker-compose` unchanged.
6. Define a runtime configuration contract for application startup, including:
   - public domain and URL settings (`APP_DOMAIN`, `FRONTEND_URL`)
   - OAuth settings matching current provider integration (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`)
   - auth/signing settings (`JWT_SECRET`, optional cookie policy flags)
   - database and service connectivity (`DATABASE_URL`, optional upstream host for frontend proxy)
   - Sensitive values via secrets (OAuth secret, JWT secret, API tokens)
7. Ensure no environment-specific secrets are baked into image layers.
8. Support parameter delivery through `.env`, compose env vars, and CI/CD deployment variables.

### Non-functional requirements

1. Builds must be deterministic and use build cache where possible.
2. Workflow must avoid credential leakage in logs.
3. Published images must include OCI labels (`revision`, `source`, `created`).
4. The process should be reusable for future services.
5. Startup must fail fast with clear errors when required runtime parameters are missing.

## Runtime Parameter Model

### Canonical variable mapping and compatibility

To avoid breaking existing deployments, this CR must define canonical names and compatibility aliases.

- Backend canonical names for this project: `DATABASE_URL`, `JWT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `FRONTEND_URL`
- If new names are introduced (for example `APP_DOMAIN`), they must be mapped to existing names with explicit precedence rules.
- Precedence rule: if both `APP_DOMAIN` and `FRONTEND_URL` are provided, `FRONTEND_URL` wins; if only `APP_DOMAIN` is provided, derive `FRONTEND_URL=https://<APP_DOMAIN>` unless overridden.
- Backward compatibility window: keep old names working for at least one release cycle and emit clear deprecation warnings.

### Backend required runtime params

- `DATABASE_URL`
- `JWT_SECRET`
- `FRONTEND_URL`
- OAuth params required by current auth mode (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`)
- OAuth access tokens are obtained dynamically during OAuth flows and must not be treated as static environment parameters.
- Optional hardening flags to avoid auth side effects across environments:
  - `AUTH_COOKIE_SECURE` (true in HTTPS environments)
  - `AUTH_COOKIE_SAMESITE` (`lax` by default, configurable if cross-site auth is required)

### Frontend required runtime params

- `NGINX_SERVER_NAME` (default `_`)
- `BACKEND_UPSTREAM` (default `backend:8000` for compose)
- Optional `PUBLIC_APP_DOMAIN` if surfaced in UI runtime config

### Frontend runtime strategy (mandatory)

- Do not rely on Vite build-time variables for environment-specific deploy values.
- Use runtime injection for static frontend image (for example, entrypoint script + template + generated `config.js` or `env.js`).
- NGINX proxy target and domain-facing values must be configurable at container startup without rebuilding the image.

### Secret handling rules

- Secrets must be injected at runtime via environment variables or secret manager integration.
- Do not place secrets in Dockerfile `ARG` defaults, committed `.env` files, or static frontend bundles.
- Provide `.env.example` files documenting required keys without sensitive values.
- Add startup preflight validation (`validate-env`) that fails fast and lists missing required variables by name.

## Changes Required

### New documentation: `system/ci-pipeline.md`

Add a section for container build/publish pipeline:

- Workflow name and trigger conditions (push, tags, manual dispatch)
- Registry authentication strategy (GitHub token or registry secrets)
- Parameter contract for image naming and tags
- Branch/tag rules for publication (for example: `main` and version tags)
- How runtime parameters and secrets are provided during deploy (not at build time)

### Update `system/architecture.md`

Document container artifact flow:

- Source -> CI build -> Registry -> Deploy environment
- Backend and frontend images versioned independently or together
- Promotion strategy (`dev` -> `staging` -> `prod`) through tags
- Runtime config boundary: immutable image + environment-provided parameters

### Update `system/interfaces.md`

Document environment configuration interface:

- Required and optional runtime variables for backend and frontend
- Canonical name -> alias mapping and precedence behavior
- Validation rules and startup failure behavior when variables are missing
- Which values are public config vs secrets

### Update `system/tech-stack.md`

Add infrastructure row for container registry and image tooling:

- `docker/build-push-action` (or equivalent)
- Registry provider in use (GHCR or Docker Hub)

### New workflow file: `code/.github/workflows/docker-publish.yml`

Implement a CI workflow with:

1. Input parameters for registry/namespace/tag strategy.
2. Login step using secrets (`REGISTRY_USERNAME`, `REGISTRY_PASSWORD` or token).
3. Metadata/tag generation (`docker/metadata-action`).
4. Build and push backend image.
5. Build and push frontend image.
6. Optional dry-run mode for PR validation (build without push).
7. Optional validation step that checks required deploy-time parameter names are documented and that example/template files are complete.

### Optional compose enhancements: `code/docker-compose.yml`

Add optional image name parameter support for parity with CI output:

- Use variables for image names/tags when `image:` is defined.
- Keep `build:` config for local developer experience.
- Add explicit `environment:` mapping for required runtime parameters (domain, OAuth, API URLs) using variable expansion.
- Add safe defaults only for local development; production-like compose overlays must require explicit secrets.

### New examples/config docs

- `code/backend/.env.example` with non-secret placeholders.
- `code/frontend/.env.example` with non-secret placeholders.
- Optional deploy template (for example `code/deploy/env.template`) listing all required variables.

## Implementation Plan

1. Define image naming standard.
   - Format: `${REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}`
   - Decide default tags for branch builds and releases.
2. Create workflow skeleton.
   - Add triggers: push to `main`, tags `v*`, and manual dispatch.
   - Add permissions required for registry publishing.
3. Add secure auth and metadata generation.
   - Use repository secrets and avoid echoing credentials.
   - Generate deterministic tags/labels from git context.
4. Build and publish backend/frontend images.
   - Reuse common steps where possible.
   - Enable BuildKit cache for faster runs.
5. Validate workflow behavior.
   - PR: build only (no push).
   - `main`: push branch/sha tags.
   - release tag: push semantic version + latest (if policy allows).
6. Define runtime parameter contract.
   - List required variables for backend/frontend and classify secret vs non-secret.
   - Add `.env.example` files and deployment variable template.
7. Implement runtime validation.
   - Backend startup validates required variables and fails with actionable errors.
   - Frontend runtime/env injection strategy implemented, documented, and verified.
   - Validate canonical/alias precedence and deprecation warnings.
8. Update architecture, interfaces, and CI docs.
   - Document build-time vs run-time variable boundaries.
9. Smoke test deployment consumption.
   - Pull produced image tags and run with environment-specific params (domain, OAuth, tokens) without rebuilding images.

## Acceptance Criteria

1. Running the publish workflow on allowed branches/tags pushes both backend and frontend images to the configured registry.
2. Image names and tags can be changed without editing workflow code, only via inputs/variables.
3. PR workflow path builds successfully without publishing.
4. Documentation clearly describes how to configure registry credentials, naming, and tagging rules.
5. Existing local `docker-compose up` developer workflow continues to work.
6. A single built image can be deployed to at least two environments by changing only runtime parameters (for example: different domains and OAuth values).
7. Missing required runtime params produce clear startup errors.
8. No secrets are present in built image history or committed configuration files.
9. Existing variable names (`JWT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `FRONTEND_URL`) remain supported during compatibility window.
10. Frontend image can switch backend upstream/domain behavior through runtime env vars only (no rebuild).

## Risks and Mitigations

- Incorrect tag policy may overwrite stable images.
  - Mitigation: explicit release-tag rules and protected `latest` policy.
- Registry rate limits or auth failures may break pipeline reliability.
  - Mitigation: retries, authenticated pulls, and clear runbook docs.
- Drift between local compose images and CI-published images.
  - Mitigation: shared naming variables and documented mapping.
- Misconfigured runtime variables (domain/OAuth/token) can break authentication or routing.
  - Mitigation: strict startup validation and `.env.example` templates.
- Variable rename drift can silently break deployments.
  - Mitigation: canonical mapping table, alias precedence tests, and deprecation warnings.
- Cookie security settings can cause login failures or insecure behavior between HTTP and HTTPS environments.
  - Mitigation: explicit `AUTH_COOKIE_SECURE` and `AUTH_COOKIE_SAMESITE` runtime parameters with environment-specific defaults.

## Rollout Notes

1. First rollout can target a non-production namespace.
2. Verify image pull and startup in staging.
3. Promote by tagging a release once validated.
