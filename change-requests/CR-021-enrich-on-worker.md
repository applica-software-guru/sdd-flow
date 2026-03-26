---
title: "Enrich on Worker — dispatch enrichment jobs for draft CRs and Bugs"
status: applied
author: ""
created-at: "2026-03-26T12:00:00.000Z"
---

# CR-021: Enrich on Worker

## Summary

Extend the Remote Worker feature with a second job type: `enrich`. When a CR or Bug is in `draft` status, a user can dispatch it to an online worker for enrichment. The worker runs the `sdd-remote` skill workflow (pull → enrich → `sdd mark-drafts-enriched` → push), and on success the entity auto-transitions from `draft` to `pending` (CR) or `open` (Bug).

## Problem

CR-020 introduced the Remote Worker feature with a single `apply` job type (for approved CRs / open bugs). But the SDD workflow begins earlier: draft CRs and Bugs need to be enriched before they can be approved. The enrichment step — expanding a rough draft into a detailed, actionable spec — was missing from the remote worker flow and had to be done manually with the CLI.

## Goals

1. Users can dispatch a draft CR/Bug to an online worker with one click ("Enrich on Worker").
2. The worker follows the `sdd-remote` skill: pull → enrich → mark-enriched → push.
3. On success (exit 0), the entity auto-transitions: CR `draft → pending`, Bug `draft → open`.
4. The enrichment prompt is generated server-side and includes the full CR/Bug body plus project documentation.
5. The existing Apply on Worker flow is unchanged.

## Proposed Solution

### New `job_type` field

Add `job_type: enrich | apply` (default `apply`) to `WorkerJob`.

### Validation

| job_type | entity | Required status |
|----------|--------|-----------------|
| `enrich` | CR | `draft` |
| `enrich` | Bug | `draft` |
| `apply` | CR | `approved` |
| `apply` | Bug | `open` or `in_progress` |

### Prompt (enrich)

The enrichment prompt instructs the agent to follow the `sdd-remote` skill workflow:
1. `sdd pull --crs-only` (or `--bugs-only`)
2. `sdd drafts`
3. Enrich the draft with technical details, acceptance criteria, edge cases
4. `sdd mark-drafts-enriched`
5. `sdd push`

### Auto-transition on completion

| job_type | entity | exit 0 transition |
|----------|--------|-------------------|
| `enrich` | CR | `draft → pending` |
| `enrich` | Bug | `draft → open` |
| `apply` | CR | `approved → applied` |
| `apply` | Bug | `open`/`in_progress → resolved` |

## Required Changes

### Documentation

1. `product/features/remote-worker.md` — Add enrich job type, updated job dispatch table, prompt description, auto-transition table
2. `system/entities.md` — Add `job_type` field to WorkerJob
3. `system/interfaces.md` — Update `POST .../worker-jobs` body and poll response to include `job_type`

### Backend

1. `alembic/versions/g7b8c9d0e1f2_add_job_type_to_worker_jobs.py` — Migration: add `job_type_enum` + column
2. `app/models/worker_job.py` — Add `JobType` enum and `job_type` mapped column
3. `app/schemas/workers.py` — Add `job_type` to `WorkerJobCreate`, `WorkerJobResponse`, `WorkerJobAssignment`
4. `app/services/worker_prompt.py` — Add enrichment prompt branch in `generate_worker_prompt()`
5. `app/api/workers.py` — Validate entity status per job_type; pass job_type to prompt; include in response
6. `app/api/workers_cli.py` — Include `job_type` in poll assignment; handle enrich auto-transition in `job_completed`

### Frontend

1. `src/types/index.ts` — Add `JobType` type; add `job_type` to `WorkerJob`
2. `src/hooks/useWorkers.ts` — Add `job_type` to `useCreateWorkerJob` payload
3. `src/pages/change-requests/DetailPage.tsx` — Add "Enrich on Worker" button (amber) for `draft` CRs
4. `src/pages/bugs/DetailPage.tsx` — Add "Enrich on Worker" button (amber) for `draft` Bugs

## Acceptance Criteria

1. A draft CR with an online worker shows "Enrich on Worker" button; an approved CR shows "Apply on Worker".
2. Clicking "Enrich on Worker" creates a job with `job_type: enrich` and navigates to the job detail page.
3. The worker receives the job with an enrichment prompt referencing the `sdd-remote` skill steps.
4. On successful completion (exit 0), a draft CR transitions to `pending`; a draft Bug transitions to `open`.
5. On failure, no status transition occurs.
6. The existing Apply on Worker flow is unaffected.
