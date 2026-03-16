---
title: "Dashboard"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# Dashboard

## Overview

The dashboard provides an at-a-glance overview of all projects within the current tenant and quick access to pending work.

## Features

### Tenant Dashboard

- List of all projects with summary stats per project:
  - Open bugs count (with severity breakdown)
  - Pending CRs count
  - Documentation sync status (percentage synced)
- Global activity feed: recent events across all projects
- Quick actions: create project, switch tenant

### Project Dashboard

- Summary cards:
  - Open bugs (clickable, links to filtered bug list)
  - Pending CRs (clickable, links to filtered CR list)
  - Docs pending sync (clickable, links to filtered doc tree)
  - Team members count
- Recent activity feed for this project
- Quick actions: create CR, report bug, view docs
- Assigned to me: list of CRs and bugs assigned to the current user
