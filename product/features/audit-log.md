---
title: "Audit Log"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# Audit Log

## Overview

Every significant action in the system is recorded in an immutable audit log. This provides accountability, debugging context, and compliance support.

## Tracked Events

- **Auth**: login, logout, failed login attempt
- **Tenant**: created, updated, member invited/removed, ownership transferred
- **Project**: created, archived, deleted, settings changed
- **CR**: created, status changed, assigned, commented
- **Bug**: created, status changed, assigned, commented
- **Documentation**: file created, edited, deleted
- **API Key**: generated, revoked
- **User**: profile updated, notification settings changed

## Features

### Audit Log View

- Available to Owners and Admins at the tenant level
- Filterable by: event type, user, project, date range
- Each entry shows: timestamp, user, action, target entity, details
- Paginated with infinite scroll

### Event Detail

- Click an event to see full details (e.g., diff of a documentation edit, old/new status of a CR)

## Agent Notes

- Audit log entries are append-only — never update or delete them
- Store as a separate table with JSON `details` column for flexible event data
- Index on `tenant_id`, `created_at`, `event_type` for efficient filtering
