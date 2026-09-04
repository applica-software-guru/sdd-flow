---
title: "CR list shows empty Author and Assignee and there is no flow to assign a CR after creation"
status: resolved
author: "roberto"
created-at: "2026-04-01T00:00:00.000Z"
---

## Decisions (review 2026-04-01)

1. **Permissions (Step 2)**: confirmed — any tenant member can assign/unassign.
2. **Assignment history**: yes — dedicated append-only `assignment_history` collection
   (not derived from the audit log, which is owner/admin-only while assignment
   history is domain data every project member can see). One row per change:
   `{tenant_id, entity_type, entity_id, assignee_id (null = unassigned), assigned_by, created_at}`.
   Seeded at creation when the CR/bug is created with an assignee. Exposed via
   `GET .../{id}/assignments` with resolved display names and shown on the detail page.
3. **Scope (Step 5)**: expanded — fix the same gaps for **Bugs** in the same change
   (endpoint, validation, audit `bug.assigned`, notification, filters, UI, history).

## Description

In the Change Requests list the **Author** and **Assignee** columns are always empty, and there is **no way to assign a CR to someone after it has been created** — neither a dedicated API operation nor a UI control. Assignment currently only works in the creation form.

Same root cause family as BUG-008 (audit log): the backend response carries only raw UUIDs (`author_id`, `assignee_id`) without resolved user objects, and the frontend never had the pieces to display or manage them.

## Symptoms

### 1. Author and Assignee columns always empty

- `code/frontend/src/pages/change-requests/ListPage.tsx` renders hardcoded `{'--'}` in both cells — there is not even an attempt to read the data:
  ```tsx
  <td ...>{'--'}</td>  // Author
  <td ...>{'--'}</td>  // Assignee
  ```
- Upstream, `CRResponse` (`code/backend/app/schemas/change_requests.py`) returns only `author_id: UUID` and `assignee_id: UUID | None` — no resolved user objects, so the UI has no names to show even if it tried.
- The frontend `ChangeRequest` type (`code/frontend/src/types/index.ts`) has no `author`/`assignee` fields either.
- The CR **DetailPage has no author/assignee display at all** (no metadata section shows them), so the information is invisible everywhere, not just in the list.

### 2. No flow to perform the assignment after creation

- **No dedicated endpoint**: `change_requests.py` exposes `POST /{cr_id}/transition` for status changes but nothing for assignment. The only path is the generic `PATCH /{cr_id}` with `CRUpdate.assignee_id`.
- **No validation**: `create_cr` and `update_cr` accept an arbitrary `assignee_id` UUID without checking it belongs to a `TenantMember` of the tenant — it is possible to "assign" a CR to a non-existent or external user.
- **No audit event**: `product/features/change-requests.md` explicitly tracks "assigned" as a CR event, and `log_event` callsites only record `cr.updated` (generic) on PATCH — no `cr.assigned` entry, so the assignment is invisible in the audit trail.
- **No notification**: `create_notification(..., "cr.assigned", ...)` fires only when the assignee is set **at creation time**; changing the assignee later silently skips notification (`update_cr` never notifies).
- **No UI**: the DetailPage offers transitions, edit and comments but no "Assign to..." control. `useUpdateCR` could technically send `assignee_id`, but nothing in the UI calls it for that purpose.
- **Filters silently broken**: `useChangeRequests` sends an `assignee_id` query param that the backend `list_crs` ignores (it only supports `status`). `product/features/change-requests.md` also declares an `author` filter that does not exist.

Note: assignment **at creation time works** — `CreatePage` has a member-populated select (via the tenants members API), the notification fires, so the gap is everything after creation.

## Affected code

| File | Problem |
|---|---|
| `code/backend/app/schemas/change_requests.py` | `CRResponse` lacks resolved `author`/`assignee` user objects |
| `code/backend/app/api/change_requests.py` | No `/assign` endpoint; no member validation; no `cr.assigned` audit event; no notification on reassignment; list endpoint ignores `author_id`/`assignee_id` filters |
| `code/frontend/src/types/index.ts` | `ChangeRequest` lacks `author`/`assignee` resolved fields |
| `code/frontend/src/pages/change-requests/ListPage.tsx` | Author/Assignee cells hardcoded to `--` |
| `code/frontend/src/pages/change-requests/DetailPage.tsx` | No author/assignee metadata, no assign control |
| `code/frontend/src/hooks/useChangeRequests.ts` | No `useAssignCR` mutation; sends `assignee_id` filter the backend ignores |
| `code/backend/tests/test_change_requests.py` | No coverage for assignment flow or resolved users |
| `product/features/change-requests.md`, `system/interfaces.md` | Docs to update once the contract is implemented |

