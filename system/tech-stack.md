---
title: "Tech Stack"
status: synced
author: ""
last-modified: "2026-09-05T14:20:00.000Z"
version: "1.5"
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
| shadcn/ui      | Code-owned UI primitives | latest |
| Radix UI       | Accessible interactions  | latest  |
| Lucide React   | Shared icon library      | latest  |
| CVA / tailwind-merge | Component variants and class merging | latest |
| i18next | Typed translation resources, fallback, interpolation and plurals | latest |
| react-i18next | React bindings for locale-aware rendering | latest |
| i18next-browser-languagedetector | Persisted and browser language detection | latest |
| vite-plugin-pwa | Vite/Workbox service-worker generation and PWA manifest integration | latest |
| Workbox | Precache and service-worker runtime strategy used by the PWA build | bundled with vite-plugin-pwa |

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
| Vitest  | Frontend unit testing                                 |
| Testing Library | Frontend interaction and accessibility tests     |
| ESLint  | Type-aware TypeScript and JSX accessibility linting     |
| Prettier | Frontend formatting and Tailwind class ordering         |
| PWA manifest/icon validator | Frontend installability metadata and icon-dimension checks |
