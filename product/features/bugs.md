---
title: "Bug Tracking"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
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

### Bug List & Filtering

- Filter by status, severity, author, assignee, date range
- Search by title or body text
- Sort by severity, created date, last modified

### Bug Detail View

- Full markdown body rendered
- Status badge and transition buttons
- Severity indicator
- Assignment
- Activity log

### Bug Assignment

- Assign a bug to a team member
- Assignee receives a notification

## Agent Notes

- The SDD CLI uses only `open` and `resolved` statuses. The additional statuses are for the web workflow. When the CLI fetches open bugs via API, it should receive bugs with status `open` or `in-progress`.
- Bug body format must be compatible with the SDD CLI frontmatter format.
