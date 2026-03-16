---
title: "Architecture Decisions"
status: changed
author: ""
last-modified: "2026-03-16T22:30:00.000Z"
version: "1.2"
---

# Architecture Decisions

## Monorepo Structure

```
sdd-flow/
├── backend/               # Python (FastAPI + uvicorn)
│   ├── app/
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── config.py      # Settings from env vars
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── api/           # Route handlers grouped by domain
│   │   │   ├── auth.py
│   │   │   ├── tenants.py
│   │   │   ├── projects.py
│   │   │   ├── change_requests.py
│   │   │   ├── bugs.py
│   │   │   ├── docs.py
│   │   │   └── ...
│   │   ├── services/      # Business logic
│   │   ├── middleware/     # Auth, tenant scoping
│   │   └── db/            # Database connection, migrations
│   ├── alembic/           # Database migrations
│   ├── pyproject.toml     # uv project config
│   └── Dockerfile
├── frontend/              # React (Vite + Tailwind)
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── hooks/         # All data fetching via react-query hooks
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page-level components (route targets)
│   │   ├── lib/           # API client, auth helpers
│   │   └── types/         # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml     # Full stack: backend + frontend + postgres
└── product/               # SDD documentation (this directory)
```

## Key Decisions

### Backend: FastAPI + SQLAlchemy + Alembic

- **FastAPI** for automatic OpenAPI docs, Pydantic validation, async support
- **SQLAlchemy** (async) as ORM with **Alembic** for migrations
- **uvicorn** as the ASGI server
- **uv** as the Python package manager

### Frontend: React + Vite + Tailwind + React Query

- **Vite** for fast dev server and builds
- **Tailwind CSS** for styling
- **React Query (TanStack Query)** for all server state — no manual fetch/loading/error state
- **All data fetching lives in `hooks/`** — components never call the API directly
- **React Router** for client-side routing

### Database: PostgreSQL

- PostgreSQL for production and development
- Full-text search via `tsvector` for global search
- JSONB for flexible audit log details
- UUID primary keys everywhere

### Auth: JWT + HTTP-only Cookies

- Access token (15min) + refresh token (7 days)
- Tokens stored in HTTP-only, Secure, SameSite cookies
- No tokens in localStorage (XSS protection)
- Google OAuth via authorization code flow (server-side token exchange)

### Multi-Tenancy: Shared Database, Tenant Column

- All tenant-scoped tables have a `tenant_id` column
- A middleware extracts the current tenant from the JWT and injects it into all queries
- No data should ever be returned without tenant scoping

### API Key Auth: Separate from User Auth

- API keys use Bearer token auth but are handled by a separate middleware
- The middleware resolves the API key to a project and tenant, then injects those into the request context
- API key routes and user routes share the same endpoint paths but different auth flows

### First-Run Seed

- On application startup, the backend checks if the `users` table is empty
- If empty, it creates a default admin user (email: `admin@sddflow.local`, random password), a default tenant ("Default"), and assigns the admin as Owner
- Credentials are printed to stdout so the operator can log in
- If users already exist, the seed is skipped silently
- Implemented in `app/services/seed.py`, triggered via the FastAPI lifespan hook in `app/main.py`

### Theming: Tailwind Dark Mode

- **Dark mode strategy**: `darkMode: 'class'` in Tailwind config — a `dark` class on `<html>` activates all `dark:` variants
- **ThemeProvider context** manages the current theme state, OS preference detection, and localStorage persistence
- **ThemeToggle component** in the header provides Light / Dark / System options
- The markdown editor (`@uiw/react-md-editor`) uses the `data-color-mode` prop bound to the resolved theme

### Deployment

- **Docker Compose** for local development and self-hosted deployment
- **Dockerfile** per service (backend, frontend)
- Frontend served as static files by nginx in production
- Environment variables for all configuration (database URL, OAuth secrets, JWT secret)
