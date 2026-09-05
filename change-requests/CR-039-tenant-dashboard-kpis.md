---
title: "Tenant dashboard KPIs when no project is selected"
status: applied
author: "user"
created-at: "2026-09-05T09:02:06.000Z"
revision: "2"
---

# CR-039: Tenant Dashboard KPIs When No Project Is Selected

## Summary

Improve the main authenticated dashboard shown at tenant level, before a project is selected, so it is no longer only a project picker. The page should remain focused and compact: show tenant-level KPI cards first, then immediately show the searchable/sortable project list.

The goal is to help owners, admins, and team members understand the volume of SDD data flowing through the tenant without turning the page into a broad analytics dashboard.

## Final product decision

The first implementation intentionally contains only:

1. tenant header and actions;
2. tenant-wide KPI overview;
3. clearly separated searchable/sortable projects section.

The following ideas were considered but are explicitly **not part of this first version**:

- projects-needing-attention panel;
- recent activity detail panel;
- worker status side panel;
- additional health/insight sections;
- complex analytics charts or BI-style filtering.

Those sections can be reconsidered later only if a concrete product need emerges.

## Context

Today the tenant-level dashboard is primarily useful as navigation: when no project is selected, users see the projects available in the current tenant and can create or open one. That behavior is correct, but the page underuses the tenant-wide perspective.

A compact KPI row can answer useful questions before opening a project:

- How many active projects exist in this tenant?
- How much documentation has been produced?
- How much documentation is synced or pending sync?
- How many bugs are open?
- How many CRs are active or waiting for review/application?
- How much collaboration happened through comments in the selected time window?
- Is there general recent activity across the tenant?

After those KPI cards, the user should immediately find the project selector/list without another large wrapper card consuming vertical space.

## Objectives

1. Make the tenant dashboard informative before project selection.
2. Keep project selection and project creation prominent.
3. Keep the page compact: header, KPI cards, divider, projects.
4. Provide tenant-wide KPI cards for project count, documentation, bugs, CRs, comments/collaboration, and activity volume.
5. Let users search and sort projects directly below the KPI row.
6. Use a dedicated aggregate backend API instead of many frontend list calls.
7. Preserve tenant scoping, role safety, responsiveness, dark mode, and design-system conventions.

## Target dashboard layout

### 1. Tenant header

The top of the page communicates that the user is in the tenant-level view, not inside a project.

Required content:

- tenant name;
- subtitle such as `Overview across all projects`;
- primary action: `New project` for roles allowed to create projects;
- secondary action: `Tenant settings` for roles allowed to manage the tenant;
- short helper copy explaining that opening a project reveals project-specific docs, CRs, bugs, workers, and settings.

### 2. KPI overview

A compact KPI grid appears below the header.

Recommended KPI cards:

| KPI | Primary value | Secondary context |
|-----|---------------|-------------------|
| Projects | Active projects | Archived projects when non-zero |
| Documentation | Sync percentage | Total files and pending files |
| Open bugs | Bugs with status `open` or `in_progress` | Critical and major breakdown |
| Active CRs | CRs in active workflow statuses | Review/apply queue count |
| Comments | Comments created in the selected window | Distinct commenters |
| Activity | Tenant activity event count in the selected window | Optional worker online count as helper text |

The KPI grid should wrap cleanly on smaller screens without horizontal overflow.

### 3. Strong separator between KPI and projects

A clearly visible divider separates the KPI cards from the projects section. The separator should make the shift from tenant metrics to project selection visually obvious while avoiding an additional outer card/container around the project selector area.

### 4. Projects section

The project section appears immediately after the divider.

Required behavior:

- no outer card around the whole selector/list section;
- section title `Projects`;
- search by project name or slug;
- sort by recent activity, open bugs, active CRs, documentation sync, or name;
- project cards/rows remain clickable and open the project;
- each project item may show compact per-project summary data: docs synced/total, pending docs, open bugs, active CRs, comments in the selected window, worker online/total, and last activity where available;
- archived project badge is shown when archived projects are included.

### 5. Empty and low-data states

- No projects: show onboarding guidance and `Create your first project`.
- Projects but no docs/CRs/bugs: show KPI cards with zero/neutral values and the searchable project list.
- No comments or activity in the selected period: show zero/neutral KPI helper text, not an error state.

## KPI definitions

Default time window:

- `last_30_days` for comments and activity-volume metrics.
- The API may support `last_7_days` and `last_90_days`, but the first UI version can use the default only.

Count semantics:

- **Active projects**: projects where `archived_at` is null.
- **Archived projects**: projects where `archived_at` is not null; excluded from primary active KPI totals unless explicitly shown as secondary text.
- **Total docs**: non-deleted `DocumentFile` records for active projects.
- **Synced docs**: documents with status `synced`.
- **Pending docs**: documents with status `new`, `changed`, or `deleted`.
- **Open bugs**: bugs with status `open` or `in_progress`.
- **Critical/major bugs**: open bugs whose severity is `critical` or `major`.
- **Active CRs**: CRs in non-terminal work statuses, at minimum `draft`, `pending`, and `approved`; excludes `applied`, `closed`, `rejected`, and `deleted`.
- **Review/apply queue**: CRs with status `pending` or `approved`, following the implemented CLI/web status mapping.
- **Comments generated**: comments on CRs and bugs created in the selected time window across active projects.
- **Distinct commenters**: distinct comment authors in the selected time window.
- **Activity events**: meaningful tenant audit-log entries in the selected time window, exposed only as an aggregate count.
- **Workers online**: workers whose computed online semantics match the project workers endpoint.

