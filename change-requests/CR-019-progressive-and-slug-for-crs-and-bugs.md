---
title: "Progressive number and immutable slug for CRs and Bugs"
status: applied
author: "roberto"
created-at: "2026-03-24T00:00:00.000Z"
---

# CR-019: Progressive Number and Immutable Slug for CRs and Bugs

## Summary

Add a per-project progressive number and an immutable slug (derived from the title) to both `ChangeRequest` and `Bug` entities. Expose them in all relevant API responses so the SDD CLI can use them to generate canonical file names in the format `<progressive>-<slug>.md`.

## Problem

Currently CRs and bugs have no stable, human-readable identifier beyond their UUID. The `path` field is only set when the entity originates from the CLI, so web-created items lack a canonical file name. The upcoming SDD CLI refactor needs a reliable `<progressive>-<slug>` pair to derive file names without relying on client-generated paths.

## Goals

1. Every CR and bug gets a zero-padded progressive number unique within its project (e.g. `001`, `042`).
2. Every CR and bug gets a slug derived from the title at creation time that never changes afterwards.
3. All API responses (web and CLI) expose both fields.
4. The combination `<progressive>-<slug>` is ready to be used by the SDD CLI as a canonical file name.

## Proposed Solution

### Data model

Add two fields to both `ChangeRequest` and `Bug`:

| Field | Type | Description |
|-------|------|-------------|
| `number` | integer | Monotonically increasing, scoped to `(project_id)`. Zero-padded to 3 digits when rendered (e.g. `001`). |
| `slug` | string | URL-friendly identifier derived from the title at creation. Immutable after first write. |

Unique constraints:
- `(project_id, number)` on both tables.
- `(project_id, slug)` on both tables.

### Number generation

The server resolves `number` according to the following priority order:

1. **Restore from CLI path** — if the push request includes a `path` whose filename starts with a numeric prefix (e.g. `change-requests/001-fix-auth.md` or `bugs/042-login-crash.md`), extract that integer and use it as `number`. This preserves the progressive that the CLI already assigned locally.
2. **Auto-increment** — otherwise, compute `MAX(number) + 1` within the same `project_id` (default `1` if none exists).

In both cases, use a `SELECT FOR UPDATE` lock (or equivalent) to prevent races. If the restored number from the path is already taken by a different entity in the same project, fall back to auto-increment and log a warning.

The number is never reassigned, even after deletion.

### Slug generation

- Derived from the title at creation: lowercase, strip non-alphanumeric characters, replace spaces/punctuation with `-`, collapse consecutive `-`, trim leading/trailing `-`.
- Example: `"Fix CLI push-docs 500 error"` → `fix-cli-push-docs-500-error`.
- If the derived slug already exists within the project, append `-2`, `-3`, … until unique.
- The slug field is immutable: `PATCH` and `PUT` requests must ignore any `slug` value sent by the client. The slug can only be set at creation.

### Formatted progressive

The `number` is stored as an integer. A `formatted_number` derived field (e.g. `"019"`) is returned in responses, zero-padded to at least 3 digits.

### API changes

All response shapes that return a CR or bug must include `number`, `formatted_number`, and `slug`.

#### Web API — CRs

- `POST .../crs` response: add `number`, `formatted_number`, `slug`
- `GET .../crs` items: add `number`, `formatted_number`, `slug`
- `GET .../crs/:cr_id` response: add `number`, `formatted_number`, `slug`
- `PATCH .../crs/:cr_id` response: add `number`, `formatted_number`, `slug` (slug is ignored in request body)

#### Web API — Bugs

- `POST .../bugs` response: add `number`, `formatted_number`, `slug`
- `GET .../bugs` items: add `number`, `formatted_number`, `slug`
- `GET .../bugs/:bug_id` response: add `number`, `formatted_number`, `slug`
- `PATCH .../bugs/:bug_id` response: add `number`, `formatted_number`, `slug` (slug is ignored in request body)

#### CLI API

- `GET /cli/pending-crs` items: add `number`, `formatted_number`, `slug`
- `GET /cli/open-bugs` items: add `number`, `formatted_number`, `slug`
- `POST /cli/crs/:cr_id/applied` response: add `number`, `formatted_number`, `slug`
- `POST /cli/bugs/:bug_id/resolved` response: add `number`, `formatted_number`, `slug`
- `POST /cli/push-crs` response items: add `number`, `formatted_number`, `slug`
- `POST /cli/push-bugs` response items: add `number`, `formatted_number`, `slug`
- `POST /cli/crs/:cr_id/enriched` response: add `number`, `formatted_number`, `slug`
- `POST /cli/bugs/:bug_id/enriched` response: add `number`, `formatted_number`, `slug`

