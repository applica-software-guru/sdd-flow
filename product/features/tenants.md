---
title: "Multi-Tenancy & Organizations"
status: synced
author: ""
last-modified: "2026-03-31T00:00:00.000Z"
version: "1.2"
---

# Multi-Tenancy & Organizations

## Overview

A tenant represents an organization. Each tenant has its own projects, members, and settings. Users can belong to multiple tenants.

## Features

### Tenant Creation

- Any authenticated user can create a new tenant
- Creator becomes the Owner
- Tenant has a name and a unique slug (used in URLs)

### Member Management

- Owner and Admins can invite users by email
- Invited users receive an email with an invitation link
- Pending invitations are visible in the tenant settings
- Members can leave a tenant voluntarily
- Owner can transfer ownership to another member

### Invitation Lifecycle

- Invitation is created by Owner/Admin from tenant settings with target email and role
- Backend generates a secure, single-use token with expiration
- System sends an invitation email containing the acceptance link
- Acceptance flow is completed from a dedicated frontend route
- Invite can be accepted only by an authenticated user whose email matches the invited email
- Accepted invites create tenant membership exactly once and are marked as consumed
- Owner or Admin can cancel a pending invitation at any time before it is accepted; the acceptance link becomes immediately invalid

### Invitation Error States

- If invited user is already a member, invitation creation is rejected
- Expired invitation tokens cannot be accepted
- Already accepted tokens cannot be reused
- Token acceptance with a different authenticated email is forbidden
- Invalid or unknown tokens return not found
- Attempting to accept a cancelled invitation returns not found

### Tenant Switching

- Users who belong to multiple tenants see a tenant switcher in the UI
- The last-used tenant is remembered across sessions
- All data is scoped to the current tenant

### Tenant Settings

- Name and slug
- Default role for new members (Member or Viewer)
- Billing information (SaaS mode only)
- Invitation management: send, cancel pending invitations, with clear success/error feedback

## Agent Notes

- All API queries must be scoped by `tenant_id` — never leak data across tenants
- Use a middleware or dependency that injects the current tenant from the JWT
