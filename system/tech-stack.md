---
title: "Tech Stack"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# Tech Stack

## Backend

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Language | 3.12+ |
| FastAPI | Web framework | latest |
| uvicorn | ASGI server | latest |
| uv | Package manager | latest |
| SQLAlchemy | ORM (async mode) | 2.x |
| Alembic | Database migrations | latest |
| Pydantic | Request/response validation | 2.x |
| python-jose | JWT encoding/decoding | latest |
| passlib[bcrypt] | Password hashing | latest |
| httpx | HTTP client (Google OAuth) | latest |
| python-multipart | Form data parsing (file uploads) | latest |

## Frontend

| Technology | Purpose | Version |
|------------|---------|---------|
| React | UI framework | 18+ |
| TypeScript | Language | 5.x |
| Vite | Build tool / dev server | latest |
| Tailwind CSS | Utility-first CSS | 3.x |
| TanStack Query | Server state management | 5.x |
| React Router | Client-side routing | 6.x |
| axios | HTTP client | latest |

## Infrastructure

| Technology | Purpose |
|------------|---------|
| PostgreSQL | Database (15+) |
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| nginx | Static file serving (frontend in production) |

## Development

| Tool | Purpose |
|------|---------|
| uv | Python dependency management and virtual environments |
| npm | Frontend dependency management |
| Alembic | Database schema migrations |
| pytest | Backend testing |
| Vitest | Frontend testing |
