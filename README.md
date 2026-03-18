# SDD Flow

SDD Flow is a platform to manage software delivery through Story Driven Development (SDD): product intent, system design, change requests, bugs, and implementation all stay connected in one workflow.

## Project Goal

The goal of this project is to make product and engineering collaboration deterministic and traceable.

It helps teams:

- define product intent clearly
- evolve requirements safely through Change Requests
- fix regressions through explicit Bug reports
- keep implementation aligned with documentation
- deploy reproducible containerized releases

## How This Project Was Designed

This repository follows a docs-first, spec-driven model.

The project thinking is structured into layers:

1. Product layer: what to build and for whom
2. System layer: how to build it (architecture, interfaces, entities, stack)
3. Change layer: controlled evolution through CRs
4. Quality layer: bug lifecycle and resolution
5. Delivery layer: implementation in code plus CI/CD and Docker images

A key principle is: documentation and code should evolve together.

## Development Method: Story Driven Development

SDD Flow uses the SDD lifecycle:

- define or update story files
- process pending change requests
- sync implementation tasks
- implement in code
- mark stories as synced

This keeps decisions auditable and reduces requirement drift.

## Deployment Model

The project supports container-based deployment with immutable images and runtime configuration.

Current publishing strategy:

- images are published to Google Artifact Registry
- tags include always latest plus a revision tag based on commit SHA
- both backend and frontend are published as multi-architecture images

## Repository Structure

- Product documentation: [product](product)
- System documentation: [system](system)
- Source code: [code](code)
- Change requests: [change-requests](change-requests)
- Bug reports: [bugs](bugs)
- CI workflows: [.github/workflows](.github/workflows)

## Resource Index

### Product Docs

- Vision: [product/vision.md](product/vision.md)
- Users: [product/users.md](product/users.md)

### Product Features

- API Keys: [product/features/api-keys.md](product/features/api-keys.md)
- Audit Log: [product/features/audit-log.md](product/features/audit-log.md)
- Authentication: [product/features/auth.md](product/features/auth.md)
- Bugs: [product/features/bugs.md](product/features/bugs.md)
- Change Requests: [product/features/change-requests.md](product/features/change-requests.md)
- Dashboard: [product/features/dashboard.md](product/features/dashboard.md)
- Docker Images Deployment: [product/features/docker-images-deployment.md](product/features/docker-images-deployment.md)
- Notifications: [product/features/notifications.md](product/features/notifications.md)
- Projects: [product/features/projects.md](product/features/projects.md)
- SDD Docs: [product/features/sdd-docs.md](product/features/sdd-docs.md)
- Search: [product/features/search.md](product/features/search.md)
- Tenants: [product/features/tenants.md](product/features/tenants.md)
- Theme: [product/features/theme.md](product/features/theme.md)
- Toasts: [product/features/toasts.md](product/features/toasts.md)

### System Docs

- Architecture: [system/architecture.md](system/architecture.md)
- CI Pipeline: [system/ci-pipeline.md](system/ci-pipeline.md)
- Entities: [system/entities.md](system/entities.md)
- Interfaces: [system/interfaces.md](system/interfaces.md)
- Tech Stack: [system/tech-stack.md](system/tech-stack.md)

### Change Requests

- CR-001: [change-requests/CR-001-seed-admin-user.md](change-requests/CR-001-seed-admin-user.md)
- CR-002: [change-requests/CR-002-dark-mode-toggle.md](change-requests/CR-002-dark-mode-toggle.md)
- CR-003: [change-requests/CR-003-mobile-hamburger-menu.md](change-requests/CR-003-mobile-hamburger-menu.md)
- CR-004: [change-requests/CR-004-toast-notifications.md](change-requests/CR-004-toast-notifications.md)
- CR-005: [change-requests/CR-005-ci-testing-pipeline.md](change-requests/CR-005-ci-testing-pipeline.md)
- CR-006: [change-requests/CR-006-global-search-all-entities.md](change-requests/CR-006-global-search-all-entities.md)
- CR-007: [change-requests/CR-007-draft-state-management.md](change-requests/CR-007-draft-state-management.md)
- CR-008: [change-requests/CR-008-parametric-docker-image-registry.md](change-requests/CR-008-parametric-docker-image-registry.md)

### Bugs

- BUG-001: [bugs/BUG-001-landing-page-redirect-to-login.md](bugs/BUG-001-landing-page-redirect-to-login.md)

### Code and Runtime Assets

- Compose setup: [code/docker-compose.yml](code/docker-compose.yml)
- Backend app: [code/backend](code/backend)
- Frontend app: [code/frontend](code/frontend)
- Deployment templates: [code/deploy](code/deploy)
- Publish workflow: [.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml)
- CI workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)

## Quick Start

1. Start the local stack:

```bash
cd code
docker compose up -d
```

2. Open the app:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health

## Notes

- This README is an entry point. Detailed product and technical behavior is documented in the linked files above.
- For production deployment with published images, refer to [product/features/docker-images-deployment.md](product/features/docker-images-deployment.md).
