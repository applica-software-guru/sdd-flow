---
title: "Audit log entries show empty Author and Action, unreadable JSON Details and unclear Entity"
status: resolved
author: "roberto"
created-at: "2026-03-20T00:00:00.000Z"
---

## Description

The Audit Log page is largely unusable: the **Author** and **Action** columns are always empty, the **Entity** column shows an opaque truncated UUID instead of a recognizable object, and the **Details** column renders a raw JSON blob that requires developer knowledge to interpret.

Root cause: the backend API contract and the frontend expectations diverge. The frontend (`code/frontend/src/types/index.ts` → `AuditLogEntry`, and `code/frontend/src/pages/system/AuditLogPage.tsx`) expects `action`, `user` (resolved user object) and human-readable details, while the backend (`code/backend/app/api/audit_log.py` → `AuditLogResponse`) returns `event_type`, a raw `user_id` UUID and a raw `details` dict.

Note: BUG-005 already fixed the visual overflow/monospace formatting of the Details column. This bug covers the *semantic* problems (what is displayed, not how it is laid out).

## Symptoms

### 1. Author column always empty ("Unknown" + "?")

- `AuditLogPage.tsx` renders `entry.user?.display_name`, falling back to `"Unknown"` and `"?"`.
- The backend `AuditLogResponse` only returns `user_id: UUID | None`; it never resolves the `User` document, so the `user` object the frontend expects does not exist.
- `system/interfaces.md` (§ Audit Log) actually specifies `{ items: [{ id, event_type, user, entity_type, entity_id, details, created_at }] }` — the `user` object is part of the declared contract but was never implemented.

### 2. Action column always empty

- `AuditLogPage.tsx` renders `entry.action` inside a badge.
- The backend returns `event_type`, not `action` → `entry.action` is `undefined` and the badge renders empty.
- The event data exists (e.g. `cr.created`, `bug.transitioned`, `project.archived`) — it is purely a field-name mismatch.

### 3. Entity column unclear

- The column renders `entity_type` (e.g. "change request") plus the first 8 chars of `entity_id` (e.g. `3f2a91c0...`).
- A truncated UUID is meaningless to end users. The entry should identify the target by its human-readable label (e.g. the project name, CR title, bug title, document filename, API key name).
- Since the audit log is append-only and referenced entities can be deleted (see `project_reset.py` which deletes projects/bugs/CRs/docs), the label must be **captured at write time** (denormalized into the entry), not resolved at read time.

### 4. Details column is a raw JSON blob

- `AuditLogPage.tsx` renders `JSON.stringify(entry.details, null, 2)`.
- Current payloads are machine-oriented single-key dicts: `{"new_status": "open"}`, `{"created": 2, "updated": 0}`, `{"deleted_bugs": 3, "deleted_change_requests": 1, ...}`.
- Users cannot understand `{"new_status":"applied"}` without knowing internal key names. Details need a human-readable representation: a generated summary line and/or label/value pairs with friendly labels.

### 5. Filters silently broken (discovered during analysis)

- `useAuditLog.ts` sends query params `action`, `entity_type`, `user_id`.
- The backend endpoint only accepts `event_type` (exact match) and ignores the others entirely.
- Result: typing in the "Filter by action..." input or picking an entity type does not filter anything client-side and would return unfiltered data; if the backend ever validated strictly it would 422. Additionally `event_type` exact match is too strict for a UX filter (users type partial text like "bug").
- `system/interfaces.md` also declares `project_id`, `from`, `to` filters that are not implemented at all.

## Affected code

| File | Problem |
|---|---|
| `code/backend/app/api/audit_log.py` | Response lacks `action` and resolved `user`; no `action`/`entity_type`/`user_id`/date filters; no entity label |
| `code/backend/app/models/audit_log_entry.py` | No field to store the denormalized entity label / human-readable summary |
| `code/backend/app/services/audit.py` | `log_event()` does not capture entity label or summary |
| All `log_event` callsites (`app/api/*.py`, `app/services/project_reset.py`) | Pass raw dicts with machine keys, no label |
| `code/frontend/src/types/index.ts` (`AuditLogEntry`) | Declares `action`, `user: User` — must be matched by backend |
| `code/frontend/src/pages/system/AuditLogPage.tsx` | Renders `entry.action`, `entry.user`, raw JSON details, UUID entity |
| `code/frontend/src/hooks/useAuditLog.ts` | Sends `action`/`entity_type` params the backend ignores |
| `code/backend/tests/test_audit_log.py` | Asserts only `event_type`/`user_id`; must cover the new contract and filters |
| `product/features/audit-log.md`, `system/interfaces.md` | Contract docs must reflect the fixed API |

## Implementation plan

### Step 1 — Backend model: self-describing entries

In `code/backend/app/models/audit_log_entry.py` add optional, backwards-compatible fields:

- `entity_label: Optional[str]` — human-readable name of the target captured at write time (e.g. `"Fix login redirect"`, `"api-prod-key"`).
- `summary: Optional[str]` — one-line human-readable description of the event (e.g. `"moved to applied"`, `"archived"`).

