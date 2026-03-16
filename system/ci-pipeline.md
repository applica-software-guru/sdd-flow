---
title: "CI Pipeline"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# CI Pipeline

## Overview

GitHub Actions runs frontend and backend tests on every push to `main` and on all pull requests. The two test suites run as **parallel jobs** for fast feedback.

## Workflow File

`.github/workflows/ci.yml` (project root)

### Triggers

- Push to `main` branch
- All pull requests

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
