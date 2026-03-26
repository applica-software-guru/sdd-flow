---
title: "Remote Worker — dispatch AI agent jobs from web UI to registered CLI workers"
status: applied
author: ""
created-at: "2026-03-26T00:00:00.000Z"
---

# CR-020: Remote Worker

## Summary

Add the ability for machines running the SDD CLI to register as Remote Workers with SDD Flow and receive AI agent jobs dispatched from the web UI. Workers execute agents (Claude Code, Codex, OpenCode) locally, streaming output in real-time to the browser with interactive Q&A support.

## Problem

Currently, applying a Change Request or resolving a Bug requires a developer to manually run the SDD CLI on their local machine (`sdd pull`, run agent, `sdd push`). There is no way to trigger agent execution from the web UI, and no visibility into agent progress for team members who don't have CLI access.

## Goals

1. Workers register automatically via `sdd remote worker` — no separate setup step.
2. Users dispatch jobs from the CR/Bug detail page with a single click.
3. Agent output streams in real-time to a terminal view in the browser.
4. Users can answer agent questions interactively from the web UI.
5. Successful jobs auto-transition CRs to `applied` and Bugs to `resolved`.
6. The agent adapter is abstracted — supports Claude Code, Codex, OpenCode, and custom agents.

## Proposed Solution

### Communication Protocol

- **Worker → Server**: Long polling (30s hold) for job pickup + POST for output/heartbeat. NAT-friendly — no persistent connection required.
- **Server → Frontend**: SSE (Server-Sent Events) for real-time output streaming.
- **Q&A relay**: Worker posts question → SSE delivers to frontend → User answers → Worker polls for answer → Writes to agent stdin.

### Data Model

Three new entities: `Worker`, `WorkerJob`, `WorkerJobMessage` (see `system/entities.md`).

### Backend

- **CLI routes** (`workers_cli.py`): 8 endpoints for worker registration, heartbeat, long-poll job assignment, output/question/answer relay, and job completion.
- **Web routes** (`workers.py`): 7 endpoints for listing workers, creating/listing/viewing jobs, SSE streaming, answering questions, and cancelling jobs.
- **Prompt service** (`worker_prompt.py`): Generates structured prompts from CR/Bug body + all project documentation.
- **Atomic assignment**: `SELECT ... FOR UPDATE SKIP LOCKED` prevents race conditions.
- **Health monitoring**: Piggybacks on heartbeat/poll — no separate scheduler. Workers offline after 60s, jobs failed after 5min.
- **Auto-transition**: Exit code 0 → CR `applied` / Bug `resolved`.

### CLI

- **Worker client** (`worker-client.ts`): API functions for all worker endpoints.
- **Agent runner extension** (`agent-runner.ts`): New `startAgent()` function returning `AgentRunnerHandle` with `writeStdin`, `kill`, `exitPromise` for interactive mode.
- **Worker daemon** (`worker-daemon.ts`): Registration, concurrent heartbeat + poll loops, job execution with output batching and Q&A relay.
- **CLI command**: `sdd remote worker [--name <name>] [--agent <agent>] [--timeout <seconds>]`.

### Frontend

- **New pages**: Worker Jobs list (`worker-jobs/ListPage.tsx`) and detail (`worker-jobs/DetailPage.tsx`) with terminal view and Q&A panel.
- **New components**: `WorkerTerminal`, `WorkerQAPanel`, `WorkerStatusBadge`, `JobStatusBadge`.
- **Modified pages**: CR detail (Apply on Worker button), Bug detail (Apply on Worker button), Project dashboard (Workers stats card + Recent Jobs section).
- **SSE hook** (`useWorkerJobStream`): EventSource-based hook that accumulates messages in state.

## Required Changes

### Documentation

1. `product/features/remote-worker.md` — New feature spec
2. `product/vision.md` — Update non-goals (SDD Flow now orchestrates remote agent execution), add goal #7
3. `system/entities.md` — Add Worker, WorkerJob, WorkerJobMessage entities
4. `system/interfaces.md` — Add 15 new endpoints (7 web + 8 CLI)
5. `system/architecture.md` — Add Remote Worker Architecture section

### Backend code

1. `app/models/worker.py`, `worker_job.py`, `worker_job_message.py` — New SQLAlchemy models
2. `alembic/versions/` — Migration for 3 tables with enums, FKs, indexes
3. `app/schemas/workers.py` — Pydantic request/response schemas
4. `app/services/worker_prompt.py` — Prompt generation service
5. `app/api/workers_cli.py` — 8 CLI endpoints (API key auth)
6. `app/api/workers.py` — 7 web endpoints (JWT auth)
7. `app/main.py` — Register new routers

### CLI code (TypeScript)

1. `packages/core/src/remote/worker-types.ts` — TypeScript interfaces
2. `packages/core/src/remote/worker-client.ts` — API client functions
3. `packages/core/src/agent/agent-runner.ts` — Add `startAgent()` with interactive stdio
4. `packages/core/src/agent/worker-daemon.ts` — Worker daemon logic
5. `packages/cli/src/commands/remote.ts` — `sdd remote worker` command
6. `packages/core/src/index.ts` — New exports

### Frontend code

1. `src/types/index.ts` — Worker, WorkerJob, WorkerJobMessage types
2. `src/hooks/useWorkers.ts` — React Query hooks + SSE hook
3. `src/components/` — WorkerTerminal, WorkerQAPanel, WorkerStatusBadge, JobStatusBadge
4. `src/pages/worker-jobs/` — ListPage, DetailPage
5. `src/pages/change-requests/DetailPage.tsx` — Apply on Worker button
6. `src/pages/bugs/DetailPage.tsx` — Apply on Worker button
7. `src/pages/project/DashboardPage.tsx` — Workers card + Recent Jobs
8. `src/App.tsx` — New routes
9. `src/components/Layout.tsx` — Workers nav link

## Acceptance Criteria

1. Running `sdd remote worker` registers the machine and shows "Worker online, waiting for jobs..."
2. The worker appears as "online" in the project dashboard within 15 seconds.
3. Clicking "Apply on Worker" on an approved CR creates a queued job and navigates to the job detail page.
4. The terminal view shows agent output streaming in real-time.
5. If the agent asks a question, the Q&A panel appears and the user can type an answer that reaches the agent.
6. On successful completion (exit 0), the CR transitions to `applied` automatically.
7. If the worker disconnects mid-job, the job is marked `failed` within 5 minutes.
8. Multiple workers on the same project can run jobs in parallel (one job per worker).
9. Cancelling a job from the web UI stops the agent process on the worker.

## Risks and Mitigations

1. **Race condition on job assignment** — Mitigated by `SELECT FOR UPDATE SKIP LOCKED` in the poll endpoint.
2. **Worker behind NAT** — Long polling works through NAT/firewalls without configuration; no inbound connections needed.
3. **Agent hangs** — Configurable timeout (default 30min); worker kills agent and reports exit code 124.
4. **SSE reconnection** — Browser `EventSource` reconnects automatically; server resumes from `sequence > last_seen`.
5. **Stale workers** — Heartbeat-based health check with piggyback cleanup; no separate scheduler needed.
