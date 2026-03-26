---
title: "API Interfaces"
status: synced
author: ""
last-modified: "2026-03-26T12:00:00.000Z"
version: "1.9"
---

# API Interfaces

Base URL: `/api/v1`

All endpoints return JSON. Errors use the format:

```json
{ "detail": "Error message" }
```

---

## Environment Configuration Interface

This project uses immutable container images with runtime configuration injected by environment variables.

### Backend runtime variables

Required:

- `DATABASE_URL`
- `JWT_SECRET`
- `FRONTEND_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `MAIL_FROM_EMAIL`
- `MAIL_FROM_NAME`

Optional:

- `AUTH_COOKIE_SECURE` (`true` for HTTPS deployments)
- `AUTH_COOKIE_SAMESITE` (`lax` default; configurable for cross-site flows)
- `MAIL_PROVIDER` (`brevo`, `smtp` or `log`)
- `MAIL_SMTP_HOST`
- `MAIL_SMTP_PORT`
- `MAIL_SMTP_USERNAME`
- `MAIL_SMTP_PASSWORD`
- `MAIL_SMTP_USE_TLS` (`true` default)
- `BREVO_API_KEY` (required when `MAIL_PROVIDER=brevo`)

### Frontend container runtime variables

Required:

- `NGINX_SERVER_NAME` (default `_`)
- `BACKEND_UPSTREAM` (default `backend:8000`)

Optional:

- `PUBLIC_APP_DOMAIN`

### Canonical/alias compatibility rules

- Canonical names are the variables listed above.
- If `APP_DOMAIN` is provided for compatibility:
  - `FRONTEND_URL` takes precedence when both exist.
  - If only `APP_DOMAIN` is set, derive `FRONTEND_URL=https://<APP_DOMAIN>`.
- Legacy aliases remain supported for at least one release cycle with deprecation warnings.

### Validation behavior

- Backend startup must fail fast when required variables are missing.
- Frontend container startup must fail fast when required runtime proxy/domain parameters are missing.
- Validation errors must list missing variable names explicitly.

### Public config vs secret classification

- Public/runtime-safe: `FRONTEND_URL`, `NGINX_SERVER_NAME`, `BACKEND_UPSTREAM`, `PUBLIC_APP_DOMAIN`.
- Secret: `JWT_SECRET`, `GOOGLE_CLIENT_SECRET`, API tokens and other credentials.
- OAuth access tokens are dynamic flow outputs and are not static environment variables.

---

## Auth

### POST /auth/register

Create a new account with email/password.

**Body:** `{ email, password, display_name }`
**Response:** `201` `{ id, email, display_name }`

### POST /auth/login

Log in with email/password. Sets JWT cookies.

**Body:** `{ email, password }`
**Response:** `200` `{ id, email, display_name }`
**Cookies:** `access_token`, `refresh_token` (HTTP-only)

### POST /auth/refresh

Refresh the access token using the refresh token cookie.

**Response:** `200` `{}`
**Cookies:** new `access_token`

### POST /auth/logout

Clear auth cookies and revoke refresh token.

**Response:** `204`

### GET /auth/google

Redirect to Google OAuth consent screen.

**Response:** `302` redirect

### GET /auth/google/callback

Google OAuth callback. Sets JWT cookies and redirects to frontend.

**Query:** `code`, `state`
**Response:** `302` redirect to frontend

### GET /auth/me

Get the current authenticated user.

**Response:** `200` `{ id, email, display_name, avatar_url }`

---

## Tenants

All tenant endpoints require authentication.

### POST /tenants

Create a new tenant. Caller becomes Owner.

**Body:** `{ name, slug }`
**Response:** `201` `{ id, name, slug, created_at }`

### GET /tenants

List tenants the current user belongs to.

**Response:** `200` `[{ id, name, slug, role }]`

### GET /tenants/:tenant_id

Get tenant details.

**Response:** `200` `{ id, name, slug, default_role, created_at }`

### PATCH /tenants/:tenant_id

Update tenant settings. Owner or Admin only.

**Body:** `{ name?, slug?, default_role? }`
**Response:** `200` `{ id, name, slug, default_role }`

### GET /tenants/:tenant_id/members

List tenant members.

