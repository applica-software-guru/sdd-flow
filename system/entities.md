---
title: "Data Entities"
status: synced
author: ""
last-modified: "2026-03-31T00:00:00.000Z"
version: "1.7"
---

# Data Entities

> All entities are Beanie Documents (MongoDB). Field names are stored in camelCase in MongoDB (e.g., `tenantId`) and accessed as snake_case in Python code (e.g., `tenant_id`) via Pydantic field aliases. UUID primary keys are stored as strings in MongoDB `_id`. Indexes are declared on the model class and created by Beanie at startup — there are no migration files.

### User

Represents an authenticated user of the platform.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| email | string | Unique, used for login |
| display_name | string | Shown in the UI |
| password_hash | string? | Null for Google OAuth-only users |
| google_id | string? | Google OAuth subject ID |
| avatar_url | string? | Profile picture URL |
| email_verified | boolean | Whether email has been verified |
| created_at | datetime | Account creation time |
| updated_at | datetime | Last profile update |

Indexes: `email` (unique), `google_id` (sparse unique)

### Tenant

An organization that groups projects and members.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | Display name |
| slug | string | Unique, URL-friendly identifier |
| default_role | enum | Default role for new members (member, viewer) |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Indexes: `slug` (unique)

### TenantMember

Links a user to a tenant with a role.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | Reference → Tenant |
| user_id | UUID | Reference → User |
| role | enum | owner, admin, member, viewer |
| invited_by | UUID? | Reference → User who sent the invite |
| joined_at | datetime | When the user accepted/joined |
| created_at | datetime | Record creation time |
| updated_at | datetime | Last update |

Indexes: `(tenant_id, user_id)` (unique compound)

### TenantInvitation

Pending invitation to join a tenant.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | Reference → Tenant |
| email | string | Invited email address |
| role | enum | Role to assign on acceptance |
| invited_by | UUID | Reference → User |
| token | string | Unique invitation token |
| expires_at | datetime | Invitation expiry |
| accepted_at | datetime? | Null until accepted |
| created_at | datetime | When invitation was sent |
| updated_at | datetime | Last update |

Indexes: `token` (unique), `expires_at` (TTL — documents are automatically deleted when `expires_at` is reached)

### Project

An SDD project within a tenant.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | Reference → Tenant |
| name | string | Display name |
| slug | string | Unique within tenant |
| description | string? | Optional project description |
| archived_at | datetime? | Null if active, set when archived |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Indexes: `(tenant_id, slug)` (unique compound)

### ApiKey

API key for CLI integration, scoped to a project.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Reference → Project |
| name | string | Human-readable label |
| key_prefix | string | First 8 chars of the key, for display |
| key_hash | string | SHA-256 hash of the full key |
| created_by | UUID | Reference → User |
| last_used_at | datetime? | Last API call timestamp |
| revoked_at | datetime? | Null if active |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Indexes: `key_hash` (unique)

### DocumentFile

An SDD documentation file stored in the platform.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Reference → Project |
| path | string | File path, e.g. `product/features/auth.md` |
| title | string | From frontmatter |
| status | enum | new, changed, synced, deleted |
| version | string | From frontmatter, e.g. "1.2" |
| content | text | Full markdown content including frontmatter |
| last_modified_by | UUID? | Reference → User |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Indexes: `(project_id, path)` (unique compound)

### ChangeRequest

A change request for a project.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Reference → Project |
| number | integer | Per-project progressive number (e.g. `1`, `42`). Immutable after creation. |
| slug | string | URL-friendly identifier derived from title at creation. Immutable after creation. |
| path | string? | Local file path from CLI (e.g. `change-requests/001-auth.md`) |
| title | string | CR title |
| body | text | Markdown body |
| status | enum | draft, pending, approved, rejected, applied, closed, **deleted** |
| author_id | UUID | Reference → User |
| assignee_id | UUID? | Reference → User |
| target_files | string[]? | List of affected doc file paths |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |
| closed_at | datetime? | When the CR was closed |

Indexes: `(project_id, number)` (unique compound), `(project_id, slug)` (unique compound)

**Status lifecycle**: `deleted` and `closed` are terminal states. No transition out of either is permitted.

**Number assignment:** on insert, if the CLI `path` filename has a numeric prefix (e.g. `001-fix-auth.md`), that integer is restored as the `number`; otherwise `MAX(number) + 1` within the project. If the restored number is already taken, falls back to auto-increment.

**Slug assignment:** on insert, if the CLI `path` has a numeric prefix, the slug is derived from the remainder of the filename without the `.md` extension (e.g. `001-fix-auth.md` → `fix-auth`); otherwise derived from the title (lowercase, non-alphanumeric replaced with `-`). Duplicate slugs within the same project are disambiguated by appending `-2`, `-3`, etc. The `slug` is never updated from client requests. Uniqueness is enforced by inserting and retrying with a suffix on `DuplicateKeyError` (no pre-check query).

### Bug

A bug report for a project.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Reference → Project |
| number | integer | Per-project progressive number (e.g. `1`, `42`). Immutable after creation. |
| slug | string | URL-friendly identifier derived from title at creation. Immutable after creation. |
| path | string? | Local file path from CLI (e.g. `bugs/001-login-crash.md`) |
| title | string | Bug title |
| body | text | Markdown body |
| status | enum | draft, open, in-progress, resolved, wont-fix, closed, **deleted** |
| severity | enum | critical, major, minor, trivial |
| author_id | UUID | Reference → User |
| assignee_id | UUID? | Reference → User |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |
| closed_at | datetime? | When the bug was closed |

