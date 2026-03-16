---
title: "Extend global search (Cmd+K) to cover all entities including audit logs"
status: applied
author: "user"
created-at: "2026-03-17T00:00:00.000Z"
---

# CR-006: Extend Global Search to All Entities

## Summary

Enhance the existing global search (Cmd+K / click on search bar) to search across **all** entity types: projects, documents, change requests, bugs, **and audit log entries**. Improve the search modal UX with entity type filtering tabs and better result navigation.

## Current State

- Backend (`GET /tenants/:tenant_id/search`) searches projects, documents, CRs, and bugs using `ILIKE`
- Frontend `SearchModal` opens via `Cmd+K` or clicking the search bar, displays results with type badges
- Audit log entries are **not** included in search results

## Changes Required

### Update `system/interfaces.md`

Update the search endpoint documentation:

- Add `audit_log` as a searchable entity type
- Add `audit_log` to the optional `type` filter values: `cr`, `bug`, `doc`, `project`, `audit_log`

### Update `product/features/search.md`

Add audit log to the list of searchable entities and document the entity type filter tabs in the search modal.

### Backend changes

#### `code/backend/app/api/search.py`

- Add audit log search: query `AuditLogEntry` matching `event_type` or `details` (cast JSONB to text) against the search term via `ILIKE`
- Return audit log results with `entity_type: "audit_log"`, the `event_type` as title, and a snippet from the `details` JSON

#### `code/backend/app/schemas/search.py`

- Add `"audit_log"` to the `entity_type` allowed values

### Frontend changes

#### `code/frontend/src/components/SearchModal.tsx`

- Add horizontal filter tabs at the top of the results area: **All**, **Projects**, **Docs**, **CRs**, **Bugs**, **Audit Log**
- Clicking a tab filters results by entity type (pass the `type` query param to the API)
- **All** tab shows results from every entity (current behavior)
- Show an icon per entity type in each result row (folder for projects, file for docs, git-pull-request for CRs, bug for bugs, clock/history for audit log)
- Clicking a result navigates to the appropriate detail page; for audit log entries, navigate to the audit log page

#### `code/frontend/src/types/index.ts`

- Add `"audit_log"` to the `SearchResult.type` union

#### `code/frontend/src/hooks/useSearch.ts`

- Pass the optional `type` filter parameter to the API when a specific tab is selected
