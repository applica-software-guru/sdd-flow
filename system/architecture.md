---
title: "Architecture Decisions"
status: synced
author: ""
last-modified: "2026-03-26T00:00:00.000Z"
version: "1.5"
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
│   │   │   ├── workers.py        # Web routes: workers & jobs (JWT)
│   │   │   ├── workers_cli.py    # CLI routes: worker daemon (API key)
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

### Responsive Navigation

- The desktop sidebar is hidden below the `lg` breakpoint
- A **hamburger menu button** appears in the header on small screens (`lg:hidden`)
- Tapping it opens a **slide-over drawer** from the left with the full sidebar navigation, tenant switcher, and a close button
- The drawer closes on backdrop tap, close button, or navigation (route change)
- The drawer supports dark mode via `dark:` variant classes

### CI Pipeline: GitHub Actions

- **GitHub Actions** runs pytest (backend) and Vitest (frontend) on every push to `main` and on all pull requests
- Backend tests use a **PostgreSQL service container** for integration testing against a real database
- Frontend and backend jobs run **in parallel** for faster feedback
- Workflow defined in `.github/workflows/ci.yml` at the project root

### Container Artifact Flow: Build Once, Configure at Runtime

- CI builds backend/frontend images and publishes them to Google Artifact Registry (GAR)
- Deployments consume immutable image tags and inject environment-specific runtime parameters
- Same image tag is promoted across environments (`dev` -> `staging` -> `prod`) by changing runtime configuration, not rebuilding
- Publish runs must share one canonical `VERSION` value between backend/frontend images
- Version source precedence in workflow: manual `image_tag` override -> git tag `v*` -> `rev-<short_sha>` fallback
- Stable releases can additionally publish `latest`, but `${VERSION}` remains the canonical deploy reference
- Runtime config boundary:
  - Image content is environment-agnostic
  - Domain, OAuth, JWT, DB URL, and proxy upstream values come from deployment environment

### Runtime Config Compatibility Rules

- Canonical backend runtime variables: `DATABASE_URL`, `JWT_SECRET`, `FRONTEND_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- If `APP_DOMAIN` is introduced, compatibility mapping must be explicit:
  - If both `APP_DOMAIN` and `FRONTEND_URL` exist, `FRONTEND_URL` takes precedence
  - If only `APP_DOMAIN` exists, derive `FRONTEND_URL=https://<APP_DOMAIN>`
- Legacy variable names remain supported for at least one release cycle with deprecation warnings

### Frontend Runtime Injection

- Frontend production image is static (nginx) and must not require rebuild per environment
- Runtime values are injected at container startup (entrypoint template + generated runtime config)
- NGINX upstream and server_name are runtime-configurable via env vars

### Remote Worker Architecture

Workers are machines running `sdd remote worker` that connect to SDD Flow to receive and execute AI agent jobs.

**Communication Protocol:**

```
┌─────────────────┐     SSE (output stream)     ┌──────────────┐
│   Web Frontend   │◄────────────────────────────│              │
│   (React)        │─── POST answer ────────────►│   Backend    │
└─────────────────┘                              │   (FastAPI)  │
                                                 │              │
┌─────────────────┐     Long-poll (jobs)         │              │
│   Worker (CLI)   │◄────────────────────────────│              │
│   sdd remote     │─── POST output/question ──►│              │
│   worker         │─── POST heartbeat ─────────►│              │
└─────────────────┘                              └──────────────┘
```

- **Worker → Server**: Long polling for job assignment (30s hold) + POST for output/heartbeat. Chosen over WebSocket for NAT/firewall friendliness — no persistent connection required.
- **Server → Frontend**: SSE (Server-Sent Events) via `StreamingResponse` for real-time output streaming. The server polls the database every 0.5s and yields new messages.
- **Q&A relay**: Worker posts a question → Server stores it → SSE delivers to frontend → User answers via POST → Worker polls for answers → Writes to agent stdin.

**Atomic Job Assignment:**

Jobs are assigned using `SELECT ... FOR UPDATE SKIP LOCKED` to prevent two workers from grabbing the same job. The first worker to execute the query wins.

**Health Monitoring:**

No separate scheduler or cron. Stale worker detection piggybacks on heartbeat and poll requests:
- Worker offline: heartbeat older than 60 seconds
- Job failed: worker offline for more than 5 minutes with a running job

**Agent Abstraction:**

The worker uses the existing agent runner infrastructure (`startAgent()` in `agent-runner.ts`) with `stdio: ['pipe', 'pipe', 'pipe']` for interactive mode. The agent adapter (Claude Code, Codex, OpenCode) is selected by the `--agent` flag or project config.

**Auto-transition on Completion:**

When a job completes with exit code 0, the backend automatically transitions the associated entity:
- Change Request: `approved` → `applied`
- Bug: `open`/`in_progress` → `resolved`

### Deployment

- **Docker Compose** for local development and self-hosted deployment
- **Dockerfile** per service (backend, frontend)
- Frontend served as static files by nginx in production
- Environment variables for all configuration (database URL, OAuth secrets, JWT secret)
