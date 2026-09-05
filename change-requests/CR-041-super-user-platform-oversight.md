---
title: "Global SUPER_USER role for platform administration and monitoring"
status: applied
author: "user"
created-at: "2026-09-05T10:53:47.000Z"
---

# CR-041: Global SUPER_USER Role for Platform Administration and Monitoring

## Summary

Introduce a new global platform role, `SUPER_USER`, distinct from the existing tenant roles, allowing authorized operators to access a central administration area and inspect and monitor the entire SDD Flow installation.

The role must provide visibility into:

- all registered users;
- all registered tenants;
- all registered projects;
- access and security events;
- audit and operational signals useful for support, compliance, and platform oversight.

`SUPER_USER` must not be modeled as an Owner or Admin membership in every tenant. It is a platform-level role, separate from tenant membership.

## User need

As a platform operator, I need to access SDD Flow with a privileged role that gives me a global view of the installation without requiring an invitation to every tenant.

I need to:

- identify all registered users;
- identify all existing tenants;
- identify all projects and their associated tenants;
- monitor accesses and relevant events;
- investigate operational and security issues;
- keep platform administration separate from normal tenant roles.

## Product decision

Implement a global `SUPER_USER` role associated with the user account.

The recommended implementation is to add a platform role attribute to `User`:

```text
platform_role = "user" | "super_user"
```

An equivalent dedicated global-role assignment model may be used if it is architecturally preferable, but a field on `User` is the simplest and clearest first implementation.

Rules:

- every standard user has `platform_role = "user"`;
- authorized operators have `platform_role = "super_user"`;
- global `/admin/*` endpoints explicitly require `platform_role = "super_user"`;
- tenant roles (`owner`, `admin`, `member`, `viewer`) remain unchanged and apply only within their tenant.

## Core principle

`SUPER_USER` is a **platform administration role**, not a tenant role.

Therefore, a `SUPER_USER`:

- is not automatically added as a member of every tenant;
- does not alter existing memberships;
- does not replace Owner, Admin, Member, or Viewer;
- does not automatically bypass tenant-scoped endpoint authorization;
- accesses dedicated global views designed for monitoring and support;
- has all access to sensitive global views audited.

## First-iteration scope

### In scope

1. Add a global `SUPER_USER` role distinct from tenant roles.
2. Add dedicated backend authorization for platform-only endpoints.
3. Add a global administration area visible only to `SUPER_USER` users.
4. Add global read-only views for:
   - users;
   - tenants;
   - projects;
   - access and audit events.
5. Audit access to sensitive global views.
6. Record or normalize access events required for monitoring.
7. Preserve all existing tenant authorization behavior.
8. Cover the behavior with backend and frontend tests.

### Out of scope

To reduce risk and keep the first iteration safe, the following are excluded:

- user impersonation;
- global modification of tenants, projects, or their content;
- global deletion of users, tenants, or projects;
- changing tenant roles from the global admin area;
- unrestricted access to project content such as documents, CRs, bugs, and comments;
- bulk data export;
- billing or subscription management;
- MFA, if it is not already available.

Any write capability or impersonation feature must be introduced through a separate CR.

## Authorization model

### Existing tenant roles

Tenant roles remain unchanged:

| Role | Scope | Meaning |
|------|-------|---------|
| Owner | Tenant | Full control over the tenant |
| Admin | Tenant | Management of members, projects, and operational content |
| Member | Tenant/Project | Operational work on CRs, bugs, and documentation |
| Viewer | Tenant | Read-only access to tenant content |

### New platform role

Add the following global role model:

| Platform role | Scope | Meaning |
|---------------|-------|---------|
| User | Platform | Standard user who accesses only tenants where they are a member |
| Super User | Platform | Global operator with access to platform administration and monitoring |

### Access rules

- Tenant-scoped endpoints continue to use `require_role(...)` with tenant roles.
- Platform-scoped endpoints use a new check such as `require_platform_role(PlatformRole.super_user)`.
- A tenant Owner or Admin is not automatically a `SUPER_USER`.
- A `SUPER_USER` is not automatically a tenant Owner or Admin.
- Global views expose safe operational metadata, not secrets or unnecessary sensitive content.
- Backend authorization remains the source of truth; hiding frontend navigation is only a presentation safeguard.