**Response:** `200` `[{ id, user_id, email, display_name, role, joined_at }]`

### POST /tenants/:tenant_id/invitations

Invite a user by email. Owner or Admin only.

**Body:** `{ email, role }`
**Response:** `201` `{ id, tenant_id, email, role, token, expires_at, accepted_at, created_at }`

Validation and behavior:

- Returns `409` if invited email already belongs to an existing tenant member
- Triggers invitation email delivery containing acceptance link generated from `FRONTEND_URL`

### POST /tenants/invitations/:token/accept

Accept an invitation.

**Response:** `200` `{ id, user_id, email, display_name, role, joined_at }`

Validation and behavior:

- Returns `404` when token is not found
- Returns `400` when invitation is expired or already accepted
- Returns `403` when authenticated user email does not match invitation email
- Returns `409` when user is already a member

### DELETE /tenants/:tenant_id/members/:user_id

Remove a member. Owner or Admin only.

**Response:** `204`

---

## Projects

All project endpoints are scoped to a tenant: `/tenants/:tenant_id/projects`

### POST /tenants/:tenant_id/projects

Create a project. Admin or Owner only.

**Body:** `{ name, slug, description? }`
**Response:** `201` `{ id, name, slug, description, created_at }`

### GET /tenants/:tenant_id/projects

List projects in the tenant.

**Query:** `archived=true` to include archived
**Response:** `200` `[{ id, name, slug, description, archived_at, stats }]`

`stats`: `{ open_bugs, pending_crs, docs_synced, docs_total }`

### GET /tenants/:tenant_id/projects/:project_id

Get project details.

**Response:** `200` `{ id, name, slug, description, archived_at, stats, created_at }`

### PATCH /tenants/:tenant_id/projects/:project_id

Update project. Admin or Owner only.

**Body:** `{ name?, slug?, description? }`
**Response:** `200` `{ ... }`

### POST /tenants/:tenant_id/projects/:project_id/archive

Archive a project. Admin or Owner only.

**Response:** `200` `{ archived_at }`

### POST /tenants/:tenant_id/projects/:project_id/restore

Restore an archived project. Admin or Owner only.

**Response:** `200` `{ archived_at: null }`

### POST /tenants/:tenant_id/projects/:project_id/reset

Reset all project data (docs, CRs, bugs, comments, notifications). Admin or Owner only. Requires slug confirmation to prevent accidental resets.

**Body:** `{ confirm_slug: "project-slug" }`
**Response:** `200` `{ message, deleted_documents, deleted_change_requests, deleted_bugs, deleted_comments, deleted_notifications }`
**Error:** `400` if slug does not match

---

## Change Requests

Scoped to a project: `/tenants/:tenant_id/projects/:project_id/crs`

### POST .../crs

Create a CR.

**Body:** `{ title, body, target_files?, assignee_id? }`
**Response:** `201` `{ id, number, formatted_number, slug, title, status: "draft", ... }`

### GET .../crs

List CRs.

**Query:** `status`, `author_id`, `assignee_id`, `page`, `per_page`
**Response:** `200` `{ items: [{ ..., number, formatted_number, slug }], total, page, per_page }`

### GET .../crs/:cr_id

Get CR details.

**Response:** `200` `{ id, number, formatted_number, slug, title, body, status, author, assignee, target_files, comments, created_at, updated_at }`

### PATCH .../crs/:cr_id

Update a CR. The `slug` field is ignored if sent — it is immutable after creation.

**Body:** `{ title?, body?, target_files?, assignee_id? }`
**Response:** `200` `{ ..., number, formatted_number, slug }`

### POST .../crs/:cr_id/transition

Change CR status.

**Body:** `{ status, comment? }`
**Response:** `200` `{ id, status }`

Allowed transitions:

- `draft` → `approved`, `rejected`
- `approved` → `applied`
- `applied` → `closed`
- `rejected` → `closed`, `draft` (reopen)

---

## Bugs

Scoped to a project: `/tenants/:tenant_id/projects/:project_id/bugs`

### POST .../bugs

Create a bug.

**Body:** `{ title, body, severity, assignee_id? }`
**Response:** `201` `{ id, number, formatted_number, slug, title, status: "open", severity, ... }`

### GET .../bugs

List bugs.

