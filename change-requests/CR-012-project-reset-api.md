---
title: "Project Data Reset API"
status: applied
author: "roberto"
created-at: "2026-03-19T00:00:00.000Z"
---

# CR-012: Project Data Reset API

## Summary

Add an API endpoint to reset (wipe) all content from a project — documents, CRs, bugs, and related comments/notifications — without deleting the project itself or its API keys.

## Problem

During development and testing of CLI sync, corrupted or stale data accumulates on the remote. The only option to get a clean slate is to delete and recreate the project, losing API keys and configuration.

## Solution

A `reset_project_data()` service function called from two routes:
- **Web**: `POST /tenants/{tenant_id}/projects/{project_id}/reset` (JWT auth, owner/admin)
- **CLI**: `POST /cli/reset` (API key auth)

Both require `confirm_slug` in the body matching the project slug as a safety mechanism.

### Deletion order (single transaction)

1. Comments (orphan cleanup via entity_id subqueries)
2. Notifications (orphan cleanup via entity_id subqueries)
3. Bugs
4. Change Requests
5. Document Files
6. Audit log event `project.reset` with deletion counts

Preserved: Project, API keys, existing audit log entries.

### CLI command

`sdd remote reset --confirm <slug>` — calls the API and clears local `remote-state.json`.

## Affected files

**Backend:**
- `app/services/project_reset.py` (new)
- `app/schemas/projects.py`
- `app/api/projects.py`
- `app/api/cli.py`
- `tests/test_projects.py`

**CLI (sdd-core):**
- `remote/types.ts`, `remote/api-client.ts`, `remote/sync-engine.ts`
- `sdd.ts`, `commands/remote.ts`, `index.ts`