### CLI push-crs / push-bugs — number and slug handling

**New entity (no `id` in the push payload):**

1. If `path` has a numeric prefix (e.g. `001-fix-auth.md`), extract and restore that number (see *Number generation* above).
2. Derive `slug` from the part of the filename after the numeric prefix and dash, stripped of the `.md` extension — so `001-fix-auth.md` → slug `fix-auth`. This ensures the server slug matches exactly what the CLI already has on disk.
3. If `path` has no numeric prefix, generate both `number` (auto-increment) and `slug` (from title).

**Existing entity (push includes `id`):**

- The server ignores any `slug` in the request body and preserves the stored immutable slug.
- The `number` is also immutable and is never updated from the push payload.

## Required Changes

### Documentation

1. `system/entities.md`
   - Add `number` (integer) and `slug` (string, immutable) fields to `ChangeRequest` table.
   - Add `number` (integer) and `slug` (string, immutable) fields to `Bug` table.
   - Add unique constraints `(project_id, number)` and `(project_id, slug)` for both entities.
   - Document that `slug` is derived from title at creation and cannot be changed afterwards.

2. `system/interfaces.md`
   - Add `number`, `formatted_number`, `slug` to all CR and Bug response shapes (web API and CLI API sections).
   - Note in `PATCH .../crs/:cr_id` and `PATCH .../bugs/:bug_id` that `slug` is not accepted as an update field.
   - Note in `POST /cli/push-crs` and `POST /cli/push-bugs` that `slug` is server-generated.

3. `product/features/change-requests.md`
   - Document the progressive number and slug as part of the CR identity.
   - Note that the slug is immutable after creation.

4. `product/features/bugs.md`
   - Document the progressive number and slug as part of the Bug identity.
   - Note that the slug is immutable after creation.

### Backend code

1. `code/backend/app/models/` — add `number` and `slug` columns to `ChangeRequest` and `Bug` models.
2. `code/backend/alembic/versions/` — migration: add `number` and `slug` columns with unique constraints.
3. `code/backend/app/services/` — slug generation utility (slugify + dedup within project).
4. `code/backend/app/api/crs.py` — assign `number` and `slug` on create; exclude `slug` from update logic; include fields in all response serializers.
5. `code/backend/app/api/bugs.py` — same as above for bugs.
6. `code/backend/app/api/cli.py` — include `number`, `formatted_number`, `slug` in all CLI response payloads.

### Frontend code

1. Update TypeScript types for `ChangeRequest` and `Bug` to include `number: number`, `formatted_number: string`, `slug: string`.
2. Display `formatted_number` in CR and Bug list rows and detail views (e.g. `#001`).
3. Do not render a slug edit field anywhere in the UI.

## Acceptance Criteria

1. Creating a CR via UI or CLI assigns a project-scoped sequential number (starting at 1) and a slug derived from the title.
2. The slug is not modifiable: `PATCH` requests silently ignore a `slug` field; no edit field exists in the UI.
3. Two CRs or bugs in the same project cannot share the same number or the same slug. Duplicate slugs are disambiguated with a numeric suffix at creation time.
4. All web API and CLI API responses include `number`, `formatted_number`, and `slug`.
5. `formatted_number` is always at least 3 digits, zero-padded (e.g. `"001"`, `"042"`, `"100"`).
6. Existing CRs and bugs created before this migration have their `number` and `slug` back-filled (in creation order within each project).

## Risks and Mitigations

1. **Race condition on number generation** — Mitigated by using a `SELECT FOR UPDATE` or a database sequence scoped to the project.
2. **Restored number already taken** — If two CLI files happen to carry the same numeric prefix within the same project (e.g. two separate repos pointing to the same project), the second push falls back to auto-increment and logs a warning. The CLI path remains unchanged; only the server-side `number` diverges.
3. **Slug derived from path vs. from title mismatch** — When a path with a numeric prefix is present, the slug is derived from the path remainder, not the title. This guarantees CLI/server consistency. The title may differ from the slug (e.g. after a rename), which is expected and acceptable.
4. **Slug collision on back-fill migration** — Mitigated by processing rows in `created_at` order and appending numeric suffix on collision.
5. **CLI compatibility** — New fields in responses (`number`, `formatted_number`, `slug`) are additive and non-breaking for existing CLI versions that ignore unknown fields.
