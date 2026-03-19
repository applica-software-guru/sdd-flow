---
title: "Bidirectional delete sync and deleted status for all entities"
status: applied
author: "roberto"
created-at: "2026-03-19T00:00:00.000Z"
---

# CR-014: Bidirectional delete sync and deleted status for all entities

## Summary

Enable bidirectional deletion propagation between the local filesystem and SDD Flow. When a file is deleted locally and the user runs `sdd push`, the corresponding entity is marked as `deleted` on remote. When an entity is deleted on remote and the user runs `sdd pull`, the local file is removed. Additionally, introduce a `deleted` status for Change Requests and Bugs (Documents already had one), and add status filters across all frontend list views so that deleted items are hidden by default but still accessible.

## Problem

1. **Local deletions are ignored**: If a developer deletes a CR, bug, or doc file locally and runs `sdd push`, nothing happens on the remote — the entity stays alive, and the next `sdd pull` recreates the file.

2. **Remote deletions are ignored**: If someone deletes an entity on SDD Flow, `sdd pull` has no way to detect the absence and remove the local file.

3. **CRs and Bugs lack a `deleted` status**: Documents have `DocStatus.deleted`, but CRs and Bugs only have `closed`. Closing and deleting are semantically different — a closed CR was intentionally concluded, a deleted one was removed.

4. **No status filter on Documents page**: The Documentation list view has no filter dropdown, unlike CRs and Bugs. Users cannot filter by status or view deleted documents.

## Solution

### Backend changes

#### New enum values
- Add `deleted` to `CRStatus` enum (`cr_status_enum`)
- Add `deleted` to `BugStatus` enum (`bug_status_enum`)
- Alembic migration `c3d4e5f6a7b8` adds both values via `ALTER TYPE ... ADD VALUE`

#### New CLI endpoints
- `POST /cli/delete-docs` — accepts `{ paths: string[] }`, sets matching documents to `DocStatus.deleted`
- `POST /cli/delete-crs` — accepts `{ paths: string[] }`, sets matching CRs to `CRStatus.deleted`
- `POST /cli/delete-bugs` — accepts `{ paths: string[] }`, sets matching bugs to `BugStatus.deleted`

#### Updated list endpoints (exclude deleted by default)
- `GET /tenants/.../change-requests` — when no `status` filter is provided, excludes `CRStatus.deleted`
- `GET /tenants/.../bugs` — when no `status` filter is provided, excludes `BugStatus.deleted`
- `GET /tenants/.../docs` — now accepts an optional `?status=` query parameter; when omitted, excludes `DocStatus.deleted` (existing behavior preserved, now explicit)

#### New Pydantic schemas
- `DocDeleteRequest`, `DocDeleteResponse`
- `CRDeleteRequest`, `CRDeleteResponse`
- `BugDeleteRequest`, `BugDeleteResponse`

### CLI changes (sdd-core 1.8.0)

#### Push — local deletion detection
During `pushToRemote`, after pushing modified files, the engine compares `remote-state.json` entries against the filesystem. Paths tracked in state but missing from disk are collected and sent to the corresponding delete endpoint. The state entries are then cleaned up.

#### Pull — remote deletion detection
During `pullFromRemote`, `pullCRsFromRemote`, and `pullBugsFromRemote`, the engine compares state entries against the remote response. Entities tracked locally but absent from the response are considered remotely deleted:
- If the local file has **not** been modified (hash matches state), it is deleted from disk.
- If the local file **has** been modified, a conflict is reported instead of silently deleting.

#### Updated types
- `PushResult.deleted: string[]`
- `PullResult.deleted: string[]`
- `PullEntitiesResult.deleted: number`
- New `RemoteDeleteResponse` type

#### Updated CLI output
- `sdd push` shows deleted files in red with `(deleted)` suffix and includes deletion count in summary
- `sdd pull` shows deleted files in red with `-` prefix and includes deletion count in summary

### Frontend changes

#### Types
- `CRStatus` union type: added `'deleted'`
- `BugStatus` union type: added `'deleted'`
- `DocStatus` union type: added `'draft'` (was missing)

#### List pages — filter dropdowns
- **CRListPage**: added "Deleted" option to status filter
- **BugListPage**: added "Deleted" option to status filter
- **DocsTreePage**: added a status filter dropdown (Draft, New, Changed, Synced, Deleted) — previously had no filter at all

#### Default behavior
"All statuses" (empty filter) hides deleted items — the backend excludes them when no status parameter is sent. Users can explicitly select "Deleted" to view soft-deleted entities.

#### StatusBadge
Already had a `deleted` color mapping (`bg-red-100 text-red-700`), so no changes needed.

## Sync behavior matrix

| Scenario | Action |
|---|---|
| File deleted locally, push | Delete on remote, clean state |
| File deleted on remote, pull (local unmodified) | Delete local file, clean state |
| File deleted on remote, pull (local modified) | Conflict reported |
| File modified locally, push | Update on remote |
| File modified on remote, pull (local unmodified) | Update local file |
| File modified on remote, pull (local modified) | Conflict reported |
