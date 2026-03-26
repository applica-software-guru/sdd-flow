---
title: "CR-022 Remote Worker UX Improvements"
status: applied
author: ""
created-at: "2026-03-26T12:00:00.000Z"
---

# CR-022 — Remote Worker UX Improvements

## Summary

A comprehensive set of improvements to the Remote Worker feature covering job dispatch UX, new job types, branch management, real-time updates, notifications, and document enrichment.

## Changes

### 1. Job Options Dialog

Before dispatching any worker job, a modal dialog now opens allowing the user to configure:

- **Worker** — dropdown of online workers; auto-selects if only one is available; shows branch
- **Agent** — the agent adapter (claude, codex, opencode)
- **Model** — available models for the selected agent (e.g. Claude Opus 4, Claude Sonnet 4, Claude Haiku 4; GPT 5.4, GPT 5.4 Mini, GPT 5.3 Codex)
- **Prompt** — read-only preview of the server-generated prompt, with an optional "Edit" toggle

Backend: new `GET .../worker-jobs/agent-models` endpoint and `POST .../worker-jobs/preview` endpoint. Jobs now accept `model`, `prompt` (override), and `worker_id` fields.

### 2. Job Type `sync` (Project-level)

A new `sync` job type dispatches a full project synchronisation:
1. `sdd pull`
2. `sdd sync` (view all pending items)
3. Implement all pending CRs and bugs
4. `sdd mark-synced`
5. Commit
6. `sdd push`

`sync` jobs have no entity (`entity_type`/`entity_id` are null). A "Sync on Worker" button (purple) appears on the Workers list page and the project Dashboard.

### 3. Document Enrich

The "Enrich on Worker" button now appears on Document detail pages when the document is in `draft` status. On success, the document transitions `draft → new`. The prompt instructs the agent to enrich the document content and push the result.

### 4. Working Branch

Each SDD project has a single **working branch** (default: `sdd`), configured in `.sdd/config.yaml` at `sdd init` time.

- All SDD write commands enforce branch check; wrong branch = error with instructions
- `sdd status` shows a warning only (read-only command)
- Workers checkout the configured branch at startup and before each job
- The branch is sent to the server at registration and visible in the web UI (worker cards, job list)
- Prompts include a branch instruction ("Make sure you are on branch `sdd`...")

### 5. Fix Real-time Status Update

When the SSE stream sends a `done` event (job reached terminal status), the frontend now invalidates the React Query cache for the job detail, causing the status badge to update automatically without a page refresh.

### 6. Fix Pending CR Transitions

CR in `pending` status now supports transitions: `approved`, `rejected`, `draft`. Previously no transitions were available from `pending`.

### 7. Comments in Prompt

For enrich and apply jobs on CRs and Bugs, the server-generated prompt includes all comments with author display name and timestamp, giving the agent full context about discussions on the entity.

### 8. Worker Notifications

Workers now trigger in-app notifications:

| Event | `event_type` | Recipient |
|-------|-------------|-----------|
| Agent asks a question | `worker_question` | Job creator |
| Job completed | `worker_job_completed` | Job creator |
| Job failed | `worker_job_failed` | Job creator |

### 9. Bug Draft Status

Bugs now support a `draft` status (consistent with CRs and Documents), enabling the Enrich workflow. The TRANSITIONS map in the Bug detail page is updated accordingly.

## Files Changed

### Backend
- `app/services/agent_models.py` — new; static model config per agent
- `app/services/worker_prompt.py` — rewritten; sync prompt, document prompt, comments, branch note
- `app/api/workers.py` — new agent-models + preview endpoints; sync/document support; branch in worker response; model in job response
- `app/api/workers_cli.py` — branch in registration; model+branch in poll; notifications; document auto-transition
- `app/models/worker.py` — + `branch`
- `app/models/worker_job.py` — + `model`, `sync` job type, nullable entity fields
- `app/schemas/workers.py` — updated all schemas
- `alembic/versions/h8c9d0e1f2a3_*` — migration

### Frontend
- `src/types/index.ts` — Worker branch, WorkerJob model/entity changes, AgentModel type, CRStatus pending, BugStatus draft, JobType sync
- `src/hooks/useWorkers.ts` — useAgentModels, usePreviewJobPrompt, updated createJob payload, onDone callback
- `src/components/JobOptionsDialog.tsx` — new
- `src/pages/change-requests/DetailPage.tsx` — dialog, pending transitions
- `src/pages/bugs/DetailPage.tsx` — dialog, draft transitions
- `src/pages/docs/ViewPage.tsx` — Enrich on Worker for drafts
- `src/pages/worker-jobs/DetailPage.tsx` — SSE onDone cache invalidation
- `src/pages/worker-jobs/ListPage.tsx` — branch in cards, Sync on Worker button
- `src/pages/project/DashboardPage.tsx` — Sync on Worker button, entity type display fix

### CLI
- `packages/core/src/types.ts` — SDDConfig.branch
- `packages/core/src/sdd.ts` — ensureBranch()
- `packages/core/src/git/git.ts` — getCurrentBranch, checkoutBranch
- `packages/core/src/scaffold/init.ts` — branch in config + checkout
- `packages/core/src/scaffold/templates.ts` — ProjectInfo.branch
- `packages/core/src/remote/worker-types.ts` — model, branch in WorkerJobAssignment
- `packages/core/src/remote/worker-client.ts` — branch in registerWorker
- `packages/core/src/agent/agent-defaults.ts` — $MODEL in command templates
- `packages/core/src/agent/agent-runner.ts` — model option, $MODEL substitution
- `packages/core/src/agent/worker-daemon.ts` — branch checkout, model pass-through
- `packages/cli/src/ui/branch-guard.ts` — new; requireCorrectBranch()
- `packages/cli/src/commands/init.ts` — branch prompt
- `packages/cli/src/commands/remote.ts` — branch passed to daemon
- All write commands — requireCorrectBranch() at start

### Documentation
- `sdd-flow/product/features/remote-worker.md` — v1.2; all new features
- `sdd-flow/system/entities.md` — v1.5; Worker.branch, WorkerJob.model/sync
- `sdd-flow/system/interfaces.md` — v1.9; new endpoints, updated schemas
- `sdd/packages/skill/sdd/SKILL.md` — working branch section + rule
- `sdd/packages/skill/sdd-remote/SKILL.md` — v1.1; all three workflows documented
