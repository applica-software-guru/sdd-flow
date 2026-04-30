---
title: "Standardize frontend content width across list/detail pages"
status: applied
author: "user"
created-at: "2026-04-30T00:00:00.000Z"
---

## Summary

In `code/frontend/`, navigating from list pages to detail pages causes a visible layout jump because the content container width changes (e.g. `max-w-5xl` on lists vs `max-w-3xl`/`max-w-4xl` on details).

We want one consistent content width for in-app navigation (especially list -> detail) to keep the UI stable and comfortable.

Scope: project-scoped screens inside the authenticated app shell (`Layout.tsx`). Public/auth flows (landing/login/register) and some form-heavy screens may intentionally stay narrower.

---

## Analysis

Today each page picks its own container width via Tailwind `max-w-*` classes. `Layout.tsx` does not enforce a shared content container for `<Outlet />`, so drift is expected.

Important note: besides `max-w-*` mismatches, a smaller but real layout shift can also come from scrollbars appearing/disappearing when switching between short vs long pages (gutter changes). This is most visible on Windows/Linux or when overlay scrollbars are disabled.

Concrete examples:

```tsx
// Bugs
// code/frontend/src/pages/bugs/ListPage.tsx
<div className="mx-auto max-w-5xl">

// code/frontend/src/pages/bugs/DetailPage.tsx
<div className="mx-auto max-w-3xl ...">

// Change Requests
// code/frontend/src/pages/change-requests/ListPage.tsx
<div className="mx-auto max-w-5xl">

// code/frontend/src/pages/change-requests/DetailPage.tsx
<div className="mx-auto max-w-3xl ...">

// Docs
// code/frontend/src/pages/docs/TreePage.tsx
<div className="mx-auto max-w-5xl">

// code/frontend/src/pages/docs/ViewPage.tsx
<div className="mx-auto max-w-3xl">

// Workers
// code/frontend/src/pages/worker-jobs/ListPage.tsx
<div className="mx-auto max-w-5xl">

// code/frontend/src/pages/worker-jobs/DetailPage.tsx
<div className="mx-auto max-w-4xl">
```

This is a UX issue (layout shift) and also a maintainability issue: any new list/detail pair can reintroduce the inconsistency.

---

## Proposed approach

1. Define a single **standard in-app content width** for project-scoped pages, used consistently across list and detail views.
2. Implement it as a small reusable component (e.g. `PageContainer`).
3. Update existing list/detail pages to use the standard.

Recommended standard: `max-w-5xl` (already used by most list pages and the project dashboard).

Notes:

- If we still want better readability for long-form markdown, keep the **page container** stable and instead constrain only the markdown body (e.g. `max-w-prose`) inside the card. This avoids the navigation layout jump while keeping text readable.
- Out of scope for this CR: revisiting non list/detail pages (create/settings forms) and addressing scrollbar gutter shifts globally. We'll evaluate these after list/detail is consistent.

### Acceptance criteria

- Navigating list -> detail for Bugs/CRs/Docs/Workers does not change the outer content width.
- No noticeable horizontal jump due to scrollbar gutter changes (if present in our target browsers).
- Mobile layout remains unchanged (max-width should not affect small breakpoints).

---

## Required changes

### Documentation

#### `system/architecture.md`

Add a short section under the frontend architecture describing:

- `Layout.tsx` provides the shell (navbar/sidebar)
- All in-app pages must render inside a consistent content container width (default `max-w-5xl`)
- Prefer using a single shared helper (`PageContainer`) instead of ad-hoc `max-w-*` per page

### Frontend

#### Add: `code/frontend/src/components/PageContainer.tsx`

- `PageContainer` should centralize the default container classes: `w-full mx-auto max-w-5xl`
- Allow an optional `className` for per-page spacing (e.g. `space-y-6`) without changing width

#### Update pages to remove list/detail width mismatch

- `code/frontend/src/pages/bugs/ListPage.tsx` (adopt `PageContainer`)
- `code/frontend/src/pages/bugs/DetailPage.tsx` (switch from `max-w-3xl` to the shared container)
- `code/frontend/src/pages/change-requests/ListPage.tsx` (adopt `PageContainer`)
- `code/frontend/src/pages/change-requests/DetailPage.tsx` (switch from `max-w-3xl` to the shared container)
- `code/frontend/src/pages/docs/TreePage.tsx` (adopt `PageContainer`)
- `code/frontend/src/pages/docs/ViewPage.tsx` (switch from `max-w-3xl` to the shared container, including loading/not-found states)
- `code/frontend/src/pages/worker-jobs/ListPage.tsx` (adopt `PageContainer`)
- `code/frontend/src/pages/worker-jobs/DetailPage.tsx` (switch from `max-w-4xl`/`max-w-3xl` to the shared container)

Out of scope for this CR:

- Forms/settings/create pages (may remain narrower)
- Scrollbar gutter stabilization (can still be a minor source of shift even with consistent max-width)

---

## Follow-ups (optional, for code reuse)

Once width is standardized, there are clear opportunities to reduce duplication across detail pages:

- Extract a shared `DetailHeader` (title + badges + actions) used by Bugs/CRs/Docs.
- Extract a shared `CommentsCard` (list + composer) used by Bugs and CRs.
- Extract `LoadingState` / `NotFoundState` primitives to keep page structure consistent.

These are optional and should be done only if they keep the code simpler (avoid over-abstraction).

---

## Risks / edge cases

- **Readability regression**: widening detail pages can increase line length for markdown-heavy content. Mitigation: constrain only the markdown block (`max-w-prose` or similar) inside the wider page.
- **Full-width components**: some views (e.g. terminals/logs/tables) may actually benefit from being wider; a single `max-w-5xl` is still a cap. If we discover a screen that truly needs full-bleed width, add an explicit opt-out rather than silently diverging.
- **Nested containers**: today pages already use `mx-auto max-w-*`. Introducing a layout-level wrapper would require removing page-level wrappers to avoid double constraints. This CR intentionally prefers a page-level `PageContainer` to keep the change incremental and explicit.
- **Scrollbar gutter**: even with consistent `max-w`, short vs long pages can still shift slightly due to scrollbar gutter changes. Decide whether to address this as part of this change (recommended if the jump is noticeable in target environments).