**Query:** `status`, `severity`, `author_id`, `assignee_id`, `page`, `per_page`
**Response:** `200` `{ items: [{ ..., number, formatted_number, slug }], total, page, per_page }`

### GET .../bugs/:bug_id

Get bug details.

**Response:** `200` `{ id, number, formatted_number, slug, title, body, status, severity, author, assignee, comments, created_at, updated_at }`

### PATCH .../bugs/:bug_id

Update a bug. The `slug` field is ignored if sent — it is immutable after creation.

**Body:** `{ title?, body?, severity?, assignee_id? }`
**Response:** `200` `{ ..., number, formatted_number, slug }`

### POST .../bugs/:bug_id/transition

Change bug status.

**Body:** `{ status, comment? }`
**Response:** `200` `{ id, status }`

Allowed transitions:

- `open` → `in-progress`, `wont-fix`
- `in-progress` → `resolved`, `open` (back to open)
- `resolved` → `closed`
- `wont-fix` → `closed`, `open` (reopen)

---

## Comments

### POST .../crs/:cr_id/comments | POST .../bugs/:bug_id/comments

Add a comment.

**Body:** `{ body }`
**Response:** `201` `{ id, body, author, created_at }`

### PATCH .../comments/:comment_id

Edit a comment. Author only.

**Body:** `{ body }`
**Response:** `200` `{ id, body, updated_at }`

---

## Documentation

Scoped to a project: `/tenants/:tenant_id/projects/:project_id/docs`

### GET .../docs

List all documentation files.

**Response:** `200` `[{ id, path, title, status, version, updated_at }]`

### GET .../docs/:doc_id

Get a documentation file.

**Response:** `200` `{ id, path, title, status, version, content, updated_at }`

### PUT .../docs/:doc_id

Update a documentation file. Auto-bumps version and updates timestamp.

**Body:** `{ content }`
**Response:** `200` `{ id, path, title, status, version, updated_at }`

### POST .../docs

Create a new documentation file.

**Body:** `{ path, content }`
**Response:** `201` `{ id, path, title, status, version }`

### DELETE .../docs/:doc_id

Mark a documentation file as deleted.

**Response:** `204`

### POST .../docs/bulk

Bulk upsert documentation files (used by CLI push).

**Body:** `{ files: [{ path, content }] }`
**Response:** `200` `{ created: n, updated: n }`

---

## API Keys

Scoped to a project: `/tenants/:tenant_id/projects/:project_id/api-keys`

### POST .../api-keys

Generate a new API key. Admin or Owner only.

**Body:** `{ name }`
**Response:** `201` `{ id, name, key, key_prefix, created_at }`

Note: `key` is the full plaintext key, shown only once.

### GET .../api-keys

List API keys for the project.

**Response:** `200` `[{ id, name, key_prefix, last_used_at, revoked_at, created_at }]`

### DELETE .../api-keys/:key_id

Revoke an API key. Admin or Owner only.

**Response:** `204`

---

## Search

### GET /tenants/:tenant_id/search

Global search across the tenant.

**Query:** `q` (search term), `type` (project, doc, cr, bug, audit_log — optional filter)
**Response:** `200` `{ results: [{ type, id, project_id, title, snippet }] }`

---

## Notifications

### GET /notifications

List notifications for the current user.

**Query:** `unread_only=true`, `page`, `per_page`
**Response:** `200` `{ items: [...], unread_count, total }`

### POST /notifications/:id/read

Mark a notification as read.

**Response:** `200`

### POST /notifications/read-all

Mark all notifications as read.

**Response:** `200`

---

## Audit Log

### GET /tenants/:tenant_id/audit-log

List audit log entries. Owner or Admin only.

**Query:** `event_type`, `user_id`, `project_id`, `from`, `to`, `page`, `per_page`
**Response:** `200` `{ items: [{ id, event_type, user, entity_type, entity_id, details, created_at }], total }`

---

## Workers & Jobs

Scoped to a project: `/tenants/:tenant_id/projects/:project_id`

### GET .../workers

List registered workers for the project. Each worker includes a computed `is_online` field (true if last heartbeat within 60 seconds).

**Response:** `200` `[{ id, name, status, agent, branch, is_online, last_heartbeat_at, registered_at }]`

