---
title: "Tenant and project workspace switcher"
status: applied
author: "user"
created-at: "2026-09-05T09:25:42.000Z"
---

# CR-040: Tenant and Project Workspace Switcher

## Summary

Improve the current tenant selector so it becomes a compact workspace switcher with two explicit navigation paths:

1. select a tenant only and navigate to the tenant-level dashboard;
2. select a project inside a tenant and navigate directly to that project's dashboard.

The selector should keep the existing tenant-switching capability, but remove the unnecessary detour where a user must first choose a tenant, land on the tenant dashboard, then choose a project. A clean grouped/tree view can show tenants as parent entries and their projects as child entries.

## Product decision

This is feasible and fits the current information architecture because tenants and projects are already distinct URL scopes:

- tenant overview: `/tenants/:tenantId`;
- project overview: `/tenants/:tenantId/projects/:projectId`.

The recommended implementation is not a heavy file-explorer tree, but a searchable workspace popover/command menu with grouped tenant sections:

- each tenant group has a first-class `Open tenant overview` action;
- projects are shown indented below the tenant;
- selecting a project navigates directly to the project route;
- the current tenant/project selection is clearly highlighted.

This keeps the interaction elegant and fast while avoiding ambiguity between "switch tenant" and "open project".

## Context

Today the top-bar/mobile tenant selector only lists tenants. When a user wants to open a project in another tenant, the flow is:

1. open tenant selector;
2. select tenant;
3. navigate to tenant dashboard;
4. find/select the project;
5. navigate into the project.

That flow is correct but unnecessarily long for users who frequently move between projects. The tenant dashboard should remain the canonical tenant-level overview, but the global selector should support direct project navigation.

## Objectives

1. Reduce cross-project navigation from multiple steps to one selector interaction.
2. Preserve the ability to select only a tenant and land on its dashboard.
3. Make the hierarchy between tenants and projects visually obvious.
4. Keep the control compact enough for the top bar and mobile drawer.
5. Avoid loading full project dashboards or full tenant aggregates just to render navigation.
6. Preserve tenant scoping, role safety, dark mode, responsiveness, and accessibility.

## Proposed UX

### Trigger button

Replace the current tenant-only trigger label with a workspace-aware label:

- when no project is selected: show tenant name and helper text such as `Tenant overview`;
- when a project is selected: show project name as the primary label and tenant name as secondary context;
- if data is still loading: show a compact skeleton/loading label;
- if the current route has a tenant/project id not present in the navigation payload: fall back gracefully to `Select workspace`.

The trigger should remain visually compact in the desktop top bar and fit in the mobile navigation drawer.

### Popover content

The popover should include:

1. search input with placeholder `Search tenants or projects`;
2. grouped tenant sections;
3. tenant row action:
   - label: tenant name;
   - secondary text: `Tenant overview`;
   - click target navigates to `/tenants/:tenantId`;
   - current marker is shown only when the route has that tenant and no project selected;
4. project rows under each tenant:
   - indented or otherwise visually nested;
   - label: project name;
   - secondary text: project slug and optional archived badge;
   - click target navigates to `/tenants/:tenantId/projects/:projectId`;
   - current marker is shown when both tenant and project match;
5. footer actions:
   - `New tenant`;
   - optionally `New project` in the currently active tenant, shown only when the user has permission.

### Search behavior

Search should match:

- tenant name;
- tenant slug;
- project name;
- project slug.

When a project matches, its parent tenant group remains visible even if the tenant name itself does not match. Search should be client-side for the first version, based on the compact navigation payload.

### Tree/grouping behavior

The first version should prefer an always-visible grouped list over a complex expandable/collapsible tree, unless the number of projects makes the list too long.

Recommended behavior:

- show tenant groups expanded by default;
- if project volume is high, cap visible projects per tenant and provide `Show all projects` or introduce collapsible groups later;
- archived projects are hidden by default unless the existing project-list semantics already include them; if shown, they must have an `Archived` badge and sort after active projects.

## Backend/API contract

Introduce a compact navigation endpoint dedicated to the selector. It should not reuse the tenant dashboard aggregate endpoint because the selector needs projects across all visible tenants, while the dashboard endpoint is scoped to one tenant and contains KPI data that is too heavy for navigation.

