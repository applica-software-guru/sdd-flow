---
title: "Project Management"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# Project Management

## Overview

A project represents one SDD repository. It holds documentation, change requests, and bugs. Projects belong to a tenant.

## Features

### Project CRUD

- Admin or Owner can create a new project within their tenant
- Project has a name, slug, and optional description
- Projects can be archived (soft-deleted) and restored

### Project Dashboard

- Summary cards: open bugs count, pending CRs count, documentation sync status
- Recent activity feed (last 10 events)
- Quick links to create CR, create bug, view docs

### Project Settings

- Name, slug, description
- API key management (see [[ApiKeys]])
- Danger zone: archive or delete project

## Agent Notes

- Project slug must be unique within a tenant
- Archiving a project hides it from listings but preserves all data
