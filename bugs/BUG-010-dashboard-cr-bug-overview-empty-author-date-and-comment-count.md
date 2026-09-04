---
title: "CR/Bug overview: 'by' author always empty, timestamps shown where date-only is wanted, and no active comment count"
status: resolved
author: "roberto"
created-at: "2026-09-04T10:29:21.000Z"
---

## Proposed scope (to review before implementing)

This bug is about the CR/Bug **overview** surfaces of a project:

- the **project dashboard** at `/tenants/:tenantId/projects/:projectId` →
  `code/frontend/src/pages/project/DashboardPage.tsx` ("Recent Change Requests"
  and "Recent Bugs" panels); and, for the same three issues,
- the **CR and Bug list pages** (tables) at `/change-requests` and `/bugs` →
  `pages/change-requests/ListPage.tsx`, `pages/bugs/ListPage.tsx`.

The three reported points map to concrete code as follows:

1. **Show only the date, not the time** — on the dashboard rows the date is
   already date-only, but the CR/Bug list tables render the `Created` column
   with `toLocaleString()` (full timestamp with hours/minutes). Fix: the whole
   overview must show date-only, consistently.
2. **The "by" is always empty** — the dashboard row meta is a hardcoded
   `by on {date}` string (no author is ever read), so the creator of the CR/bug
   is never visible. The API already resolves `author` (see BUG-009), so this is
   a pure frontend gap.
3. **Show the number of active comments** — decide presentation (D1 below): an
   extra "Comments" column on the list tables and/or an inline count on the
   dashboard row meta line ("la revisione" in the report = the row meta line
   under the title; there is no other "revision" concept for CR/bugs in the app).

### Decisions (proposed, pending review)

- **D1 — Comment count presentation**: inline chip on the dashboard row meta
  line (`by {author} · {date} · 💬 N`) **and** a "Comments" column on the CR/Bug
  list tables (hidden below `lg`, like the `Created` column). Both read the same
  new `comments_count` field, so the cost is one backend field, two UIs.
- **D2 — Data source for the count**: batch `comments_count` computed by the
  backend on CR/Bug responses (list + get), via one MongoDB aggregation per
  entity type (no N+1, no extra round-trips from the dashboard).
- **D3 — "Active" comments**: the `Comment` model has no soft-delete, so every
  comment is active; `comments_count` = all comments for the entity.
- **D4 — Date format**: date-only everywhere in these surfaces (shared frontend
  helper, no timezone/time suffix).

## Description

The project dashboard shows, per project, a "Recent Change Requests" and a
"Recent Bugs" overview. Each row currently renders:

```tsx
<p className="text-xs ...">
  by on{' '}
  {new Date(cr.created_at).toLocaleDateString()}
</p>
```

This produces a literal `by on 9/4/2026` — the "by" is a hardcoded placeholder
with no author name, so the user who created the CR/bug is invisible even though
the resolved author is already in the payload. The related CR/Bug list tables
show the creation timestamp with the time of day (`toLocaleString()`), which is
more precision than wanted. Finally, none of these surfaces exposes how much
discussion an item has generated, making it hard to spot items that need
attention (an open review with many comments) from the overview alone.

## Symptoms

### 1. Dashboard rows: "by" always empty (author never rendered)

- `code/frontend/src/pages/project/DashboardPage.tsx:195` (CR row) and `:234`
  (bug row) hardcode `by on{' '}` followed by the date — `cr.author` /
  `bug.author` are never read.
- The data is already there: `CRResponse`/`BugResponse` resolve
  `author: UserBrief | None` (BUG-009), the TS types already carry
  `author?: UserBrief | null`, and `UserCell` already knows how to render a
  user with initials.

### 2. Timestamps with time where date-only is wanted

- `code/frontend/src/pages/change-requests/ListPage.tsx:147` and
  `code/frontend/src/pages/bugs/ListPage.tsx:176` render the `Created` column
  with `new Date(...).toLocaleString()` → "9/4/2026, 12:34:56" instead of
  date-only.

### 3. No active comment count in any overview

- CR/Bug list responses carry no comment count; comments are stored in a
  separate `comments` collection (`Comment.model`, keyed by `entityType` +
  `entityId`) and are only fetched per entity by the detail pages via
  `GET .../comments` (`code/backend/app/api/change_requests.py:327`,
  `bugs.py:331`). The dashboard would need 1 request per row to count them —
  that is why the count must come from the backend response.