Recommended endpoint:

```text
GET /tenants/navigation
```

Response:

```json
{
  "tenants": [
    {
      "id": "...",
      "name": "Acme",
      "slug": "acme",
      "role": "admin",
      "can_create_project": true,
      "projects": [
        {
          "id": "...",
          "name": "Web App",
          "slug": "web-app",
          "archived_at": null
        }
      ]
    }
  ]
}
```

Endpoint rules:

- returns only tenants where the authenticated user is a member;
- returns only projects visible to that user in each tenant;
- returns compact navigation fields only;
- does not return docs, CRs, bugs, comments, KPI details, audit details, API keys, or member lists;
- orders tenants by name or last-used/recently-used semantics if available;
- orders projects with active projects first, then by name or recent activity if available;
- may exclude archived projects by default, or include them with `archived_at` if that is the existing project-list behavior.

If adding a new endpoint is considered too much for the first iteration, an acceptable fallback is lazy loading projects per tenant when a group is expanded using `GET /tenants/:tenantId/projects`. The dedicated endpoint is still preferred because it avoids multiple round trips and keeps the selector deterministic.

## Frontend contract

Rename or replace the current `TenantSwitcher` with a workspace-aware component, for example `WorkspaceSwitcher`.

Required behavior:

- uses a dedicated query hook such as `useWorkspaceNavigation()` backed by `GET /tenants/navigation`;
- reads `tenantId` and `projectId` from the current route;
- computes current label from route params and navigation payload;
- navigates to `/tenants/:tenantId` when a tenant overview row is selected;
- navigates to `/tenants/:tenantId/projects/:projectId` when a project row is selected;
- keeps `New tenant` behavior;
- shows `New project` only when a tenant context is known and permissions allow it;
- handles loading, empty, and error states inside the popover;
- supports keyboard navigation and screen-reader labels;
- uses shared UI primitives/design tokens and works in dark mode;
- is reused in both desktop top bar and mobile navigation drawer.

## Documentation changes to apply

Update the following documentation files:

- `product/features/tenants.md`
  - Expand `Tenant Switching` into workspace switching.
  - Document that users can select a tenant overview or a project directly from the selector.
- `product/features/dashboard.md`
  - Clarify that the tenant dashboard remains the canonical tenant-level overview, but is no longer the only way to reach a project.
- `system/interfaces.md`
  - Add `GET /tenants/navigation` compact response contract.
- `system/architecture.md`
  - Document the workspace switcher as shared desktop/mobile navigation and explain why it uses a compact navigation endpoint instead of tenant dashboard aggregates.

## Acceptance criteria

1. The top-bar/mobile selector shows tenants and their projects in a clear grouped/tree-like layout.
2. Selecting a tenant row navigates to `/tenants/:tenantId` and leaves the user at tenant overview level.
3. Selecting a project row navigates directly to `/tenants/:tenantId/projects/:projectId`.
4. The current tenant overview is highlighted when no project is selected.
5. The current project is highlighted when a project route is active.
6. Search filters both tenants and projects without losing parent context for matching projects.
7. The selector renders loading, empty, and error states gracefully.
8. The selector is available and usable in both desktop and mobile navigation.
9. The backend navigation payload is scoped to the authenticated user's tenant memberships and project visibility.
10. The navigation endpoint returns compact selector data only and does not expose dashboard aggregates or sensitive details.
11. Role-gated actions such as `New project` remain permission-aware.
12. Existing tenant dashboard project list behavior remains intact.
13. Existing direct URLs for tenant and project dashboards continue to work.
14. Frontend tests cover tenant-only navigation, project navigation, current-state highlighting, and search behavior.
15. Backend tests cover endpoint scoping and payload shape.

## Out of scope

- Replacing the tenant dashboard project list.
- Adding project-level favorites, pinned projects, or recents persistence.
- Global command palette search across docs, CRs, and bugs.
- Cross-tenant admin views.
- Showing tenant dashboard KPIs inside the selector.
- Showing project stats inside the selector beyond minimal status badges needed for navigation.
- Changing project permissions or membership semantics.
