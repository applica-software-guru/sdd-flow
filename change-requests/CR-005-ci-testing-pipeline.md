---
title: "Add frontend and backend tests to GitHub Actions CI pipeline"
status: applied
author: "user"
created-at: "2026-03-16T00:00:00.000Z"
---

# CR-005: Add Frontend/Backend Tests to GitHub Actions CI Pipeline

## Summary

Set up a GitHub Actions CI pipeline that runs both backend (pytest) and frontend (Vitest) tests on every push and pull request.

## Changes Required

### New documentation file: `system/ci-pipeline.md`

Create a new system doc describing the CI/CD pipeline configuration:

- **GitHub Actions workflow** file at `.github/workflows/ci.yml` inside `code/`
- **Triggers**: runs on push to `main` and on all pull requests
- **Two parallel jobs**: `backend-tests` and `frontend-tests`

#### Backend test job (`backend-tests`)
- Runs on `ubuntu-latest`
- Sets up Python 3.12
- Installs `uv` for dependency management
- Starts a PostgreSQL service container for integration tests
- Installs backend dependencies via `uv sync`
- Runs `pytest` with the appropriate database URL

#### Frontend test job (`frontend-tests`)
- Runs on `ubuntu-latest`
- Sets up Node.js (LTS)
- Installs frontend dependencies via `npm ci`
- Runs `npx vitest run` (single-run mode)

### Update `system/architecture.md`

Add a new section under **Key Decisions** documenting the CI pipeline:

- GitHub Actions for CI — runs pytest and Vitest on every push/PR
- PostgreSQL service container for backend integration tests
- Frontend and backend jobs run in parallel for faster feedback

### Update `system/tech-stack.md`

Add to the **Infrastructure** table:

| GitHub Actions | CI pipeline — runs tests on push/PR |
