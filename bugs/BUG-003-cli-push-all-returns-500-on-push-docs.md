---
title: "CLI push --all fails with 500 on /api/v1/cli/push-docs"
status: resolved
author: "roberto"
created-at: "2026-03-18T00:00:00.000Z"
---

## Description

Running `sdd push --all` intermittently fails with HTTP 500 from the remote backend. The failing API call is `POST /api/v1/cli/push-docs`.

## Evidence from Cloud Run logs

Project: `s-dd-490608`
Service: `sdd-flow-backend`
Region: `europe-west1`

Observed failing request:

- Timestamp: `2026-03-18T19:10:55.707320Z`
- Endpoint: `POST /api/v1/cli/push-docs`
- Status: `500`
- User-Agent: `node`
- Trace: `projects/s-dd-490608/traces/82d5cd38196574ec91d8cdcf7baed4ec`

Related stack trace (stderr) shows:

- `pydantic_core.ValidationError: 1 validation error for DocResponse`
- `Error extracting attribute: MissingGreenlet`
- `updated_at`
- Source frame: `app/api/cli.py`, function `push_docs`, line building `DocResponse.model_validate(d)`

## Impact

- `sdd push --all` can fail even when payload is valid.
- Documentation synchronization from CLI to remote becomes unreliable.
- Users receive generic server errors and must retry manually.

## Suspected root cause

In `code/backend/app/api/cli.py`, endpoint `push_docs` returns:

- `documents=[DocResponse.model_validate(d) for d in docs]`

After `await db.flush()`, some ORM fields with DB-managed values (notably `updated_at`) are not fully materialized for all `DocumentFile` instances. While Pydantic reads attributes from ORM (`from_attributes=True`), SQLAlchemy attempts lazy IO in a context where `MissingGreenlet` is raised.

Unlike `push_crs` and `push_bugs`, `push_docs` does not refresh each ORM instance before validation.

## Suggested fix

1. In `push_docs`, refresh each document before serialization:
   - `await db.refresh(doc)` for every item in `docs` after flush
2. Optionally commit before response serialization if required by timestamp/onupdate semantics.
3. Add a regression test for `POST /api/v1/cli/push-docs` that verifies a 200 response and valid `updated_at`/`created_at` in response items.
4. Improve error handling/logging in CLI endpoints to return a clearer message when response serialization fails.

## Notes

There is also a separate 500 observed on notifications endpoint (`GET /api/v1/notifications?page_size=10`) in the same day; this appears unrelated and should be tracked separately.
