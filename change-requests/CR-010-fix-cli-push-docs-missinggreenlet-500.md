---
title: "Fix CLI push-docs 500 caused by ORM serialization MissingGreenlet"
status: draft
author: "roberto"
created-at: "2026-03-18T00:00:00.000Z"
---

# CR-010: Fix CLI push-docs MissingGreenlet 500

## Summary

Fix backend serialization in `POST /api/v1/cli/push-docs` to prevent intermittent HTTP 500 during `sdd push --all`.

## Problem

Cloud Run logs show `POST /api/v1/cli/push-docs` failing with HTTP 500 due to:

- `pydantic_core.ValidationError` on `DocResponse`
- `Error extracting attribute: MissingGreenlet`
- failing attribute: `updated_at`

The failure occurs while serializing ORM `DocumentFile` objects into response models after flush.

## Root cause

In `code/backend/app/api/cli.py`, `push_docs` currently does:

1. create/update multiple `DocumentFile` rows
2. `await db.flush()`
3. immediate `DocResponse.model_validate(d)` for each ORM object

For some objects, DB-managed fields (such as `updated_at`) are not fully loaded at serialization time, triggering lazy attribute fetch and raising `MissingGreenlet` in async context.

## Proposed solution

Make `push_docs` follow the same safe serialization pattern used by `push_crs` and `push_bugs`:

1. Keep `await db.flush()`
2. Refresh each `DocumentFile` instance in `docs` before validation
3. Build response from fully materialized ORM objects

Optional hardening:

- Wrap response model conversion in explicit error handling and log a structured error with endpoint, project_id, and document count.
- Consider using explicit `RETURNING`/selected columns mapping to avoid model-level lazy reads in response construction.

## Changes Required

### Backend

#### `code/backend/app/api/cli.py`

- In `push_docs`, add `await db.refresh(doc)` loop for all docs before `DocResponse.model_validate`.
- Ensure no ORM attribute access in response serialization can trigger lazy IO.

### Tests

#### `code/backend/tests/test_docs.py` (or CLI test file)

- Add regression test for `POST /api/v1/cli/push-docs` with multiple documents.
- Assert response is 200 and each returned document has non-null `created_at` and `updated_at`.

#### `code/backend/tests/test_cli.py` (if present)

- Add targeted test for push-docs serialization stability in async context.

### Documentation

#### `product/features/sdd-docs.md`

- Add note that CLI push operations are robust for batch synchronization and return deterministic metadata.

## Implementation Plan

1. Reproduce locally by posting bulk docs to `/api/v1/cli/push-docs` in async tests.
2. Update `push_docs` to refresh all ORM instances before schema validation.
3. Add regression tests for bulk push success and response timestamps.
4. Verify no performance regression with typical batch sizes.
5. Deploy and validate via Cloud Run logs that 500 on push-docs no longer appears.

## Acceptance Criteria

1. `sdd push --all` no longer fails with 500 on `/api/v1/cli/push-docs` for valid payloads.
2. `POST /api/v1/cli/push-docs` returns 200 consistently with populated `created_at` and `updated_at`.
3. Regression tests cover the serialization path that previously triggered `MissingGreenlet`.
4. Cloud Run logs show no new serialization exceptions in this endpoint after deployment.

## Risks and Mitigations

- Risk: refreshing each row adds overhead for large batches.
  - Mitigation: validate performance with realistic payload sizes and optimize only if needed.
- Risk: fix masks another underlying ORM/session lifecycle issue.
  - Mitigation: keep logs structured and add a dedicated integration test for the endpoint.