### GET .../worker-jobs/agent-models

Return available models grouped by agent adapter. Used to populate the Job Options Dialog.

**Response:** `200` `{ claude: [{ id, label }, ...], codex: [...], opencode: [...] }`

### POST .../worker-jobs/preview

Generate the prompt for a job without creating it. Used for the prompt preview in the Job Options Dialog.

**Body:** `{ entity_type?, entity_id?, job_type }`
- `entity_type`/`entity_id` required for `enrich`/`apply`; omit for `sync`

**Response:** `200` `{ prompt: string }`

### POST .../worker-jobs

Create a new worker job (dispatch to queue).

**Body:** `{ entity_type?, entity_id?, job_type?, agent?, model?, prompt?, worker_id? }`
- `job_type`: `"apply"`, `"enrich"` (default), or `"sync"`
- `entity_type`: `change_request`, `bug`, or `document`; omit for `sync` jobs
- `model`: optional model override passed to the agent CLI (`--model` flag)
- `prompt`: optional prompt override (if omitted, server generates it)
- `worker_id`: optional target worker; if omitted, any available worker picks it up

**Response:** `201` `{ id, entity_type, entity_id, job_type, status: "queued", agent, model, created_at }`

Validation:
- `entity_type` and `entity_id` are required for `enrich`/`apply` jobs
- `entity_type` must be `change_request`, `bug`, or `document`
- For `job_type: "enrich"`: entity must be in `draft` status
- For `job_type: "apply"`: CR must be `approved`; Bug must be `open` or `in_progress`; documents are not supported with `apply`
- Returns `400` if entity is not in a valid status for the given job type

### GET .../worker-jobs

List worker jobs for the project.

**Query:** `status`, `page`, `page_size`
**Response:** `200` `{ items: [{ id, entity_type, entity_id, entity_title, job_type, status, agent, model, worker_name, exit_code, created_at, completed_at }], total, page, page_size }`

### GET .../worker-jobs/:job_id

Get job details including full message transcript.

**Response:** `200` `{ id, entity_type, entity_id, entity_title, job_type, status, agent, model, worker_name, exit_code, started_at, completed_at, created_at, messages: [{ id, kind, content, sequence, created_at }] }`

### GET .../worker-jobs/:job_id/stream

Server-Sent Events stream for real-time job output. Polls the database every 0.5 seconds and yields new messages as SSE events. Sends a `done` event when the job reaches a terminal status.

**Response:** `200` `text/event-stream`
**Events:** `data: { id, kind, content, sequence, created_at }` | `event: done\ndata: { type, status, exit_code }`

When the frontend receives the `done` event it invalidates the React Query cache for the job, causing the status badge to update automatically.

### POST .../worker-jobs/:job_id/answer

Post a user answer to an agent question.

**Body:** `{ content }`
**Response:** `201` `{ id, kind: "answer", content, sequence, created_at }`

### POST .../worker-jobs/:job_id/cancel

Cancel a queued or running job.

**Response:** `200` `{ id, status: "cancelled" }`

---

## CLI Integration (API Key Auth)

These endpoints accept API key auth (`Authorization: Bearer sddflow_sk_...`) instead of JWT cookies. The API key implicitly scopes requests to its project.

### GET /cli/pending-crs

Get draft/pending/approved CRs.

**Response:** `200` `[{ id, project_id, number, formatted_number, slug, path, title, body, status, author_id, assignee_id, target_files, closed_at, created_at, updated_at }]`

### GET /cli/open-bugs

Get draft/open/in-progress bugs.

**Response:** `200` `[{ id, project_id, number, formatted_number, slug, path, title, body, status, severity, author_id, assignee_id, closed_at, created_at, updated_at }]`

### POST /cli/crs/:cr_id/applied

Mark a CR as applied.

**Response:** `200` `{ id, number, formatted_number, slug, path, title, body, status, ... }`

### POST /cli/bugs/:bug_id/resolved

Mark a bug as resolved.

**Response:** `200` `{ id, number, formatted_number, slug, path, title, body, status, ... }`

### POST /cli/push-docs

Push local documentation to SDD Flow.

**Body:** `{ documents: [{ path, title, content }] }`
**Response:** `200` `{ created, updated, documents: [{ id, path, title, status, version, content, ... }] }`

