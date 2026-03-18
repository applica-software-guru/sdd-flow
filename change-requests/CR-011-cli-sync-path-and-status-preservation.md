---
title: "CLI Sync — Path and status preservation for CRs and Bugs"
status: applied
author: "roberto"
created-at: "2026-03-18T00:00:00.000Z"
---

# CR-011: CLI Sync — Path and status preservation for CRs and Bugs

## Summary

Add `path` column to ChangeRequest and Bug entities so the CLI can round-trip filenames through push→pull without generating ID-based duplicates. Also pass-through the local status on push instead of hardcoding `pending`/`open`.

## Problem

1. **Duplicate files on pull**: When the CLI pushes a CR with path `change-requests/001-area-geografica.md`, the backend ignores the path. On pull, the CLI has no way to recover the original filename and falls back to `CR-{id}.md`, creating a duplicate.

2. **Status lost on push**: The backend hardcodes `CRStatus.pending` and `BugStatus.open` on every push, ignoring the local status. A CR marked `applied` locally would revert to `pending` on remote after push.

3. **Frontmatter corruption on pull**: `buildStoryMarkdown` rewrites the entire file on pull, replacing author, timestamps, version, and YAML quoting style — even when the body content hasn't changed.

## Solution

### Backend changes

- Add nullable `path` column (String 1024) to `change_requests` and `bugs` tables
- Store `item.path` in push-crs and push-bugs endpoints (both create and update)
- Return `path` in `CRResponse` and `BugResponse`
- Accept optional `status` in `CRBulkItem` and `BugBulkItem`; use local status when provided, keep existing/default otherwise
- Alembic migration `b2c3d4e5f6a7`

### CLI changes (sdd-core)

- Add `path: string | null` to `RemoteCRResponse` and `RemoteBugResponse`
- Pull resolution priority: `remote.path` → reverse mapping from state → `CR-{id}.md` fallback
- Send `status` field in push payloads for CRs and bugs
- Content-based comparison on pull: skip file if body is identical, surgically replace body only if changed (preserving original frontmatter)

## Affected files

**Backend:**
- `app/models/change_request.py` — add `path` column
- `app/models/bug.py` — add `path` column
- `app/schemas/change_requests.py` — add `path` to `CRResponse`, `status` to `CRBulkItem`
- `app/schemas/bugs.py` — add `path` to `BugResponse`, `status` to `BugBulkItem`
- `app/api/cli.py` — store path, pass-through status
- `alembic/versions/b2c3d4e5f6a7_add_path_to_crs_and_bugs.py` — migration

**CLI (sdd-core):**
- `remote/types.ts` — add `path` to response interfaces
- `remote/sync-engine.ts` — use remote path on pull, send status on push, content-based comparison
