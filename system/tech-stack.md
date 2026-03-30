---
title: "Tech Stack"
status: synced
author: ""
last-modified: "2026-03-29T00:00:00.000Z"
version: "1.2"
---

# Tech Stack

## Backend

| Technology       | Purpose                          | Version |
| ---------------- | -------------------------------- | ------- |
| Python           | Language                         | 3.12+   |
| FastAPI          | Web framework                    | latest  |
| uvicorn          | ASGI server                      | latest  |
| uv               | Package manager                  | latest  |
| PyMongo (async)  | Official async MongoDB driver    | 4.10+   |
| Beanie           | Async ODM for MongoDB (Pydantic-native) | 2.1+  |
| slowapi          | Rate limiting for FastAPI        | 0.1.9+  |
| Pydantic         | Request/response validation      | 2.x     |
| python-jose      | JWT encoding/decoding            | latest  |
| passlib[bcrypt]  | Password hashing                 | latest  |
| httpx            | HTTP client (Google OAuth)       | latest  |
| python-multipart | Form data parsing (file uploads) | latest  |

## Frontend

| Technology     | Purpose                 | Version |
| -------------- | ----------------------- | ------- |
| React          | UI framework            | 18+     |
| TypeScript     | Language                | 5.x     |
| Vite           | Build tool / dev server | latest  |
| Tailwind CSS   | Utility-first CSS       | 3.x     |
| TanStack Query | Server state management | 5.x     |
| React Router   | Client-side routing     | 6.x     |
| axios          | HTTP client             | latest  |

## Infrastructure

| Technology               | Purpose                                          |
| ------------------------ | ------------------------------------------------ |
| MongoDB                  | Database (7.0+)                                  |
| Docker                   | Containerization                                 |
| Docker Compose           | Multi-service orchestration                      |
| nginx                    | Static file serving (frontend in production)     |
| GitHub Actions           | CI pipeline — runs tests on push/PR              |
| docker/build-push-action | Build and publish multi-service container images |
| docker/metadata-action   | Deterministic tags and OCI labels for images     |
| GHCR / Docker Hub        | Container registry for deployment artifacts      |

## Development

| Tool    | Purpose                                               |
| ------- | ----------------------------------------------------- |
| uv      | Python dependency management and virtual environments |
| npm     | Frontend dependency management                        |
| pytest  | Backend testing                                       |
| Vitest  | Frontend testing                                      |
