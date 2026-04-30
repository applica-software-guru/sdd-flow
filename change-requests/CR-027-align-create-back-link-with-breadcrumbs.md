---
title: "Align Create page back link with breadcrumbs"
status: applied
author: "user"
created-at: "2026-04-30T00:00:00.000Z"
---

## Summary

After standardizing list/detail widths, the Bug/CR **Create** pages still use a narrower centered layout (`max-w-2xl`). This is acceptable, but the top "Back" link should align with the project breadcrumbs (which use the standard in-app container width).

Goal: keep forms narrow while aligning navigation affordances (back link) with the breadcrumbs baseline.

---

## Required changes

### Documentation

#### `system/architecture.md`

In the frontend section, add a note:

- When a page uses a narrow inner form, keep the top navigation/back affordances aligned to the standard container (same baseline as breadcrumbs).

### Frontend

#### `code/frontend/src/pages/bugs/CreatePage.tsx`

- Wrap the page with the standard container (`PageContainer`)
- Render the back link (and optional header) aligned with the outer container
- Keep the form card narrow via an inner wrapper `mx-auto max-w-2xl`

#### `code/frontend/src/pages/change-requests/CreatePage.tsx`

Same as above.

---

## Notes / edge cases

- This change is intentionally limited to Bugs/CRs create pages.
- We can extend the same pattern to other narrow pages later (settings/create flows) if desired.
