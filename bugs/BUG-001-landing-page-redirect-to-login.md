---
title: "Landing page redirects unauthenticated users to /login"
status: resolved
author: "roberto"
created-at: "2026-03-17T00:00:00.000Z"
---

## Description

Unauthenticated users visiting `/` are immediately redirected to `/login` instead of seeing the landing page.

## Root cause

The axios response interceptor in `code/frontend/src/lib/api.ts` catches all 401 responses and performs a hard `window.location.href = '/login'` redirect. The only exclusion was `/login` itself.

When the `LandingPage` component mounts, it calls `useCurrentUser()` which triggers `GET /auth/me`. For unauthenticated users:

1. `/auth/me` returns 401
2. Interceptor tries `POST /auth/refresh` — also fails (no session)
3. Interceptor checks `window.location.pathname !== '/login'` — true (pathname is `/`)
4. Hard redirect to `/login` before the landing page renders

## Fix

Changed the interceptor guard in `api.ts` from a single-path check to a public paths list:

```typescript
// Before
if (window.location.pathname !== '/login') {
  window.location.href = '/login';
}

// After
const publicPaths = ['/', '/login', '/register'];
if (!publicPaths.includes(window.location.pathname)) {
  window.location.href = '/login';
}
```

This ensures the interceptor never redirects away from public pages (`/`, `/login`, `/register`).
