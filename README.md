# SDD Flow

SDD Flow is an open-source platform for managing **Story Driven Development** across teams, projects, repositories, and coding agents. It keeps product intent, system design, change requests, bugs, implementation status, and delivery activity in one shared workspace.

## What SDD Flow provides

- **Multi-tenant workspaces** with memberships, invitations, roles, and project-level navigation.
- **Living SDD documentation** with hierarchical browsing, Markdown, Mermaid diagrams, and bidirectional CLI synchronization.
- **Change Request and Bug workflows** with progressive identifiers, lifecycle transitions, severity, assignment, comments, and audit history.
- **Remote coding workers** for enrichment and implementation jobs, including presence, progress, terminal output, and agent questions.
- **Project dashboards** with Change Request, Bug, document, and worker summaries.
- **Search, notifications, themes, responsive navigation, and audit logs** for daily collaboration.
- **API keys and CLI integration** for hosted and self-managed projects.
- **Container and cloud deployment paths** for Docker, Cloud Run, and Cloudflare Pages.

## Documentation

This repository is also its own SDD specification. Its documentation is divided into four stable areas that can be browsed directly from the repository:

| Area                                  | Contents                                                                   |
| ------------------------------------- | -------------------------------------------------------------------------- |
| [`product/`](product)                 | Product vision, user personas, and implemented feature specifications      |
| [`system/`](system)                   | Architecture decisions, entities, API interfaces, technology stack, and CI |
| [`change-requests/`](change-requests) | Proposed and applied changes, rationale, scope, and acceptance criteria    |
| [`bugs/`](bugs)                       | Reproducible defects, analysis, fixes, and resolution criteria             |

The directory listings are the documentation index: adding a feature, Change Request, or bug does not require updating this README.

## Architecture

```text
Browser / React application
          │
          │ HTTP, JSON, secure auth cookie
          ▼
       FastAPI
          │
          ├── domain services and API adapters
          ├── authentication, authorization, rate limits, and mail
          └── Beanie / PyMongo
                    │
                    ▼
                 MongoDB

SDD CLI / remote worker ─── scoped API keys ───► FastAPI
```

| Layer    | Technologies                                                                                    |
| -------- | ----------------------------------------------------------------------------------------------- |
| Frontend | React 18, TypeScript, Vite, React Router, TanStack Query, Tailwind CSS, shadcn/Radix primitives |
| Backend  | Python 3.12+, FastAPI, Pydantic, Beanie, PyMongo, Uvicorn                                       |
| Data     | MongoDB 7                                                                                       |
| Testing  | Vitest, Testing Library, Playwright, Pytest                                                     |
| Quality  | ESLint, Prettier, TypeScript, Ruff, Pyright                                                     |
| Delivery | Docker and GitHub Actions                                                                       |

## Repository structure

```text
.
├── product/                 Product vision, users, and feature specifications
├── system/                  Architecture, entities, interfaces, stack, and CI
├── change-requests/         Proposed and applied product/system changes
├── bugs/                    Defect reports and resolution records
├── code/
│   ├── backend/             FastAPI application, services, models, and tests
│   ├── frontend/            React application, component tests, and E2E tests
│   └── docker-compose.yml   Local container stack
├── .github/workflows/       CI, image publishing, and cloud deployment
├── .sdd/                    Local metadata managed by the SDD CLI
└── run-dev.sh               Local backend/frontend process manager
```

## Local development

### Prerequisites

- Python 3.12 or newer
- `uv`
- Node.js 20, managed with FNM or NVM
- npm
- MongoDB on `localhost:27017`

MongoDB can be started separately with Docker:

```bash
docker run --name sdd-flow-mongo -p 27017:27017 -d mongo:7
```

### Configuration

Create the backend environment file:

```bash
cp code/backend/.env.example code/backend/.env
```

Review it before starting. In particular:

- set `MONGODB_URL` to the intended database;
- replace `JWT_SECRET` with a private value of at least 32 characters;
- keep `FRONTEND_URL` aligned with the frontend port;
- configure OAuth and mail only when needed.

A development secret can be generated with:

```bash
openssl rand -hex 32
```

Never commit real credentials or production secrets.

### Start the application

The development helper installs missing dependencies and runs both applications with hot reload:

```bash
./run-dev.sh
```

Default endpoints:

- web application: <http://localhost:3002>
- backend API: <http://localhost:8000>
- health check: <http://localhost:8000/health>
- OpenAPI documentation: <http://localhost:8000/docs>

Useful commands:

```bash
./run-dev.sh --status
./run-dev.sh --restart
./run-dev.sh --only backend
./run-dev.sh --stop frontend
./run-dev.sh --stop-all
./run-dev.sh --help
```

## Docker quick start

Build and run MongoDB, backend, and frontend from `code/`:

```bash
cd code
JWT_SECRET="$(openssl rand -hex 32)" docker compose up --build
```

Docker exposes:

- frontend: <http://localhost:5173>
- backend: <http://localhost:8000>
- MongoDB: `localhost:27017`

For persistent settings, create `code/.env` and provide deployment-specific values. Stop the stack with `docker compose down`; add `-v` only when the MongoDB volume should also be deleted.

## Quality checks

### Frontend

```bash
cd code/frontend
npm install
npm run check       # filenames, ESLint, TypeScript, Prettier, Vitest, build
npm run test:e2e    # Playwright browser suite
```

### Backend

```bash
cd code/backend
./cli.sh install
./cli.sh check      # Ruff and Pyright
./cli.sh test       # Pytest; requires MongoDB
```

These quality gates are also enforced by the repository CI workflow.

## SDD workflow

The repository follows a Markdown-first lifecycle:

1. Describe product behavior under `product/`.
2. Describe architecture and technical contracts under `system/`.
3. Record proposed evolution under `change-requests/`.
4. Record reproducible defects under `bugs/`.
5. Use the SDD CLI to identify documentation awaiting implementation.
6. Synchronize code, tests, and documentation in the same change.

Common SDD commands:

```bash
sdd bug open
sdd cr pending
sdd sync
sdd validate
sdd status
```

Document frontmatter communicates lifecycle state, such as `draft`, `pending`, `applied`, `open`, `resolved`, `new`, `changed`, or `synced`. Files under `.sdd/` are managed by the CLI and should not be edited manually.

## Deployment

GitHub Actions workflows cover continuous integration, container image publication, backend deployment to Cloud Run, and frontend deployment to Cloudflare Pages. Review workflow inputs, environment configuration, and secret requirements before publishing or deploying.

## License

SDD Flow is available under the [MIT License](LICENSE).
