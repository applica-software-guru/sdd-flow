---
title: "Audit Log"
status: synced
author: "roberto"
last-modified: "2026-09-04T21:00:00.000Z"
version: "1.2"
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
- Filterable by: action (free-text search over event type), entity type, user, date range
- Each row keeps a compact, consistent width and shows timestamp, author, action, and target entity
- Entries with structured detail data expose an accessible expand/collapse control; expanded details render in a full-width row directly below the event
- The target entity is identified by a human-readable label (project name, bug/CR title, document path, API key name, invited email) captured when the event happened, so it stays meaningful even after the entity is deleted
- Details render a human-readable summary plus friendly key/value pairs; raw JSON is shown only for unrecognized or legacy payloads
- Paginated list

### Event Detail

- Expand an event with structured details inline to inspect its full payload (e.g., a documentation diff or the old/new status of a CR); entries without meaningful details do not show an expansion control

## Agent Notes

- Audit log entries are append-only — never update or delete them
- Store as a separate table with JSON `details` column for flexible event data
- Index on `tenant_id`, `created_at`, `event_type` for efficient filtering
