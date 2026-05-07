# SDD Flow

SDD Flow is a web platform to manage Story Driven Development projects.
It gives teams a single place to work on documentation, changes, and delivery status across multiple repositories.

## What The App Does

- centralizes project context (product + system docs)
- tracks changes and issues in a shared workflow
- exposes API integration for CLI-based sync
- supports team collaboration with multi-tenant access
- runs both as SaaS companion and self-hosted via Docker

## Quick Start

1. Configure backend environment variables:

```bash
cd code/backend
cp .env.example .env
```

Edit `code/backend/.env` and fill in the required values. In particular:

- `JWT_SECRET` must be **at least 32 characters long**. Generate a strong random value, for example:

  ```bash
  openssl rand -hex 32
  ```

- `MONGODB_URL`, `FRONTEND_URL`, mail provider keys, and OAuth credentials should be reviewed before starting the stack.

2. Start the local stack:

```bash
cd code
docker compose up -d
```

3. Open the app:

- Frontend: http://localhost:3002
- Backend health: http://localhost:8000/health

## Project Folders

- Product docs: [product](product)
- System docs: [system](system)
- Source code: [code](code)
- Change requests: [change-requests](change-requests)
- Bug reports: [bugs](bugs)

## Notes

- This README is intentionally concise.
- Detailed domain and technical specifications remain in the project folders above.