## Affected code

| File | Problem |
|---|---|
| `code/frontend/src/pages/project/DashboardPage.tsx` | Row meta hardcodes `by on {date}` — author never shown (lines 195, 234); no comment count |
| `code/frontend/src/pages/change-requests/ListPage.tsx` | `Created` column shows time (`toLocaleString()`, line 147); no Comments column |
| `code/frontend/src/pages/bugs/ListPage.tsx` | Same as above (line 176) |
| `code/frontend/src/types/index.ts` | `ChangeRequest`/`Bug` lack `comments_count` |
| `code/backend/app/schemas/change_requests.py` / `bugs.py` | `CRResponse`/`BugResponse` lack `comments_count` |
| `code/backend/app/api/change_requests.py` / `bugs.py` | List/get endpoints do not attach comment counts |
| `code/backend/app/repositories/comment_repository.py` | No batched count-by-entity method |
| `code/backend/tests/test_change_requests.py`, `test_bugs.py` | No coverage for comment counts |

## Implementation plan

### Step 1 — Backend: batched `comments_count`

- Add `CommentRepository.count_by_entities(entity_type: str, entity_ids: list[UUID]) -> dict[UUID, int]`
  — one aggregation on `comments`: `$match {entityType, entityId: {$in: ids}}`
  (convert ids with `uuid_to_bin` like `delete_by_project_entities`) + `$group`
  by `entityId`, then map back with `bin_to_uuid`.
- Add `comments_count: int = 0` to `CRResponse` and `BugResponse`
  (backwards-compatible default).
- In `api/change_requests.py` and `api/bugs.py`: after `_attach_users(...)`,
  attach counts on **list** (`list_crs`/`list_bugs`) and on **single-entity**
  responses that may already have comments (`get_cr`/`get_bug`; also the
  mutation endpoints `update`/`transition`/`assign` for correctness, one small
  extra call each). Creation returns 0, which is correct by construction.

### Step 2 — Frontend: types + shared date formatter

- `ChangeRequest` and `Bug` gain `comments_count?: number`.
- Add a tiny shared helper (e.g. `code/frontend/src/lib/format.ts`):
  `formatDateOnly(iso: string) => string` wrapping `toLocaleDateString()` — the
  single source of the date-only rule (D4).

### Step 3 — Dashboard rows (points 1 and 2)

- `DashboardPage.tsx`, CR and Bug rows: meta line becomes
  `by {author?.display_name ?? 'Unknown'} · {formatDateOnly(created_at)}` and an
  inline comment chip (`💬 {comments_count ?? 0}`, hidden when the item has no
  comments or the field is still undefined from a cached payload). Reuse the
  UserCell initials pattern for the author, or keep it as plain text — pick the
  compact variant; do **not** introduce a time component (D4).

### Step 4 — List pages (points 1 and 3)

- Replace `toLocaleString()` in the `Created` cells with `formatDateOnly(...)`.
- Add a "Comments" header + cell on both tables (`hidden lg:table-cell`, like
  the `Created` column) rendering `comments_count` with a speech-bubble icon and
  tooltip "active comments"; `—`/empty when 0 or undefined.

### Step 5 — Tests

- Backend: extend `test_change_requests.py`/`test_bugs.py` — list and get
  return `comments_count` matching the comments actually posted for that entity;
  counts are scoped per entity type/id (a bug's comments do not count toward a
  CR); zero when no comments; count does not leak across pages.
- Frontend: if a component test pattern exists, cover the dashboard meta line
  and the Comments column; otherwise manual check + screenshots.

### Step 6 — Sync

- Run `sdd sync`, implement, `sdd mark-synced`, commit immediately after.

## Acceptance criteria

1. The dashboard "Recent Change Requests"/"Recent Bugs" rows show the real
   creator (no more dangling `by on ...`), a date-only creation date, and the
   number of active comments.
2. The CR and Bug list tables show date-only in `Created` and include a
   "Comments" column with the active comment count.
3. Comment counts come from a single batched backend query — no N+1 and no new
   per-row API calls from the frontend.
4. No other place regresses to showing the time for these entities.
5. Backend tests cover the new `comments_count` behaviour; all existing tests
   pass.