### GET /cli/pull-docs

Pull documentation from SDD Flow.

**Response:** `200` `[{ id, path, title, status, version, content, ... }]`

### POST /cli/push-crs

Push change requests from CLI.

**Body:** `{ change_requests: [{ path, title, body, status?, id? }] }`
**Response:** `200` `{ created, updated, change_requests: [{ id, number, formatted_number, slug, path, title, body, status, ... }] }`

Number and slug are server-generated. If `path` has a numeric prefix (e.g. `001-fix-auth.md`), the server restores that number and derives the slug from the path remainder. For existing entities (push with `id`), `number` and `slug` are immutable and never updated from the payload.

### POST /cli/push-bugs

Push bugs from CLI.

**Body:** `{ bugs: [{ path, title, body, severity?, status?, id? }] }`
**Response:** `200` `{ created, updated, bugs: [{ id, number, formatted_number, slug, path, title, body, status, severity, ... }] }`

Same number and slug rules as `push-crs`.

### POST /cli/docs/:doc_id/enriched

Submit enriched content for a draft document.

**Body:** `{ content }`
**Response:** `200` `{ id, path, title, status, version, ... }`

### POST /cli/crs/:cr_id/enriched

Submit enriched content for a draft CR.

**Body:** `{ body }`
**Response:** `200` `{ id, number, formatted_number, slug, path, title, body, status, ... }`

### POST /cli/bugs/:bug_id/enriched

Submit enriched content for a draft bug.

**Body:** `{ body }`
**Response:** `200` `{ id, number, formatted_number, slug, path, title, body, status, ... }`

### POST /cli/workers/register

Register or reconnect a worker. Upserts by (project_id, name). Sends the current git branch at startup so it is visible in the web UI.

**Body:** `{ name, agent?, branch?, metadata? }`
**Response:** `200` `{ id, name, status, agent, branch, registered_at }`

### POST /cli/workers/:worker_id/heartbeat

Send worker heartbeat. Also triggers stale worker/job cleanup.

**Body:** `{ status }`
**Response:** `200` `{ ok: true }`

### GET /cli/workers/:worker_id/poll

Long-poll for a queued job (holds connection up to 30 seconds). Atomically assigns the job to the requesting worker using `SELECT FOR UPDATE SKIP LOCKED`.

**Response:** `200` `{ job_id, entity_type, entity_id, job_type, prompt, agent, model, branch }` or `204` if no job available

- `entity_type`/`entity_id` are null for `sync` jobs
- `model` is the model override requested by the user (null if default)
- `branch` is the worker's registered branch at startup (informational)

### POST /cli/workers/jobs/:job_id/started

Notify that the worker has started executing the agent.

**Response:** `200` `{ ok: true }`

### POST /cli/workers/jobs/:job_id/output

Post a batch of output lines from the agent.

**Body:** `{ lines: [string] }`
**Response:** `200` `{ ok: true }`

### POST /cli/workers/jobs/:job_id/question

Post an agent question for the user to answer. Triggers a `worker_question` notification to the job creator.

**Body:** `{ content }`
**Response:** `200` `{ ok: true }`

### GET /cli/workers/jobs/:job_id/answers

Get user answers posted after a given sequence number.

**Query:** `after_sequence`
**Response:** `200` `[{ id, kind: "answer", content, sequence, created_at }]`

### POST /cli/workers/jobs/:job_id/completed

Mark a job as completed or failed. On success (`exit_code: 0`):
- CR enrich: `draft → pending`
- Bug enrich: `draft → open`
- Document enrich: `draft → new`
- CR apply: `approved → applied`
- Bug apply: `open`/`in_progress → resolved`
- Sync: no entity transition (CLI commands handle it)

Triggers a `worker_job_completed` or `worker_job_failed` notification to the job creator.

**Body:** `{ exit_code }`
**Response:** `200` `{ status, exit_code }`

### POST /cli/reset

Reset all project data (docs, CRs, bugs, comments, notifications). Requires slug confirmation.

**Body:** `{ confirm_slug: "project-slug" }`
**Response:** `200` `{ message, deleted_documents, deleted_change_requests, deleted_bugs, deleted_comments, deleted_notifications }`
**Error:** `400` if slug does not match
