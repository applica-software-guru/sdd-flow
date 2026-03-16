---
title: "Change Request Management"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
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

### CR List & Filtering

- List CRs with filters: status, author, date range
- Search by title or body text
- Sort by created date, last modified, status

### CR Detail View

- Full markdown body rendered
- Status badge and transition buttons
- Assignment (who should review/apply)
- Activity log (status changes, comments)

### CR Review

- Admins and Members can approve or reject a CR
- Optional review comment when changing status
- Approved CRs appear in `sdd cr pending` via the API

### CR Assignment

- Assign a CR to a team member for review or implementation
- Assignee receives a notification

## Agent Notes

- The SDD CLI uses only `draft` and `applied` statuses. The `approved`, `rejected`, and `closed` statuses are additions for the web workflow. When the CLI fetches pending CRs via API, it should receive CRs with status `approved`.
- CR body format must be compatible with the SDD CLI frontmatter format for bidirectional sync.
