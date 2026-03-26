---
title: "Remote Workers"
status: synced
author: ""
last-modified: "2026-03-26T12:00:00.000Z"
version: "1.2"
---

# Remote Workers

## Overview

Remote Workers allow machines running the SDD CLI to register with SDD Flow and receive jobs dispatched from the web UI. Three job types are supported:

- **Enrich** — for draft entities (CR, Bug, or Document): the agent enriches the specification. On success the entity transitions `draft → pending` (CR), `draft → open` (Bug), or `draft → new` (Document).
- **Apply** — for approved CRs or open/in-progress Bugs: the agent implements the change or fixes the bug. On success the entity transitions to `applied` (CR) or `resolved` (Bug).
- **Sync** — project-level operation: the agent runs `sdd pull` → `sdd sync` → implements all pending items → `sdd push`. No specific entity required.

Output streams in real-time to the web UI and users can answer agent questions interactively from the browser.

## Features

### Branch

The worker uses whatever git branch is active when `sdd remote worker` is started — no checkout is performed. The current branch is sent to the server at registration and shown in the web UI (worker cards and job list) as informational context.

SDD commands work on any branch; there is no branch restriction.

### Worker Registration

- A machine registers as a worker by running `sdd remote worker`
- Registration is automatic on first run — no separate setup step
- Each worker has a name (defaults to hostname), unique within a project
- Workers reconnect automatically if restarted (upsert by project + name)
- Options: `--name <name>`, `--agent <agent>`, `--timeout <seconds>`
- The configured working branch is sent to the server at registration and shown in the UI

### Worker Health & Lifecycle

- Workers send a heartbeat every 15 seconds
- A worker is considered **online** if its last heartbeat is within 60 seconds
- Workers marked **offline** automatically after 60 seconds without heartbeat
- Running jobs on a worker that has been offline for more than 5 minutes are marked **failed**
- The web UI shows worker status: online (green), offline (gray), busy (amber)

### Job Options Dialog

Before dispatching any job, a **Job Options Dialog** opens (max-width 3xl):

- **Worker** dropdown — lists online workers with name, agent, and branch; auto-selects if only one is online
- **Agent** dropdown — the agent adapter to use (claude, codex, opencode)
- **Model** dropdown — available models for the selected agent (e.g. Claude Opus 4, Claude Sonnet 4, Claude Haiku 4)
- **Prompt** — read-only preview of the server-generated prompt; an "Edit" toggle allows free-form editing before dispatch
- Confirm dispatches the job; Cancel closes without dispatching

### Job Dispatch

Job dispatch buttons appear on entity pages when at least one worker is online:

| Button | Job Type | Entity | Required Status |
|--------|----------|--------|-----------------|
| **Enrich on Worker** (amber) | `enrich` | CR | `draft` |
| **Enrich on Worker** (amber) | `enrich` | Bug | `draft` |
| **Enrich on Worker** (amber) | `enrich` | Document | `draft` |
| **Apply on Worker** (indigo) | `apply` | CR | `approved` |
| **Apply on Worker** (indigo) | `apply` | Bug | `open` or `in_progress` |
| **Sync on Worker** (purple) | `sync` | Project | any |

"Sync on Worker" appears on the Workers list page and on the project Dashboard.

- Jobs enter a queue with status `queued`
- Workers pick up jobs via long polling — first available worker wins (atomic assignment)
- One worker handles one job at a time

### Job Execution

- The worker receives the job with a server-generated prompt appropriate to the job type
- The prompt includes entity content, comments (if any), and project documentation
- Agent output streams to the server in batches (every ~2 seconds)
- The server relays output to the frontend via Server-Sent Events (SSE)
- On failure (non-zero exit), the job is marked `failed` with no status transition
- When SSE completes (`done` event), the frontend automatically refreshes the job status badge

