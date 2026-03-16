---
title: "User Personas"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# User Personas

### Tenant Owner

The person who creates the organization (tenant) on SDD Flow. They configure billing, invite members, and manage projects. Typically a CTO, tech lead, or founder.

- Creates and configures the tenant
- Manages billing and subscription (SaaS mode)
- Invites and removes members
- Has full access to all projects within the tenant

### Project Admin

A team member responsible for one or more projects within a tenant. They create projects, configure API keys, and oversee the SDD workflow.

- Creates and configures projects
- Generates API keys for CLI integration
- Reviews and assigns CRs and bugs
- Manages project-level settings

### Developer

A team member who works on SDD projects day-to-day. They use the web UI to create CRs and bugs, review documentation, and track progress. They may also use the SDD CLI locally.

- Creates and edits change requests and bug reports
- Views and edits SDD documentation (product/, system/)
- Tracks sync status of documentation vs. code
- Uses the CLI with an API key to sync with SDD Flow

### Viewer

A stakeholder with read-only access. They can see project status, documentation, and history but cannot make changes. Useful for managers, product owners, or clients.

- Views dashboards, documentation, CRs, and bugs
- Cannot create or modify any content
