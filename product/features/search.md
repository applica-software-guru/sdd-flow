---
title: "Search & Filtering"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# Search & Filtering

## Overview

Global search and per-entity filtering allow users to quickly find CRs, bugs, and documentation across all projects in a tenant.

## Features

### Global Search

- Search bar in the header, accessible from any page
- Searches across: CR titles/bodies, bug titles/bodies, documentation content
- Results grouped by type (CRs, Bugs, Docs) with project name shown
- Keyboard shortcut: `Cmd+K` / `Ctrl+K`

### Entity Filters

Each list view (CRs, Bugs, Docs) has contextual filters:

- **CRs**: status, author, assignee, date range
- **Bugs**: status, severity, author, assignee, date range
- **Docs**: status (new/changed/synced/deleted), file path

### Saved Filters

- Users can save filter combinations as named views (e.g., "My open bugs", "Pending CRs this week")
- Saved filters appear in the sidebar for quick access

## Agent Notes

- Use PostgreSQL full-text search (`tsvector` / `tsquery`) for the global search — no external search engine needed for v1
- Filter state is reflected in URL query params so links are shareable
