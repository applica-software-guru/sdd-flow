---
title: "Data Entities"
status: synced
author: ""
last-modified: "2026-03-26T12:00:00.000Z"
version: "1.4"
---

# Data Entities

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

### TenantMember

Join table linking users to tenants with a role.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | FK → Tenant |
| user_id | UUID | FK → User |
| role | enum | owner, admin, member, viewer |
| invited_by | UUID? | FK → User who sent the invite |
| joined_at | datetime | When the user accepted/joined |

Unique constraint: `(tenant_id, user_id)`

### TenantInvitation

Pending invitation to join a tenant.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | FK → Tenant |
| email | string | Invited email address |
| role | enum | Role to assign on acceptance |
| invited_by | UUID | FK → User |
| token | string | Unique invitation token |
| expires_at | datetime | Invitation expiry |
| accepted_at | datetime? | Null until accepted |
| created_at | datetime | When invitation was sent |

### Project

An SDD project within a tenant.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | FK → Tenant |
| name | string | Display name |
| slug | string | Unique within tenant |
| description | string? | Optional project description |
| archived_at | datetime? | Null if active, set when archived |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Unique constraint: `(tenant_id, slug)`

### ApiKey

API key for CLI integration, scoped to a project.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK → Project |
| name | string | Human-readable label |
| key_prefix | string | First 8 chars of the key, for display |
| key_hash | string | SHA-256 hash of the full key |
| created_by | UUID | FK → User |
| last_used_at | datetime? | Last API call timestamp |
| revoked_at | datetime? | Null if active |
| created_at | datetime | Creation time |

### DocumentFile

An SDD documentation file stored in the platform.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK → Project |
| path | string | File path, e.g. `product/features/auth.md` |
| title | string | From frontmatter |
| status | enum | new, changed, synced, deleted |
| version | string | From frontmatter, e.g. "1.2" |
| content | text | Full markdown content including frontmatter |
| last_modified_by | UUID? | FK → User |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Unique constraint: `(project_id, path)`

### ChangeRequest

A change request for a project.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK → Project |
| number | integer | Per-project progressive number (e.g. `1`, `42`). Immutable after creation. |
| slug | string | URL-friendly identifier derived from title at creation. Immutable after creation. |
| path | string? | Local file path from CLI (e.g. `change-requests/001-auth.md`) |
| title | string | CR title |
| body | text | Markdown body |
| status | enum | draft, pending, approved, rejected, applied, closed |
| author_id | UUID | FK → User |
| assignee_id | UUID? | FK → User |
| target_files | string[]? | List of affected doc file paths |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |
| closed_at | datetime? | When the CR was closed |

Unique constraints: `(project_id, number)`, `(project_id, slug)`

**Number assignment:** on insert, if the CLI `path` filename has a numeric prefix (e.g. `001-fix-auth.md`), that integer is restored as the `number`; otherwise `MAX(number) + 1` within the project. If the restored number is already taken, falls back to auto-increment.

**Slug assignment:** on insert, if the CLI `path` has a numeric prefix, the slug is derived from the remainder of the filename without the `.md` extension (e.g. `001-fix-auth.md` → `fix-auth`); otherwise derived from the title (lowercase, non-alphanumeric replaced with `-`). Duplicate slugs within the same project are disambiguated by appending `-2`, `-3`, etc. The `slug` is never updated from client requests.

### Bug

A bug report for a project.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK → Project |
| number | integer | Per-project progressive number (e.g. `1`, `42`). Immutable after creation. |
| slug | string | URL-friendly identifier derived from title at creation. Immutable after creation. |
| path | string? | Local file path from CLI (e.g. `bugs/001-login-crash.md`) |
| title | string | Bug title |
| body | text | Markdown body |
| status | enum | draft, open, in-progress, resolved, wont-fix, closed |
| severity | enum | critical, major, minor, trivial |
| author_id | UUID | FK → User |
| assignee_id | UUID? | FK → User |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |
| closed_at | datetime? | When the bug was closed |

Unique constraints: `(project_id, number)`, `(project_id, slug)`

**Number and slug assignment:** same rules as ChangeRequest above.

### Comment

A comment on a CR or bug.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| entity_type | enum | change_request, bug |
| entity_id | UUID | FK → ChangeRequest or Bug |
| author_id | UUID | FK → User |
| body | text | Markdown content |
| created_at | datetime | Creation time |
| updated_at | datetime | Last edit time |

### AuditLogEntry

Immutable record of a system event.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | FK → Tenant |
| user_id | UUID? | FK → User (null for system events) |
| event_type | string | e.g. `cr.created`, `bug.status_changed` |
| entity_type | string? | e.g. `change_request`, `bug`, `project` |
| entity_id | UUID? | FK to the affected entity |
| details | jsonb | Event-specific data |
| created_at | datetime | Event timestamp |

Index: `(tenant_id, created_at)`, `(tenant_id, event_type)`

### Notification

A notification for a user.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK → User |
| tenant_id | UUID | FK → Tenant |
| event_type | string | e.g. `assigned`, `status_changed`, `mentioned` |
| entity_type | string | e.g. `change_request`, `bug` |
| entity_id | UUID | FK to the related entity |
| title | string | Short notification text |
| read_at | datetime? | Null until read |
| created_at | datetime | When notification was created |

### NotificationPreference

Per-user email notification settings.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK → User |
| event_type | string | e.g. `assigned`, `status_changed` |
| email_enabled | boolean | Whether to send email for this event type |

Unique constraint: `(user_id, event_type)`

### Worker

A registered remote worker machine that can execute AI agent jobs.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK → Project |
| name | string | Worker name, unique per project (default: hostname) |
| status | enum | online, offline, busy |
| agent | string | Agent adapter identifier (default: "claude") |
| last_heartbeat_at | datetime | Last heartbeat timestamp |
| registered_at | datetime | First registration time |
| metadata | jsonb? | Optional: hostname, OS, etc. |

Unique constraint: `(project_id, name)`

### WorkerJob

A job dispatched to a worker for execution.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK → Project |
| worker_id | UUID? | FK → Worker (null while queued) |
| entity_type | string | `change_request` or `bug` |
| entity_id | UUID | FK → ChangeRequest or Bug |
| job_type | enum | `apply` (default), `enrich` |
| status | enum | queued, assigned, running, completed, failed, cancelled |
| prompt | text | Generated prompt sent to the agent |
| agent | string | Agent adapter used for this job |
| exit_code | int? | Agent process exit code (null until completed/failed) |
| created_by | UUID | FK → User who dispatched the job |
| started_at | datetime? | When agent execution began |
| completed_at | datetime? | When job finished |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |

Index: `(project_id, status)`

### WorkerJobMessage

A message in a job's execution transcript (output line, question, or answer).

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| job_id | UUID | FK → WorkerJob (CASCADE delete) |
| kind | enum | output, question, answer |
| content | text | Message content |
| sequence | int | Ordering within the job |
| created_at | datetime | Message timestamp |

Index: `(job_id, sequence)`

### RefreshToken

Stores active refresh tokens for session management.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK → User |
| token_hash | string | SHA-256 hash of the refresh token |
| expires_at | datetime | Token expiry |
| created_at | datetime | When token was issued |
