---
title: "Change Request Management"
status: synced
author: ""
last-modified: "2026-09-04T00:00:00.000Z"
version: "1.5"
---

# Change Request Management

## Overview

Change requests (CRs) describe modifications to a project's SDD documentation. They mirror the `change-requests/` directory in the SDD CLI but are managed through the web UI and API.

## CR Lifecycle

```
draft → approved → applied → closed
  │                            ▲
  └──── rejected ──────────────┘
```

| Status | Description |
|--------|-------------|
| **draft** | Author is still writing the CR |
| **approved** | Reviewed and approved, ready for the agent to apply |
| **rejected** | Reviewed and rejected, will not be applied |
| **applied** | Agent has applied the CR to documentation |
| **closed** | CR is complete (auto-set after applied, or manually after rejected) |

## Features

### Create CR

- Title (required)
- Body in Markdown (required) — describes what to change and why
- Target files — optional list of documentation files affected
- Author is set automatically to the current user
- A **progressive number** (scoped to the project, zero-padded to 3 digits, e.g. `001`) and an immutable **slug** (derived from the title) are assigned automatically at creation. Neither can be changed afterwards.

### Assign CR

- Any tenant member can assign or unassign a CR, at creation and at any time afterwards
- Assignment is only possible to active tenant members
- Every assignment change appends an entry to the append-only **assignment history** (who was assigned, by whom, when), visible on the CR detail page
- The new assignee receives a notification; the change is recorded in the audit log as `cr.assigned` with previous and new assignee

### CR List & Filtering

- List CRs with filters: status, author, assignee, date range
- Each entry shows author and assignee display names
- Search by title or body text
- Sort by progressive number descending by default (newest first); also supports created date, last modified, status
- Date fields display both date and time

### CR Detail View

- Full markdown body rendered
- Shared markdown viewer with GFM support (tables, task lists, syntax-highlighted code blocks, heading anchors)
- Status badge and transition buttons
- **Transition & assignment band**: AUTHOR, ASSIGNEE, and ASSIGN TO are shown in the same section as the "Transition to" controls (no separate card). Assignment history remains available as an expandable block inside the same band.
- Activity log (status changes, comments)
- Comments are rendered with the same shared markdown viewer for consistent formatting; each comment shows the commenter's avatar initials, display name, and a date + time timestamp.
- The comments section has an anchor (`id="comments"`); a **floating action button** appears at the bottom-right of the viewport while the comments section is below the fold. It shows the comment count as a badge and, on click, smooth-scrolls to the comments and focuses the comment input. The button hides automatically when the comments section is already visible. Supports dark mode and is accessible (`aria-label`).

### CR Review

- Admins and Members can approve or reject a CR
- Optional review comment when changing status
- Approved CRs appear in `sdd cr pending` via the API

### CR Assignment

- Assign a CR to a team member for review or implementation
- Assignee receives a notification

### CR Comment & Content-Change Notifications

- When a comment is added, all **actors** of the CR — author, current assignee (if any), and all distinct previous commenters, excluding the comment author and inactive tenant members — receive an in-app notification (`comment_added`) and, by default (email preference on), an email with a deep link to the CR's comments section
- When a comment is added, the event is recorded in the audit log as `cr.commented`
- When a CR's title or body is actually modified (no-op saves trigger nothing), all actors receive an in-app notification (`content_changed`); email is sent only to actors who explicitly enabled the `content_changed` email preference (default: off)
- The content change is recorded in the audit log as `cr.content_changed` with the changed fields in the details
- Notification/email dispatch failures never fail the triggering action
- Multiple comments on the same CR within a 5-minute window are coalesced into a single email per recipient

## Agent Notes

- The SDD CLI uses only `draft` and `applied` statuses. The `approved`, `rejected`, and `closed` statuses are additions for the web workflow. When the CLI fetches pending CRs via API, it should receive CRs with status `approved`.
- CR body format must be compatible with the SDD CLI frontmatter format for bidirectional sync.
- `number` and `slug` are server-generated at creation and immutable. Do not expose a slug edit field in the UI. `formatted_number` is `number` zero-padded to at least 3 digits and is computed, not stored.
