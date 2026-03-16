---
title: "Authentication & Authorization"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.1"
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

- **Admin user**: `admin@sddflow.dev` with a randomly generated password
- **Default tenant**: "Default" (slug: `default`) with the admin as Owner
- Credentials are printed to stdout on the backend console
- The admin should change the password after first login

## Agent Notes

- Use a reusable auth middleware for all protected API routes
- Store refresh tokens in the database for revocation support
- Google OAuth client ID/secret come from environment variables
