---
title: "API Keys & CLI Integration"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# API Keys & CLI Integration

## Overview

API keys allow the SDD CLI to authenticate with SDD Flow and sync data bidirectionally. Each API key is scoped to a single project.

## Features

### API Key Management

- Admins and Owners can generate API keys for a project
- Each key has a name (e.g., "CI pipeline", "Roberto's CLI")
- Keys are shown once at creation — cannot be retrieved later
- Keys can be revoked at any time
- List all active keys with name, created date, last used date

### CLI Configuration

- The SDD CLI stores the API key in `.sdd/config.yaml`:
  ```yaml
  flow:
    url: "https://app.sddflow.com"
    api-key: "sddflow_sk_..."
  ```
- When configured, the CLI can push/pull CRs, bugs, and documentation

### API Key Authentication

- API keys are sent in the `Authorization` header: `Bearer sddflow_sk_...`
- Keys are hashed (SHA-256) in the database — only the prefix is stored in plain text for identification
- Rate limited: 100 requests/minute per key

### CLI Commands (future SDD CLI integration)

- `sdd flow push` — push local CRs, bugs, and documentation to SDD Flow
- `sdd flow pull` — pull remote CRs, bugs, and documentation to local
- `sdd flow status` — show sync status between local and remote

## Agent Notes

- API key format: `sddflow_sk_` prefix followed by 32 random hex characters
- Store only the SHA-256 hash in the database, plus the first 8 characters as a prefix for display
