---
title: "Reorganize frontend pages into domain-based folders"
status: applied
author: "roberto"
created-at: "2026-03-19T00:00:00.000Z"
---

# CR-016: Reorganize frontend pages into domain-based folders

## Summary

Improve frontend maintainability by replacing the current flat `src/pages` structure with a domain-based folder organization and a non-redundant naming convention inside each folder. This change keeps routing behavior unchanged while making page discovery, onboarding, and future feature growth easier.

## Problem Analysis

The current frontend keeps all page components in a single directory (`code/frontend/src/pages`), including auth, tenant, project, docs, bugs, and change-request pages.

As the app grows, this creates the following problems:

1. **Low discoverability**: developers must scan one long list of files to find related pages.
2. **Weak domain boundaries**: pages from unrelated contexts (for example auth and project management) are mixed together.
3. **Redundant naming**: when filenames already include domain prefixes (for example `BugListPage.tsx`, `CRDetailPage.tsx`), names become repetitive after grouping by domain.
4. **Higher maintenance cost**: adding or refactoring a feature requires touching a crowded folder and increasing import churn.
5. **Scalability risk**: new pages will make the flat structure progressively harder to navigate and review.

### Current Examples

The following files currently coexist in one folder despite belonging to different areas:
- Auth: `LoginPage.tsx`, `RegisterPage.tsx`
- Tenant: `TenantDashboardPage.tsx`, `CreateTenantPage.tsx`, `TenantSettingsPage.tsx`
- Project: `ProjectListPage.tsx`, `CreateProjectPage.tsx`, `ProjectDashboardPage.tsx`, `ProjectSettingsPage.tsx`
- Change Requests: `CRListPage.tsx`, `CRCreatePage.tsx`, `CRDetailPage.tsx`
- Bugs: `BugListPage.tsx`, `BugCreatePage.tsx`, `BugDetailPage.tsx`
- Docs: `DocsTreePage.tsx`, `DocViewPage.tsx`

In a domain-folder structure, these prefixes become unnecessary and can be simplified.

## Proposed Solution

Adopt a domain-oriented structure under `code/frontend/src/pages`.

### Target Structure

```text
src/pages/
  auth/
    LoginPage.tsx
    RegisterPage.tsx
  tenant/
    DashboardPage.tsx
    CreatePage.tsx
    SettingsPage.tsx
  project/
    ListPage.tsx
    CreatePage.tsx
    DashboardPage.tsx
    SettingsPage.tsx
  change-requests/
    ListPage.tsx
    CreatePage.tsx
    DetailPage.tsx
  bugs/
    ListPage.tsx
    CreatePage.tsx
    DetailPage.tsx
  docs/
    TreePage.tsx
    ViewPage.tsx
  system/
    AuditLogPage.tsx
    LandingPage.tsx
    NotFoundPage.tsx
```

### Design Principles

1. **Route stability first**: URL paths and route behavior remain unchanged.
2. **Domain grouping**: each folder maps to a product area.
3. **No repeated prefixes inside folders**: once grouped by domain, filenames should describe the page role (`ListPage`, `DetailPage`, `SettingsPage`) without repeating the domain.
4. **Predictable imports**: centralize page exports via optional `index.ts` files per folder.
5. **Incremental migration**: move and rename files in controlled steps and update imports immediately.

### Implementation Approach

1. Create domain subfolders under `src/pages`.
2. Move and rename existing page files into their target folders using the non-redundant naming convention.
3. Update imports in `code/frontend/src/App.tsx` to the new paths.
4. Optionally add folder-level `index.ts` barrel exports to simplify route imports.
5. Run unit and e2e tests to confirm no route regressions.

### Non-goals

1. No redesign of page UI.
2. No change to route URLs or access control logic.
3. No backend API changes.

## Acceptance Criteria

1. `src/pages` is organized into domain subfolders as defined above.
2. Redundant filename prefixes are removed inside domain folders (for example no `Bug*` files inside `pages/bugs`).
3. `code/frontend/src/App.tsx` compiles with updated imports and unchanged route behavior.
4. Existing navigation flows (auth, tenant, project, CR, bug, docs, audit) continue to work.
5. Frontend tests pass without introducing route-level regressions.
6. New pages can be added inside the correct domain folder without reintroducing a flat structure or redundant names.

## Risks and Mitigations

- **Risk**: broken imports after file moves.
  - **Mitigation**: migrate folder by folder and run type-check/tests after each step.

- **Risk**: merge conflicts with parallel frontend work.
  - **Mitigation**: perform a single focused refactor commit and avoid unrelated edits.

- **Risk**: inconsistent future placement of new pages.
  - **Mitigation**: document folder conventions in frontend README or contribution notes.

- **Risk**: generic names may collide when imported from multiple domains.
  - **Mitigation**: use folder-qualified imports (or folder-level barrels with aliases) to keep import clarity.

## Affected Files (Expected)

- `code/frontend/src/pages/**` (file moves)
- `code/frontend/src/App.tsx` (import path updates)
- `code/frontend/src/pages/**/index.ts` (optional barrel exports)
- `code/frontend/e2e/**/*.spec.ts` (only if imports or route assumptions require adjustments)

## Notes

This CR focuses on structural maintainability. It is intentionally low risk because it does not alter runtime business logic, API contracts, or route definitions.