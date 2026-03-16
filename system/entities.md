---
title: "Data Entities"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
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
| title | string | CR title |
| body | text | Markdown body |
| status | enum | draft, approved, rejected, applied, closed |
| author_id | UUID | FK → User |
| assignee_id | UUID? | FK → User |
| target_files | string[]? | List of affected doc file paths |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |
| closed_at | datetime? | When the CR was closed |

### Bug

A bug report for a project.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK → Project |
| title | string | Bug title |
| body | text | Markdown body |
| status | enum | open, in-progress, resolved, wont-fix, closed |
| severity | enum | critical, major, minor, trivial |
| author_id | UUID | FK → User |
| assignee_id | UUID? | FK → User |
| created_at | datetime | Creation time |
| updated_at | datetime | Last update |
| closed_at | datetime? | When the bug was closed |

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

### RefreshToken

Stores active refresh tokens for session management.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK → User |
| token_hash | string | SHA-256 hash of the refresh token |
| expires_at | datetime | Token expiry |
| created_at | datetime | When token was issued |
