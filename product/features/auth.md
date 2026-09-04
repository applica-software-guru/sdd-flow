---
title: "Authentication & Authorization"
status: synced
author: ""
last-modified: "2026-03-24T00:00:00.000Z"
version: "1.2"
---

# Authentication & Authorization

## Overview

Users can sign up and log in via Google OAuth or email/password. Authorization is role-based at the tenant level.

## Authentication

### Google OAuth

- Sign up / sign in with Google account
- Uses OAuth 2.0 authorization code flow
- On first login, a user account is created automatically
- Links Google email to the user profile

### Email & Password

- Sign up with email, password, and display name
- Email verification required before first login
- Password reset via email link
- Passwords hashed with bcrypt

### Sessions

- JWT-based authentication
- Access token (short-lived, 15 minutes) + refresh token (long-lived, 7 days)
- Tokens sent via HTTP-only cookies
- Refresh endpoint to rotate tokens
- Auth redirects preserve return URL for protected invitation acceptance flow

### Invitation Acceptance Authentication Rules

- Invitation acceptance requires an authenticated session
- If user is not authenticated, app redirects to login and then returns to invitation route
- Authenticated user email must match invitation target email
- Mismatched email blocks acceptance with explicit forbidden response

## Self-Service Profile

Every user manages their own account from a unified **Profile page** (`/settings/profile`), reachable from the header user menu. The page has three sections:

- **Account**: avatar (initials, or `avatar_url` image when present), email (read-only, with verified badge), and an editable display name saved via `PATCH /auth/me`
- **Security**: password change for password users (current password required); Google-only users can set an initial password to enable hybrid login (Google or email/password). Changing the password revokes all other sessions
- **Notification preferences**: per-event-type email toggles (see Notifications)

Rules:

- Email address cannot be changed from the profile (future feature)
- Avatar upload is not available (avatar is shown when `avatar_url` exists, e.g. from Google)
- Profile updates and password changes are audit-logged
- `/settings/notifications` redirects to `/settings/profile` for backward compatibility

## Authorization

### Roles

Roles are assigned **per tenant**. A user can have different roles in different tenants.

| Role | Description |
|------|-------------|
| **Owner** | Full control over tenant, billing, members, and all projects |
| **Admin** | Manage projects, members (except owner), CRs, bugs |
| **Member** | Create/edit CRs, bugs, documentation within assigned projects |
| **Viewer** | Read-only access to all tenant content |

### Permissions

- **Owner** can transfer ownership, delete tenant
- **Admin** can create/delete projects, invite/remove members, manage API keys
- **Member** can CRUD change requests, bugs, and documentation
- **Viewer** can only read

## Default Admin Account

On first startup (when no users exist), the backend automatically creates:

- **Admin user**: `roberto.conterosito@applica.guru` with a randomly generated password
- **Default tenant**: "Default" (slug: `default`) with the admin as Owner
- Credentials are printed to stdout on the backend console
- The admin should change the password after first login

## Agent Notes

- Use a reusable auth middleware for all protected API routes
- Store refresh tokens in the database for revocation support
- Google OAuth client ID/secret come from environment variables