## Bootstrapping the SUPER_USER on Cloud Run

The production deployment must use a private GitHub Actions secret containing the email address of the user to promote automatically.

### GitHub secret

Create the following private GitHub Actions repository or environment secret:

```text
CLOUDRUN_SUPER_USER_EMAIL=roberto.conterosito@applica.guru
```

The email value is supplied through a private GitHub Secret and must not be hard-coded in application source code, workflow files, container images, or committed `.env` files.

### Cloud Run runtime variable

Update `.github/workflows/cloudrun-deploy-backend.yml` so that the deploy job:

1. reads `${{ secrets.CLOUDRUN_SUPER_USER_EMAIL }}` into the workflow environment;
2. fails before deployment if the secret is missing or empty;
3. injects it into the backend Cloud Run service as:

```text
SUPER_USER_EMAIL=roberto.conterosito@applica.guru
```

The GitHub secret uses the `CLOUDRUN_` prefix consistently with the existing deployment secrets, while the backend reads the runtime variable `SUPER_USER_EMAIL`.

### Automatic promotion behavior

On backend startup, the application must:

1. read and normalize `SUPER_USER_EMAIL` by trimming whitespace and comparing email addresses case-insensitively;
2. locate the existing `User` whose normalized email matches the configured value;
3. set that user's `platform_role` to `super_user` when the user exists and is not already promoted;
4. perform the update idempotently so repeated Cloud Run deployments and multi-instance startups are safe;
5. write a platform-level audit event such as `super_user.promoted_from_environment` without exposing secrets;
6. emit a clear operational log when the configured user does not exist yet, without failing application startup.

If the configured user does not exist at startup, the same check must run after successful registration or login so that `roberto.conterosito@applica.guru` is promoted as soon as that account becomes available.

Removing or changing `SUPER_USER_EMAIL` must not automatically demote an existing `SUPER_USER`. Demotion requires an explicit administrative operation to avoid unintended privilege changes during deployment.

An in-app UI for promoting or demoting other `SUPER_USER` users remains out of scope for the first iteration.

## Global administration UX

Add a global administration area at the preferred route:

```text
/admin
```

The navigation entry must be visible only when the authenticated user has `platform_role = "super_user"`.

The UI must make it clear that the operator is in a global platform context rather than a specific tenant context.

### Overview section

Display a global summary containing:

- total number of users;
- total number of tenants;
- total number of projects;
- recent successful logins;
- recent failed logins;
- recent platform and security events.

### Users section

Display all registered users.

Recommended fields:

- email;
- display name;
- platform role;
- email verification status;
- Google login availability;
- local password availability;
- tenant membership count;
- creation timestamp;
- last update timestamp.

Recommended filters:

- search by email or display name;
- platform role;
- verified or unverified email;
- authentication provider.

Never expose:

- password hashes;
- access or refresh tokens;
- OAuth secrets or tokens;
- complete API keys.

### Tenants section

Display all registered tenants.

Recommended fields:

- name;
- slug;
- member count;
- project count;
- creation timestamp;
- last update timestamp.

Recommended filters and sorting:

- search by name or slug;
- sort by name, creation date, or project count.

### Projects section

Display all registered projects.

Recommended fields:

- project name;
- project slug;
- associated tenant;
- active or archived status;
- creation timestamp;
- last update timestamp.

Recommended filters:

- tenant;
- archived status;
- search by name or slug.

### Access & Audit section

Display global access and audit events relevant to platform operations.

Support filtering by:

- user;
- tenant, when applicable;
- project, when applicable;
- event type;
- date range;
- success or failure outcome, when applicable.

## Backend API contract

Add platform-only endpoints under a dedicated prefix:

```text
GET /admin/overview
GET /admin/users
GET /admin/tenants
GET /admin/projects
GET /admin/audit-log
```

