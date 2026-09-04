---
title: "Bug Tracking"
status: synced
author: ""
last-modified: "2026-09-04T00:00:00.000Z"
version: "1.5"
---

# Bug Tracking

## Overview

Bugs describe defects found in a project. They mirror the `bugs/` directory in the SDD CLI but are managed through the web UI and API.

## Bug Lifecycle

```
open → in-progress → resolved → closed
  │                               ▲
  └──── wont-fix ─────────────────┘
```

| Status | Description |
|--------|-------------|
| **open** | Bug reported, not yet being worked on |
| **in-progress** | Someone is actively fixing it |
| **resolved** | Fix has been applied |
| **wont-fix** | Decided not to fix |
| **closed** | Bug is complete (auto-set after resolved, or manually after wont-fix) |

## Features

### Create Bug

- Title (required)
- Body in Markdown (required) — describes the bug, steps to reproduce, expected vs. actual behavior
- Severity: `critical`, `major`, `minor`, `trivial`
- Author is set automatically
- A **progressive number** (scoped to the project, zero-padded to 3 digits, e.g. `001`) and an immutable **slug** (derived from the title) are assigned automatically at creation. Neither can be changed afterwards.

### Assign Bug

- Any tenant member can assign or unassign a bug, at creation and at any time afterwards
- Assignment is only possible to active tenant members
- Every assignment change appends an entry to the append-only **assignment history** (who was assigned, by whom, when), visible on the bug detail page
- The new assignee receives a notification; the change is recorded in the audit log as `bug.assigned` with previous and new assignee

### Bug List & Filtering

- Filter by status, severity, author, assignee, date range
- Search by title or body text
- Sort by progressive number descending by default (newest first); also supports severity, created date, last modified
- Date fields display both date and time

### Bug Detail View

- Full markdown body rendered
- Shared markdown viewer with GFM support (tables, task lists, syntax-highlighted code blocks, heading anchors)
- Status badge and transition buttons
- Severity indicator
- **Transition & assignment band**: AUTHOR, ASSIGNEE, and ASSIGN TO are shown in the same section as the "Transition to" controls (no separate card). Assignment history remains available as an expandable block inside the same band.
- Activity log
- Comments are rendered with the same shared markdown viewer for consistent formatting; each comment shows the commenter's avatar initials, display name, and a date + time timestamp.
- The comments section has an anchor (`id="comments"`); a **floating action button** appears at the bottom-right of the viewport while the comments section is below the fold. It shows the comment count as a badge and, on click, smooth-scrolls to the comments and focuses the comment input. The button hides automatically when the comments section is already visible. Supports dark mode and is accessible (`aria-label`).

### Bug Assignment

- Assign a bug to a team member
- Assignee receives a notification

### Bug Comment & Content-Change Notifications

- When a comment is added, all **actors** of the bug — author, current assignee (if any), and all distinct previous commenters, excluding the comment author and inactive tenant members — receive an in-app notification (`comment_added`) and, by default (email preference on), an email with a deep link to the bug's comments section
- When a comment is added, the event is recorded in the audit log as `bug.commented`
- When a bug's title or body is actually modified (no-op saves trigger nothing), all actors receive an in-app notification (`content_changed`); email is sent only to actors who explicitly enabled the `content_changed` email preference (default: off)
- The content change is recorded in the audit log as `bug.content_changed` with the changed fields in the details
- Notification/email dispatch failures never fail the triggering action
- Multiple comments on the same bug within a 5-minute window are coalesced into a single email per recipient

## Agent Notes

- The SDD CLI uses only `open` and `resolved` statuses. The additional statuses are for the web workflow. When the CLI fetches open bugs via API, it should receive bugs with status `open` or `in-progress`.
- Bug body format must be compatible with the SDD CLI frontmatter format.
- `number` and `slug` are server-generated at creation and immutable. Do not expose a slug edit field in the UI. `formatted_number` is `number` zero-padded to at least 3 digits and is computed, not stored.
