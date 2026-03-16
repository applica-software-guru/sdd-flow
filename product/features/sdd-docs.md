---
title: "SDD Documentation Storage"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# SDD Documentation Storage

## Overview

SDD Flow stores the full SDD documentation tree (`product/` and `system/` files) for each project. This allows teams to view, edit, and manage documentation through the web UI without needing local filesystem access.

## Features

### Documentation Tree

- Display the file tree: `product/vision.md`, `product/users.md`, `product/features/*.md`, `system/*.md`
- Each file shows its title, status, version, and last modified date (from frontmatter)
- Tree view with expandable folders

### View & Edit Documentation

- Render markdown files with full formatting
- Edit files inline with a markdown editor
- Frontmatter is parsed and shown as metadata (status, version, author)
- On save, version is patch-bumped and last-modified is updated automatically

### Sync Status Overview

- Color-coded status indicators: new (blue), changed (yellow), synced (green), deleted (red)
- Summary: "3 files pending sync, 12 synced, 1 deleted"
- Quick filter to show only pending files

### CLI Sync

- When the SDD CLI is connected via API key, documentation can be pushed/pulled:
  - **Push**: CLI sends local documentation files to SDD Flow
  - **Pull**: CLI fetches documentation from SDD Flow to local filesystem
- Conflict detection: warn if both local and remote have changed since last sync

### Cross-Reference Validation

- Validate `[[EntityName]]` cross-references across all documentation
- Show broken references as warnings in the UI

## Agent Notes

- Documentation files are stored as markdown text in the database, not on the filesystem
- Preserve the exact SDD frontmatter format so files are compatible with the CLI
- Screenshots/images referenced in features are stored as file attachments