**Enrich job prompt** (CR/Bug) follows the `sdd-remote` skill workflow:
1. Pull the latest remote state (`sdd pull --crs-only` or `--bugs-only`)
3. Run `sdd drafts` to list pending drafts
4. Enrich the draft with technical details, acceptance criteria, edge cases, plus any comments from the web UI
5. Run `sdd mark-drafts-enriched` → transitions `draft → pending` (CR) / `draft → open` (Bug)
6. Run `sdd push` to publish the enriched content

**Enrich job prompt** (Document):
1. Pull the latest remote state (`sdd pull`)
3. Update the local document file with enriched content
4. Run `sdd push` to publish

**Apply job prompt** instructs the agent to implement the CR or fix the bug:
1. Implement the change described in the specification (using all project documentation and comments as context)
3. Commit the changes
4. Run `sdd push`

**Sync job prompt** (project-level):
1. Run `sdd pull` to fetch latest specs
3. Run `sdd sync` to see what is pending
4. Implement all pending change requests and bug fixes
5. Run `sdd mark-synced` to mark implemented items
6. Commit changes
7. Run `sdd push`

**Auto-transitions on exit code 0:**

| Job Type | Entity | From → To |
|----------|--------|-----------|
| `enrich` | CR | `draft → pending` |
| `enrich` | Bug | `draft → open` |
| `enrich` | Document | `draft → new` |
| `apply` | CR | `approved → applied` |
| `apply` | Bug | `open`/`in_progress → resolved` |
| `sync` | — | (transitions happen via CLI commands) |

### Comments in Prompt

For enrich and apply jobs on CRs and Bugs, the server-generated prompt includes all comments posted on the entity, each with the author's display name and timestamp. This ensures the agent has full context about any discussions or clarifications.

### Notifications

Workers trigger in-app notifications:

| Event | `event_type` | Recipient |
|-------|-------------|-----------|
| Agent asks a question | `worker_question` | Job creator |
| Job completed successfully | `worker_job_completed` | Job creator |
| Job failed | `worker_job_failed` | Job creator |

Notifications appear in the NotificationBell. Clicking a notification navigates to the job detail page.

### Interactive Q&A

- When the agent asks a question, the worker detects it and posts it to the server, triggering a `worker_question` notification
- The question appears in the web UI terminal with a text input for the user to respond
- The user's answer is sent to the server, the worker polls for it and writes it to the agent's stdin
- Multiple Q&A exchanges are supported within a single job

### Job Terminal View

- A dedicated page shows job details: status, worker name, entity link, timestamps, agent, model
- A terminal-style component displays the full output stream with color-coded messages:
  - White: agent output
  - Amber/yellow: agent questions
  - Green: user answers
- Auto-scrolls during live streaming; static transcript when job is complete
- When the SSE stream ends, the job status badge updates automatically without a page refresh
- Users can cancel running or queued jobs

### Worker Jobs List

- Project-level page listing all worker jobs with status filters
- Shows worker status cards: name, status badge, agent, branch
- A "Sync on Worker" button dispatches a project-level sync job
- Each job row shows entity type/title (or "Project Sync" for sync jobs), worker name, status badge, and timestamp

### Dashboard Integration

- Project dashboard shows a "Workers Online" stats card (online / total count)
- A "Recent Worker Jobs" section shows the 5 most recent jobs with status badges
- A "Sync on Worker" button in the Recent Jobs section dispatches a sync job

## Agent Notes

- The agent adapter is configurable per worker (`--agent` flag or project config)
- Default agent is `claude` (Claude Code with `--dangerously-skip-permissions`)
- Models are configurable per job via the Job Options Dialog; the `--model` flag is passed to the agent CLI
- The prompt is generated server-side and includes: branch instruction, entity body, comments, and all project documentation
- Agent detection of questions uses pattern matching on stdout (lines ending with `?` or `[Y/n]`-style prompts)
- Job timeout is configurable (default 30 minutes); worker kills the agent and reports exit code 124 on timeout