All endpoints require:

- a valid authenticated session;
- `platform_role = "super_user"`.

### GET /admin/overview

Example response:

```json
{
  "users_count": 128,
  "tenants_count": 32,
  "projects_count": 91,
  "recent_login_count": 44,
  "recent_failed_login_count": 3,
  "recent_events": []
}
```

### GET /admin/users

Supported query parameters:

```text
?page=1&page_size=25&search=alice&platform_role=super_user&email_verified=true
```

Example item:

```json
{
  "id": "...",
  "email": "alice@example.com",
  "display_name": "Alice",
  "platform_role": "user",
  "email_verified": true,
  "google_linked": true,
  "has_password": true,
  "tenant_count": 3,
  "created_at": "...",
  "updated_at": "..."
}
```

### GET /admin/tenants

Supported query parameters:

```text
?page=1&page_size=25&search=acme
```

Example item:

```json
{
  "id": "...",
  "name": "Acme",
  "slug": "acme",
  "member_count": 12,
  "project_count": 8,
  "created_at": "...",
  "updated_at": "..."
}
```

### GET /admin/projects

Supported query parameters:

```text
?page=1&page_size=25&search=web&tenant_id=...&archived=false
```

Example item:

```json
{
  "id": "...",
  "tenant_id": "...",
  "tenant_name": "Acme",
  "name": "Web App",
  "slug": "web-app",
  "archived_at": null,
  "created_at": "...",
  "updated_at": "..."
}
```

### GET /admin/audit-log

Supported query parameters:

```text
?page=1&page_size=25&event_type=auth.login_success&user_id=...&tenant_id=...&project_id=...&from=...&to=...
```

The response must be paginated and include global events and, where appropriate, tenant and project events with sufficient context.

If the current audit model supports only tenant-scoped events, introduce platform-level audit storage for events without a tenant context, such as failed logins or access to global admin views.

## Access monitoring

Add or normalize the following events:

- `auth.login_success`;
- `auth.login_failed`;
- `auth.logout`;
- `auth.refresh`, or a summarized session event if recording every refresh is too noisy;
- `auth.password_changed`;
- `user.profile_updated`;
- `api_key.used`, or expose API key `last_used_at` safely;
- `super_user.admin_view_opened`;
- `super_user.admin_users_viewed`;
- `super_user.admin_tenants_viewed`;
- `super_user.admin_projects_viewed`;
- `super_user.admin_audit_viewed`.

Sensitive-data rules:

- never record passwords, password hashes, tokens, cookies, complete API keys, or OAuth tokens;
- store IP addresses and user-agent values only when permitted by the privacy policy and deployment requirements;
- if IP addresses or user-agent values are stored, document their purpose and retention period.

## Data model

Update `User` with a platform role:

| Field | Type | Description |
|-------|------|-------------|
| platform_role | enum | `user` or `super_user`; defaults to `user` |

Add a backend enum such as:

```text
PlatformRole.user
PlatformRole.super_user
```

Platform-level audit events must also be supported. Possible approaches are:

1. allow `tenant_id = null` on `AuditLogEntry` for platform-level events;
2. introduce a separate `PlatformAuditLogEntry` entity;
3. retain existing tenant-scoped events and add a dedicated collection only for global events.

Select the approach most consistent with the current MongoDB/Beanie architecture and the required global queries. The chosen model must preserve existing tenant audit behavior.

## Frontend contract

Expose the platform role in the current-session response. For example, `GET /auth/me` returns:

```json
{
  "id": "...",
  "email": "admin@example.com",
  "display_name": "Admin",
  "avatar_url": null,
  "has_password": true,
  "google_linked": false,
  "platform_role": "super_user"
}
```

Frontend behavior:

- show the `Admin` navigation entry only for `platform_role = "super_user"`;
- protect `/admin/*` routes in the UI;
- treat backend `403` responses as authoritative;
- use the existing layout, components, and design tokens;
- support dark mode and responsive layouts;
- provide loading, empty, and error states;
- support pagination and filters on global lists.

