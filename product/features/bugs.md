---
title: "Bug Tracking"
status: synced
author: ""
last-modified: "2026-04-01T00:00:00.000Z"
version: "1.3"
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
- Assignment
- Activity log
- Comments are rendered with the same shared markdown viewer for consistent formatting

### Bug Assignment

- Assign a bug to a team member
- Assignee receives a notification

## Agent Notes

- The SDD CLI uses only `open` and `resolved` statuses. The additional statuses are for the web workflow. When the CLI fetches open bugs via API, it should receive bugs with status `open` or `in-progress`.
- Bug body format must be compatible with the SDD CLI frontmatter format.
- `number` and `slug` are server-generated at creation and immutable. Do not expose a slug edit field in the UI. `formatted_number` is `number` zero-padded to at least 3 digits and is computed, not stored.
