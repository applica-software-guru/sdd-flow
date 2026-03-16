---
title: "Product Vision"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# Product Vision

## Summary

SDD Flow is a web platform for managing Story Driven Development projects. It provides a centralized UI and API for teams to create, track, and resolve change requests, bugs, and SDD documentation across multiple projects and organizations.

## Problem

The SDD CLI is a powerful local tool, but teams working on SDD projects lack:

- A shared view of pending CRs, bugs, and sync status across projects
- A way to manage SDD workflows without direct filesystem and git access
- Multi-project oversight for organizations running several SDD repositories
- Collaboration features — assignments, notifications, audit trails

## Solution

SDD Flow is the **companion platform** for the SDD CLI. It can be used:

- **As a SaaS** — hosted by us, teams sign up and manage projects via the web UI
- **Self-hosted** — deployed via Docker by organizations that prefer to keep data on-premise
- **Via API** — the SDD CLI connects to SDD Flow using an API key, enabling push/pull of CRs, bugs, documentation, and sync status

## Goals

1. **Centralized management** — one place to see all projects, CRs, bugs, and documentation status
2. **Team collaboration** — assign work, get notifications, track who changed what
3. **CLI integration** — the SDD CLI can optionally connect to SDD Flow to sync data bidirectionally
4. **Multi-tenant SaaS** — organizations sign up, create projects, invite members
5. **Self-hostable** — provide a Dockerfile for on-premise deployment
6. **Open source friendly** — core platform is open source, SaaS adds managed hosting

## Non-Goals

- SDD Flow does **not** replace the SDD CLI — it complements it
- SDD Flow does **not** run agents or generate code — that stays in the CLI
- SDD Flow does **not** host or deploy application code