Indexes: `(project_id, number)` (unique compound), `(project_id, slug)` (unique compound)

**Status lifecycle**: `deleted` and `closed` are terminal states. No transition out of either is permitted.

**Number and slug assignment:** same rules as ChangeRequest above.

### Comment

A comment on a CR or bug.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| entity_type | enum | change_request, bug |
| entity_id | UUID | Reference → ChangeRequest or Bug |
| author_id | UUID | Reference → User |
| body | text | Markdown content |
| created_at | datetime | Creation time |
| updated_at | datetime | Last edit time |

Indexes: `entity_id`, `(entity_type, entity_id)` compound

### AuditLogEntry

Immutable record of a system event. Inherits `ImmutableDocument` — no `updated_at`.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | Reference → Tenant |
| user_id | UUID? | Reference → User (null for system events) |
| event_type | string | e.g. `cr.created`, `bug.status_changed`, `invitation.created`, `invitation.cancelled` |
| entity_type | string? | e.g. `change_request`, `bug`, `project` |
| entity_id | UUID? | Reference to the affected entity |
| details | object | Event-specific data (native MongoDB document) |
| created_at | datetime | Event timestamp |

Indexes: `(tenant_id, created_at)`, `(tenant_id, event_type)`

Global search over audit logs matches against `event_type` via case-insensitive regex.

### Notification

A notification for a user. Inherits `ImmutableDocument` — no `updated_at`.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Reference → User |
| tenant_id | UUID | Reference → Tenant |
| event_type | string | e.g. `assigned`, `status_changed`, `mentioned` |
| entity_type | string | e.g. `change_request`, `bug` |
| entity_id | UUID | Reference to the related entity |
| title | string | Short notification text |
| read_at | datetime? | Null until read |
| created_at | datetime | When notification was created |

Indexes: `(user_id, read_at)`

### NotificationPreference

Per-user email notification settings.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Reference → User |
| event_type | string | e.g. `assigned`, `status_changed` |
| email_enabled | boolean | Whether to send email for this event type |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Indexes: `(user_id, event_type)` (unique compound)

### Worker

A registered remote worker machine that can execute AI agent jobs.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Reference → Project |
| name | string | Worker name, unique per project (default: hostname) |
| status | enum | online, offline, busy |
| agent | string | Agent adapter identifier (default: "claude") |
| branch | string? | Current git branch at worker startup (informational) |
| last_heartbeat_at | datetime | Last heartbeat timestamp |
| registered_at | datetime | First registration time |
| metadata | object? | Optional: hostname, OS, etc. (stored as `metadata` in MongoDB; Python attribute `metadata_` to avoid naming conflict) |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Indexes: `(project_id, name)` (unique compound)

Worker registration uses an atomic `find_one_and_update` upsert — concurrent registrations with the same name are safe.

### WorkerJob

A job dispatched to a worker for execution.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | Reference → Project |
| worker_id | UUID? | Reference → Worker (null while queued) |
| entity_type | string? | `change_request`, `bug`, or `document`; null for `sync` jobs |
| entity_id | UUID? | Reference to entity; null for `sync` jobs |
| job_type | enum | `apply`, `enrich`, or `sync` |
| status | enum | queued, assigned, running, completed, failed, cancelled |
| prompt | text | Generated prompt sent to the agent |
| agent | string | Agent adapter used for this job |
| model | string? | Model override passed to the agent CLI (`--model` flag) |
| exit_code | int? | Agent process exit code (null until completed/failed) |
| created_by | UUID | Reference → User who dispatched the job |
| started_at | datetime? | When agent execution began |
| completed_at | datetime? | When job finished |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Indexes: `(project_id, status)`

**Job types:**
- `enrich` — enriches a draft entity (CR/Bug/Document). Entity fields required.
- `apply` — implements an approved CR or open/in-progress Bug. Entity fields required.
- `sync` — project-level sync: pull → sync → implement all pending → push. No entity fields.

### WorkerJobMessage

A message in a job's execution transcript (output line, question, or answer). Inherits `ImmutableDocument` — no `updated_at`.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| job_id | UUID | Reference → WorkerJob |
| kind | enum | output, question, answer |
| content | text | Message content |
| sequence | int | Ordering within the job |
| created_at | datetime | Message timestamp |

Indexes: `(job_id, sequence)`

When a `WorkerJob` is deleted, all associated `WorkerJobMessage` documents must be explicitly deleted in application code (no database-level cascade).

### RefreshToken

Stores active refresh tokens for session management.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Reference → User |
| token_hash | string | SHA-256 hash of the refresh token |
| expires_at | datetime | Token expiry |
| created_at | datetime | When token was issued |
| updated_at | datetime | Last update |

Indexes: `token_hash` (unique), `expires_at` (TTL — documents are automatically deleted when `expires_at` is reached)

All refresh tokens for a user are revoked (deleted) when the user resets their password.

### PasswordResetToken

Short-lived token for the password reset flow.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Reference → User |
| token_hash | string | SHA-256 hash of the reset token |
| expires_at | datetime | Token expiry (short TTL, typically 1 hour) |
| created_at | datetime | When token was issued |

Indexes: `token_hash` (unique), `expires_at` (TTL — documents are automatically deleted when `expires_at` is reached)

The token is consumed atomically via `find_one_and_delete` — deleted as the first step of the reset flow, before the password update, to prevent replay attacks.
