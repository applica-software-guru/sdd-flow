---
title: "Remote Workers"
status: synced
author: ""
last-modified: "2026-03-26T12:00:00.000Z"
version: "1.1"
---

# Remote Workers

## Overview

Remote Workers allow machines running the SDD CLI to register with SDD Flow and receive jobs dispatched from the web UI. Two job types are supported:

- **Enrich** — for draft CRs/Bugs: the agent enriches the specification following the `sdd-remote` skill workflow (pull → enrich → `sdd mark-drafts-enriched` → push). On success the entity transitions `draft → pending` (CR) or `draft → open` (Bug).
- **Apply** — for approved CRs or open/in-progress Bugs: the agent implements the change or fixes the bug. On success the entity transitions to `applied` (CR) or `resolved` (Bug).

Output streams in real-time to the web UI and users can answer agent questions interactively from the browser.

## Features

### Worker Registration

- A machine registers as a worker by running `sdd remote worker`
- Registration is automatic on first run — no separate setup step
- Each worker has a name (defaults to hostname), unique within a project
- Workers reconnect automatically if restarted (upsert by project + name)
- Options: `--name <name>`, `--agent <agent>`, `--timeout <seconds>`

### Worker Health & Lifecycle

- Workers send a heartbeat every 15 seconds
- A worker is considered **online** if its last heartbeat is within 60 seconds
- Workers marked **offline** automatically after 60 seconds without heartbeat
- Running jobs on a worker that has been offline for more than 5 minutes are marked **failed**
- The web UI shows worker status: online (green), offline (gray), busy (amber)

### Job Dispatch

Two buttons appear on CR/Bug detail pages when at least one worker is online:

| Button | Job Type | Required Status |
|--------|----------|-----------------|
| **Enrich on Worker** (amber) | `enrich` | CR: `draft` / Bug: `draft` |
| **Apply on Worker** (indigo) | `apply` | CR: `approved` / Bug: `open` or `in_progress` |

- Jobs enter a queue with status `queued`
- Workers pick up jobs via long polling — first available worker wins (atomic assignment)
- One worker handles one job at a time

### Job Execution

- The worker receives the job with a server-generated prompt appropriate to the job type
- Agent output streams to the server in batches (every ~2 seconds)
- The server relays output to the frontend via Server-Sent Events (SSE)
- On failure (non-zero exit), the job is marked `failed` with no status transition

**Enrich job prompt** follows the `sdd-remote` skill workflow:
1. Pull the latest remote state (`sdd pull`)
2. Run `sdd drafts` to list pending drafts
3. Enrich the draft with technical details, acceptance criteria, edge cases
4. Run `sdd mark-drafts-enriched` → transitions `draft → pending` (CR) / `draft → open` (Bug)
5. Run `sdd push` to publish the enriched content

**Apply job prompt** instructs the agent to implement the CR or fix the bug using the project codebase and documentation as context.

**Auto-transitions on exit code 0:**

| Job Type | Entity | From → To |
|----------|--------|-----------|
| `enrich` | CR | `draft → pending` |
| `enrich` | Bug | `draft → open` |
| `apply` | CR | `approved → applied` |
| `apply` | Bug | `open`/`in_progress → resolved` |

### Interactive Q&A

- When the agent asks a question, the worker detects it and posts it to the server
- The question appears in the web UI terminal with a text input for the user to respond
- The user's answer is sent to the server, the worker polls for it and writes it to the agent's stdin
- Multiple Q&A exchanges are supported within a single job

### Job Terminal View

- A dedicated page shows job details: status, worker name, entity link, timestamps
- A terminal-style component displays the full output stream with color-coded messages:
  - White: agent output
  - Amber/yellow: agent questions
  - Green: user answers
- Auto-scrolls during live streaming; static transcript when job is complete
- Users can cancel running or queued jobs

### Worker Jobs List

- Project-level page listing all worker jobs with status filters
- Shows worker status cards (online count / total)
- Each job row shows entity type, title, worker name, status badge, and timestamp

### Dashboard Integration

- Project dashboard shows a "Workers Online" stats card (online / total count)
- A "Recent Worker Jobs" section shows the 5 most recent jobs with status badges

## Agent Notes

- The agent adapter is configurable per worker (`--agent` flag or project config)
- Default agent is `claude` (Claude Code with `--dangerously-skip-permissions`)
- The prompt is generated server-side and includes the full CR/Bug body plus all project documentation
- Agent detection of questions uses pattern matching on stdout (lines ending with `?` or `[Y/n]`-style prompts)
- Job timeout is configurable (default 30 minutes); worker kills the agent and reports exit code 124 on timeout
