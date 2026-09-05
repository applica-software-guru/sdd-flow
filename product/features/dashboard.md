---
title: "Dashboard"
status: synced
author: ""
last-modified: "2026-09-05T09:25:00.000Z"
version: "1.1"
---

# Dashboard

## Overview

The dashboard provides an at-a-glance overview of the current tenant and, after a project is selected, of the selected project. The tenant-level dashboard is the authenticated entry state before project selection: it helps users understand tenant-wide SDD volume through KPI cards and then immediately choose a project from a searchable project list.

## Features

### Tenant Dashboard

The tenant dashboard is shown when the user has selected a tenant but no project. The first version intentionally stays focused and contains only:

1. tenant header and actions;
2. tenant-wide KPI overview;
3. searchable/sortable project list.

No additional attention panels, recent activity panels, worker sidebars, or secondary insight sections are shown on the page for now.

Required sections:

1. **Tenant header**
   - Shows the tenant name and a subtitle such as `Overview across all projects`.
   - Keeps project selection context clear: users are at tenant level, not inside a project.
   - Provides `New project` for roles allowed to create projects.
   - Provides tenant settings access only to roles allowed to manage the tenant.
   - Explains that opening a project reveals project-specific docs, CRs, bugs, workers, and settings.

2. **KPI overview**
   - Compact cards summarize tenant-wide project and SDD activity across active projects.
   - The first implementation uses at most six desktop KPI cards and wraps to two or one columns on smaller screens.
   - KPI cards use short labels, trusted counts, optional helper text/tooltips, and semantic status treatment.

Recommended KPI cards:

| KPI | Primary value | Secondary context |
|-----|---------------|-------------------|
| Projects | Active projects | Archived projects when non-zero |
| Documentation | Total documentation files and sync percentage | Files pending sync (`new`, `changed`, `deleted`) |
| Open bugs | Bugs with status `open` or `in_progress` | Critical and major breakdown |
| Active CRs | CRs in active workflow statuses | Review/apply queue count |
| Comments / collaboration | Comments created in the selected window | Distinct commenters in the same window |
| Recent activity | Tenant activity event count in the selected window | Optional compact worker online count as card helper text |

3. **Projects**
   - The project list appears immediately after the KPI cards, separated by a clearly visible divider, without an additional outer card/container around the whole selector area so the page stays compact.
   - Users can search projects by name or slug.
   - Users can sort by name, recent activity, open bugs, active CRs, or documentation sync.
   - Each project row/card shows project name, description, docs synced/total, pending-doc count, open bugs, active CRs, comment count for the selected window, worker online/total, and last activity where available.
   - The primary action opens the project.
   - Secondary actions such as settings, archive, and restore remain permission-gated if shown.
   - For tenants with many projects, client-side search/sort may operate on the aggregate dashboard payload. Server-side pagination/filtering can be introduced later if dataset size requires it.

4. **Empty and low-data states**
   - No projects: show onboarding guidance and `Create your first project` instead of a grid of zero-value KPIs.
   - Projects but no docs/CRs/bugs: show KPI cards with zero/neutral values and the searchable project list.
   - No comments or activity in the selected period: show zero/neutral KPI helper text, not an error state.

### Tenant KPI Semantics

KPI definitions must be stable, documented, and covered by tests.

Default time window:

- The first implementation uses `last_30_days` for comments and activity-volume metrics.
- A later version may add a simple `7 days / 30 days / 90 days` selector.

Count semantics:

- **Active projects**: projects where `archived_at` is null.
- **Archived projects**: projects where `archived_at` is not null; excluded from primary active KPIs unless explicitly shown as secondary text.
- **Total docs**: `DocumentFile` records for active projects, excluding `deleted` unless deleted/pending-deletion files are explicitly shown.
- **Synced docs**: documents with status `synced`.
- **Pending docs**: documents with status `new`, `changed`, or `deleted`.
- **Open bugs**: bugs with status `open` or `in_progress`.
- **Critical/major bugs**: open bugs whose severity is `critical` or `major`.
- **Active CRs**: CRs in non-terminal work statuses, at minimum `draft`, `pending`, and `approved`; excludes `applied`, `closed`, `rejected`, and `deleted`.
- **Review/apply queue**: CRs with status `pending` or `approved`, following the implemented CLI/web status mapping.
- **Comments generated**: comments on CRs and bugs created in the selected time window across active projects.
- **Distinct commenters**: distinct comment authors in the selected time window.
- **Activity events**: meaningful tenant audit-log entries in the selected time window, exposed only as an aggregate KPI count in this first dashboard version.
- **Workers online**: workers whose computed `is_online` value is true across active projects.

### Project Dashboard

After selecting a project, the project dashboard remains project-scoped and shows quick access to work inside that project.

- Summary cards:
  - Open bugs (clickable, links to filtered bug list)
  - Pending CRs (clickable, links to filtered CR list)
  - Docs pending sync (clickable, links to filtered doc tree)
  - Team members count
  - Workers online / total when remote workers are available
- Recent activity feed for this project
- Quick actions: create CR, report bug, view docs, dispatch worker job where supported
- Assigned to me: list of CRs and bugs assigned to the current user

## Agent Notes

- The tenant dashboard should consume a dedicated aggregate API response rather than reconstructing tenant-wide KPIs with many paginated list requests.
- The tenant dashboard visual hierarchy is: header, KPI cards, projects. Do not add additional panels until there is a specific product need.
- The dashboard must remain tenant-scoped and role-safe. Backend authorization is the source of truth; frontend permission hiding is presentation only.
- The tenant dashboard is not a billing or quota-metering feature. KPI numbers describe operational SDD volume and collaboration, not commercial usage limits.