## Implementation plan

### Step 1 — Backend: resolve author/assignee in CR responses

- Add a shared lightweight user schema (e.g. `UserBrief { id, display_name, email }`) — the audit-log fix (BUG-008) already introduced the same shape as `AuditUserResponse`; extract and reuse instead of duplicating.
- `CRResponse` gains `author: UserBrief | None` and `assignee: UserBrief | None` (keep the raw `*_id` fields for compatibility).
- Resolve users in **batch** (single query for the page's distinct ids — same pattern as the audit-log endpoint, no N+1) in both `get_cr` and `list_crs`.

### Step 2 — Backend: dedicated assign operation

- Add `POST /tenants/{tenant_id}/projects/{project_id}/change-requests/{cr_id}/assign` with body `{ assignee_id: UUID | null }` (`null` = unassign).
- Validation: if `assignee_id` is not null, it must correspond to an active `TenantMember` of the tenant → `404/422` otherwise. Unassignment is always allowed.
- Audit: `log_event(..., "cr.assigned", "change_request", cr.id, entity_label=cr.title, summary="assigned to <display_name>" | "unassigned", details={old_assignee, new_assignee})` — consistent with the BUG-008 conventions.
- Notification: when the new assignee differs from the actor, send `create_notification(assignee, tenant_id, "cr.assigned", "change_request", cr.id, ...)` — mirroring the creation-time behavior. No notification on unassign.
- Permission model: **DECIDED — any tenant member** (same access rule as `update_cr`).
- No-op handling: assigning the same assignee that is already set should not audit/notify.
- **Assignment history (DECIDED)**: dedicated append-only `assignment_history` collection (see Decisions above); every change appends one row, seeded at creation when created with an assignee; exposed via `GET .../{cr_id}/assignments` with resolved display names.

### Step 3 — Backend: list filters

- `list_crs` accepts optional `author_id` and `assignee_id` exact-match filters (the docs declare the author filter; the hook already sends `assignee_id`).

### Step 4 — Frontend

- `ChangeRequest` type: add `author`/`assignee` brief objects.
- **ListPage**: render Author and Assignee with display names + avatar initials (same visual pattern as the audit-log User column); fallback `--` only when genuinely absent (e.g. unassigned).
- **DetailPage**: metadata section showing Author and Assignee; an "Assign to..." select (populated from the tenant members API, same source as CreatePage) plus an "Unassign" option, calling a new `useAssignCR` mutation with toasts on success/failure.
- `useChangeRequests`: forward `author_id` filter too; keep `assignee_id` (now actually supported).

### Step 5 — Consistency with Bugs (DECIDED: included)

`app/api/bugs.py` has the exact same gaps (resolved users, `/assign`, validation, audit `bug.assigned`, notification on reassignment, filters). **Scope approved: apply the identical pattern to Bugs in this same change** — endpoint, validation, audit, notification, filters, UI and assignment history.

### Step 6 — Tests

- Backend `test_change_requests.py`:
  - response includes resolved `author`/`assignee` (display_name/email) in get and list;
  - assign endpoint: valid member → 200, audit entry `cr.assigned` with label/summary, notification created for the new assignee; unknown/external user → error; unassign → allowed, audited, no notification; no-op assign → no audit/notification;
  - filters `author_id`/`assignee_id`;
  - PATCH with `assignee_id` keeps working (backwards compatibility).
- Frontend: extend component/hook tests for the list cells and the assign mutation if a pattern exists.

### Step 7 — Docs update and sync

- `system/interfaces.md`: CR endpoints — new `/assign`, response with `author`/`assignee`, list filters.
- `product/features/change-requests.md`: describe post-creation assignment flow (who can assign, unassign, notifications).
- Run `sdd sync`, implement, `sdd mark-synced`, commit.

## Acceptance criteria

1. The CR list shows real names in Author and Assignee for every CR.
2. The CR detail shows author/assignee and provides an assign/unassign control backed by a dedicated endpoint.
3. Assignment is only possible to active tenant members; unassignment is always possible.
4. Every assignment change produces a `cr.assigned` audit entry (with entity label and summary) and a notification for the new assignee (except no-ops and unassign).
5. `author_id`/`assignee_id` list filters work end-to-end.
6. Backend tests cover the whole flow; all existing tests pass.
7. Docs match the implemented contract and are marked synced.
