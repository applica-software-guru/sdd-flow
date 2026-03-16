---
title: "Multi-Tenancy & Organizations"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
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

### Tenant Switching

- Users who belong to multiple tenants see a tenant switcher in the UI
- The last-used tenant is remembered across sessions
- All data is scoped to the current tenant

### Tenant Settings

- Name and slug
- Default role for new members (Member or Viewer)
- Billing information (SaaS mode only)

## Agent Notes

- All API queries must be scoped by `tenant_id` — never leak data across tenants
- Use a middleware or dependency that injects the current tenant from the JWT
