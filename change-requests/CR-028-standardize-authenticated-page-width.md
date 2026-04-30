---
title: "Standardize authenticated page width (including create/settings)"
status: applied
author: "user"
created-at: "2026-04-30T00:00:00.000Z"
---

## Summary

Even after standardizing list/detail widths, some authenticated pages (e.g. Bug/CR create pages, settings) still use narrower containers (`max-w-2xl`, `max-w-lg`, `max-w-xl`).

We want a single consistent content width across the authenticated app shell to keep navigation intuitive and eliminate width changes between flows like list -> detail -> create/edit.

---

## Required changes

### Documentation

#### `system/architecture.md`

- Strengthen the guideline: all authenticated in-app pages should use the standard outer container width (default `max-w-5xl`).
- Remove/replace the guidance about keeping narrow inner forms, since we are intentionally standardizing width.

### Frontend

- Update authenticated pages that still use narrower widths (`max-w-xl`, `max-w-lg`, `max-w-2xl`, `max-w-4xl`) to use the shared `PageContainer` width.
- Keep the change limited to pages rendered inside `Layout.tsx` (protected routes). Public landing/auth pages remain unchanged.

Target pages (non-exhaustive, patch as found):

- `code/frontend/src/pages/bugs/CreatePage.tsx`
- `code/frontend/src/pages/change-requests/CreatePage.tsx`
- `code/frontend/src/pages/project/CreatePage.tsx`
- `code/frontend/src/pages/project/SettingsPage.tsx`
- `code/frontend/src/pages/tenant/CreatePage.tsx`
- `code/frontend/src/pages/tenant/SettingsPage.tsx`
- `code/frontend/src/pages/tenant/DashboardPage.tsx` (subviews that currently use narrower containers)
- `code/frontend/src/pages/tenant/InvitationAcceptPage.tsx`

---

## Acceptance criteria

- All authenticated pages have the same outer content width (`PageContainer`/`max-w-5xl`).
- Navigating between list/detail/create/settings does not change the container width.