Keep existing fields unchanged (append-only log: never migrate/rewrite existing entries; old entries simply have empty optional fields).

### Step 2 — Backend service: capture label and summary at write time

- Extend `log_event()` in `code/backend/app/services/audit.py` with optional `entity_label: str | None` and `summary: str | None` parameters, persisted into the new fields.
- Update every `log_event` callsite (`projects.py`, `bugs.py`, `change_requests.py`, `docs.py`, `tenants.py`, `api_keys.py`, `project_reset.py`) to pass:
  - `entity_label`: project name / bug title / CR title / doc filename / API key name / tenant name / target email (for member events). Use the object available in scope at creation time; for events on objects that no longer exist in scope (e.g. `project.reset` before deletion), capture the label before mutating.
  - `summary`: short sentence with the key fact, e.g. `"created"`, `"status: open → applied"` (for transitions include old and new status), `"2 documents created, 0 updated"` (for bulk), `"reset: 3 bugs, 1 CR, 5 docs deleted"`.

### Step 3 — Backend API: fix the response contract and filters

In `code/backend/app/api/audit_log.py`:

- Add `action: str` to `AuditLogResponse` (alias of `event_type`, keeping `event_type` for backwards compatibility).
- Add `entity_label: str | None` and `summary: str | None` passthrough.
- Resolve users in batch (single query on `User` for the page's distinct `user_id`s, to avoid N+1) and embed `user: { id, display_name, email } | None` in each item.
- Filters (all optional, combinable):
  - `action: str` — case-insensitive substring match on `eventType` (powers the "Filter by action" input).
  - `entity_type: str` — exact match.
  - `user_id: UUID` — exact match.
  - `from: datetime`, `to: datetime` — range on `createdAt` (declared in `system/interfaces.md`, currently missing).
- Keep `event_type` query param working for backwards compatibility (exact match).
- Enforcement of Owner/Admin-only visibility must be verified against `get_current_tenant_member` per `product/features/audit-log.md`.

### Step 4 — Frontend types and hook

- Update `AuditLogEntry` in `code/frontend/src/types/index.ts` to the final contract: `action`, `user: { id, display_name, email } | null`, `entity_type`, `entity_id`, `entity_label?`, `summary?`, `details?`.
- `useAuditLog.ts` already sends `action`/`entity_type`/`user_id` — after Step 3 these will work; optionally add `from`/`to` support.

### Step 5 — Frontend Audit Log page

In `code/frontend/src/pages/system/AuditLogPage.tsx`:

- **Author**: render `entry.user.display_name` (fallback only if truly null, e.g. system events); keep avatar initials.
- **Action**: render `entry.action` — the badge is now populated. Optionally map known event types to friendly labels (`cr.created` → "Created").
- **Entity**: render `entry.entity_label ?? entry.entity_id` with the entity type as secondary text; drop the raw truncated UUID display when a label exists.
- **Details**: replace the raw `JSON.stringify` with a human-readable rendering:
  1. If `summary` is present, show it as the primary text.
  2. Below it, render `details` as friendly key/value chips with humanized labels (`new_status` → "New status", `created` → "Created count", `deleted_bugs` → "Bugs deleted") — keep the existing monospace/overflow treatment from BUG-005 as fallback for unknown/complex payloads.

### Step 6 — Tests

- Update `code/backend/tests/test_audit_log.py`:
  - assert `action` mirrors `event_type`;
  - assert `user.display_name`/`user.email` are resolved;
  - assert `entity_label` and `summary` round-trip;
  - assert filtering by `action` (substring), `entity_type`, `user_id`, `from`/`to`.
- Add a test that `log_event` persists `entity_label`/`summary` (unit test on the service).
- Frontend: extend the existing page/hook tests if present; at minimum verify the details renderer produces friendly labels for known keys.

### Step 7 — Docs update and sync

- Update `system/interfaces.md` (§ Audit Log) to the final contract: response with `action`, `user`, `entity_label`, `summary`; query params `action`, `entity_type`, `user_id`, `from`, `to`.
- Update `product/features/audit-log.md` "Audit Log View" section: entries show entity label and human-readable summary; filters by action (text search), entity type, user and date range.
- Run `sdd sync` for the changed docs, implement, then `sdd mark-synced` and commit.

## Acceptance criteria

1. Every audit entry on the page shows a real user name in Author (or an explicit "System" marker when `user_id` is null) — never "Unknown" for user actions.
2. The Action badge always shows the event (e.g. `bug.transitioned`), never empty.
3. The Entity column shows the captured human-readable label; the raw UUID appears only as fallback for legacy entries without `entity_label`.
4. Details shows a readable summary plus friendly key/value pairs; raw JSON only for unrecognized payloads; no layout regressions (BUG-005 still holds).
5. Filtering by action text, entity type and user works end-to-end; date-range filters work per the documented contract.
6. Backend tests cover the new contract; all existing tests pass.
7. `system/interfaces.md` and `product/features/audit-log.md` match the implemented API, then are marked synced and committed.