## Backend/API contract

Introduce a dedicated tenant dashboard summary endpoint:

```text
GET /tenants/:tenant_id/dashboard
```

Recommended query parameters:

- `window`: optional, one of `last_7_days`, `last_30_days`, `last_90_days`; default `last_30_days`.
- `include_archived`: optional boolean; default `false`.

Recommended response shape:

```json
{
  "tenant": { "id": "...", "name": "Acme", "slug": "acme" },
  "window": {
    "preset": "last_30_days",
    "from": "2026-08-06T00:00:00Z",
    "to": "2026-09-05T00:00:00Z"
  },
  "kpis": {
    "active_projects": 6,
    "archived_projects": 1,
    "documents_total": 148,
    "documents_synced": 132,
    "documents_pending": 16,
    "docs_sync_percentage": 89,
    "open_bugs": 12,
    "critical_bugs": 2,
    "major_bugs": 5,
    "active_crs": 21,
    "review_queue_crs": 8,
    "comments_in_window": 94,
    "distinct_commenters_in_window": 7,
    "activity_events_in_window": 240,
    "workers_online": 3,
    "workers_total": 5
  },
  "projects": [
    {
      "id": "...",
      "name": "Web App",
      "slug": "web-app",
      "description": "...",
      "archived_at": null,
      "stats": {
        "documents_total": 34,
        "documents_synced": 29,
        "documents_pending": 5,
        "open_bugs": 4,
        "critical_bugs": 1,
        "major_bugs": 2,
        "active_crs": 6,
        "review_queue_crs": 2,
        "comments_in_window": 18,
        "distinct_commenters_in_window": 3,
        "activity_events_in_window": 47,
        "workers_online": 1,
        "workers_total": 2,
        "last_activity_at": "2026-09-05T08:45:00Z"
      }
    }
  ]
}
```

The endpoint returns compact summaries only. It must not return full document, CR, bug, comment, or audit-log bodies/details.

## Landing-page preview contract

Because the public landing page presents a static product preview of the tenant dashboard, the landing preview must be updated together with this dashboard change.

The tenant-dashboard preview should show:

- tenant header/context;
- KPI cards;
- clear KPI-to-projects divider;
- compact project search/sort controls;
- project card/list example.

It must not show removed first-version sections such as projects-needing-attention, recent-activity detail panels, or worker sidebars.

## Frontend contract

The tenant dashboard page should:

- load the dashboard summary once for the current tenant;
- render loading skeleton/state, error retry, and empty project state;
- render KPI cards using shared design-system primitives;
- render a strong divider between KPI and projects;
- render the projects selector/list directly in the page without an additional outer card;
- support client-side project search and sorting against the summary payload;
- preserve existing project open and project creation behavior;
- use semantic tokens and support dark mode/responsive layouts.

## Documentation changes applied

This CR updates:

- `product/features/dashboard.md`
  - Tenant Dashboard redefined as header + KPI cards + divider + projects.
  - Explicitly excludes extra panels from the first version.
- `product/features/landing-page.md`
  - Tenant dashboard landing preview must match the implemented layout and must not show removed dashboard panels.
- `system/interfaces.md`
  - Adds `GET /tenants/:tenant_id/dashboard` with compact response shape.
- `system/architecture.md`
  - Documents backend aggregate endpoint and frontend composition rule.
- `product/features/bugs.md` and `system/entities.md`
  - Align bug status names with implemented enum values (`in_progress`, `wont_fix`).

## Acceptance criteria

1. The tenant-level dashboard remains the entry point before project selection.
2. The page shows KPI cards for projects, documentation, open bugs, active CRs, comments/collaboration, and recent activity count.
3. The projects section appears immediately after KPI cards, separated by a clearly visible divider.
4. The projects selector/list is not wrapped in an additional outer card/container.
5. Users can search projects by name or slug.
6. Users can sort projects by name, recent activity, open bugs, active CRs, or documentation sync.
7. Project cards remain easy to scan and open the selected project.
8. Empty, low-data, loading, and error states are intentionally handled.
9. Aggregates are tenant-scoped and role-safe.
10. The dashboard endpoint returns compact summaries and avoids N+1 frontend list calls.
11. Existing tenant/project navigation behavior remains unchanged.
12. Tests cover the summary endpoint aggregation logic.
13. Frontend lint/typecheck and backend lint/typecheck pass.

## Out of scope

- Billing, pricing, quota enforcement, or usage-based metering.
- Live real-time dashboard updates via websockets.
- Complex analytics charts, custom report builders, exports, or BI-style filtering.
- Cross-tenant administration views.
- Projects-needing-attention panel.
- Recent activity detail panel.
- Worker status side panel.
- Changing project-level dashboard behavior except where shared components are reused.
- Introducing materialized analytics storage unless profiling proves it is necessary.