## Documentation changes to apply

Update:

- `product/users.md`
  - add a `Platform Operator / Super User` persona.
- `product/features/auth.md`
  - document `platform_role` and its separation from tenant roles;
  - document automatic promotion through `SUPER_USER_EMAIL`;
  - document access-monitoring events.
- `product/features/tenants.md`
  - clarify that `SUPER_USER` is not a tenant membership role and does not appear automatically in tenant member lists.
- `product/features/dashboard.md`
  - document the global admin dashboard as separate from tenant dashboards.
- `system/entities.md`
  - add `platform_role` to `User`;
  - add or extend platform-level audit storage as required.
- `system/interfaces.md`
  - add the `/admin/*` endpoints and update `GET /auth/me`;
  - document `SUPER_USER_EMAIL` as a private backend runtime variable.
- `system/architecture.md`
  - document the platform-admin boundary, authorization checks, automatic promotion, and audit/security design.
- `system/ci-pipeline.md`
  - document the private GitHub secret `CLOUDRUN_SUPER_USER_EMAIL` and its injection into Cloud Run as `SUPER_USER_EMAIL`.

## Acceptance criteria

1. A global `SUPER_USER` role exists and is distinct from tenant roles.
2. The role is associated with the user through `platform_role` or an equivalent model.
3. Standard users have `platform_role = "user"` by default.
4. All `/admin/*` endpoints require authentication and `SUPER_USER` authorization.
5. A tenant Owner or Admin without `SUPER_USER` cannot access global views.
6. A `SUPER_USER` can access the global admin area after login.
7. Frontend navigation displays the admin entry only to `SUPER_USER` users.
8. A `SUPER_USER` can list all users using safe operational metadata only.
9. A `SUPER_USER` can list all tenants with member and project counts.
10. A `SUPER_USER` can list all projects with their tenant context.
11. A `SUPER_USER` can inspect global access and audit events using filters.
12. Successful and failed logins and other relevant events are audited without secrets.
13. Access to global admin views is itself audited.
14. A `SUPER_USER` is not automatically added to every tenant member list.
15. This CR does not grant `SUPER_USER` the ability to modify tenant or project content.
16. Existing tenant authorization checks continue to work without regressions.
17. Admin pages handle loading, empty, error, pagination, filtering, dark mode, and responsive layouts.
18. Backend tests cover allowed and denied access and safe response payloads.
19. Frontend tests cover route gating and rendering of the main global lists.
20. A private GitHub Actions secret named `CLOUDRUN_SUPER_USER_EMAIL` is configured with `roberto.conterosito@applica.guru`.
21. `.github/workflows/cloudrun-deploy-backend.yml` fails fast when `CLOUDRUN_SUPER_USER_EMAIL` is missing and injects it into Cloud Run as `SUPER_USER_EMAIL`.
22. On startup, the matching existing user is promoted to `platform_role = "super_user"` idempotently.
23. If the account does not exist at startup, it is promoted automatically after its first successful registration or login.
24. Email matching is trimmed and case-insensitive.
25. Automatic promotion is audit-logged, while missing-user handling is logged without preventing startup.
26. Removing or changing the runtime variable does not automatically demote an existing `SUPER_USER`.
27. Backend tests cover startup promotion, repeated promotion, missing users, and promotion after registration or login.
28. Documentation explains the GitHub Secret to Cloud Run runtime-variable contract.

## Security notes

- `SUPER_USER` is a highly privileged role and must be assigned sparingly.
- Assignment and removal of the role must be auditable.
- No admin view may expose secrets or tokens.
- The first iteration must avoid project-content access beyond metadata required for monitoring.
- Mandatory MFA for `SUPER_USER` should be considered in a future CR.
- Retention policies should be defined for access events and any stored IP or user-agent data.

## Open questions

1. Is an operational script for manual promotion and demotion also required in addition to the Cloud Run bootstrap?
2. Should access events store IP addresses and user-agent values?
3. What retention period should apply to the global audit log?
4. Should the admin route be `/admin` or `/system/admin`?
