---
title: "Add draft state and AI enrichment workflow for all element types"
status: applied
author: "user"
created-at: "2026-03-17T00:00:00.000Z"
---

# CR-007: Draft State and AI Enrichment Workflow

## Summary

Introduce a universal `draft` state for all SDD element types (documents, change requests, bugs). The `draft` state indicates human-written content that may be incomplete and requires enrichment by a local AI agent before becoming operational. This is a core SDD feature, not exclusive to the remote flow.

## Motivation

When a human creates an element (via SDD Flow or locally), the content is often rough or incomplete. The AI must be able to reprocess these drafts using global project context to produce final, coherent, and complete documentation.

## New states by element type

### Documents (story files)

```
draft → new → changed → synced → deleted
```

- `draft` added to `StoryFileStatus`
- After AI enrichment the document transitions to `new`

### Change Requests

```
draft → pending → applied
```

- `pending` added to `ChangeRequestStatus` as an intermediate state
- `draft` = raw human-written content, needs enrichment
- `pending` = AI-enriched, ready to be applied to documents (former role of `draft`)

### Bugs

```
draft → open → resolved
```

- `draft` added to `BugStatus`
- After AI enrichment the bug transitions to `open`

## Changes

### Backend — Models

#### `code/backend/app/models/document_file.py`

- Added `draft` to `DocStatus` enum

#### `code/backend/app/models/change_request.py`

- Added `pending` to `CRStatus` enum

#### `code/backend/app/models/bug.py`

- Added `draft` to `BugStatus` enum

### Backend — DB Migration

#### `alembic/versions/a1b2c3d4e5f6_add_draft_and_pending_states.py`

- `ALTER TYPE doc_status_enum ADD VALUE 'draft' BEFORE 'new'`
- `ALTER TYPE bug_status_enum ADD VALUE 'draft' BEFORE 'open'`
- `ALTER TYPE cr_status_enum ADD VALUE 'pending' AFTER 'draft'`

### Backend — CLI API

#### `code/backend/app/api/cli.py`

- `GET /cli/pending-crs` — Also filters for `CRStatus.pending` (in addition to draft and approved)
- `GET /cli/open-bugs` — Also filters for `BugStatus.draft`
- **New** `POST /cli/docs/{doc_id}/enriched` — Receives enriched content, transitions `draft → new`, increments version
- **New** `POST /cli/crs/{cr_id}/enriched` — Updates enriched body, transitions `draft → pending`
- **New** `POST /cli/bugs/{bug_id}/enriched` — Updates enriched body, transitions `draft → open`

### Backend — Pydantic Schemas

#### `code/backend/app/schemas/docs.py`

- Added `DocEnrichRequest(content: str)`

#### `code/backend/app/schemas/change_requests.py`

- Added `CREnrichRequest(body: str)`

#### `code/backend/app/schemas/bugs.py`

- Added `BugEnrichRequest(body: str)`

### SDD Core — Types

#### `packages/core/src/types.ts`

- `StoryFileStatus` = `'draft' | 'new' | 'changed' | 'deleted' | 'synced'`
- `ChangeRequestStatus` = `'draft' | 'pending' | 'applied'`
- `BugStatus` = `'draft' | 'open' | 'resolved'`

### SDD Core — SDD Class

#### `packages/core/src/sdd.ts`

- **New** `drafts()` — Returns all draft elements grouped as `{ docs, crs, bugs }`
- **New** `draftEnrichmentPrompt()` — Generates AI prompt with global project context
- **New** `markDraftsEnriched(paths?)` — Transitions drafts to their next active state (docs → new, CRs → pending, bugs → open)
- `pending()` — Excludes drafts (draft ≠ pending for code sync)
- `pendingChangeRequests()` — Filters for `'pending'` instead of `'draft'`
- `markCRApplied()` — Operates on CRs with `'pending'` status
- `applyPrompt()` — Includes drafts + global project context in the prompt

### SDD Core — Prompt Generator

#### `packages/core/src/prompt/draft-prompt-generator.ts` (new)

- `generateDraftEnrichmentPrompt(drafts, projectContext, projectDescription)` — Generates a structured prompt with global project context and instructions for enriching each draft

#### `packages/core/src/prompt/apply-prompt-generator.ts`

- Accepts optional parameters `drafts`, `projectContext`, `projectDescription`
- When drafts are present, prepends an enrichment section to the prompt with global context

### SDD Core — Sync Engine

#### `packages/core/src/remote/sync-engine.ts`

- `pullFromRemote()` — Preserves `draft` status from remote instead of forcing `synced`
- `pullCRsFromRemote()` — Maps `draft` → `draft`, otherwise → `pending`
- `pullBugsFromRemote()` — Preserves `draft` status
- `pushToRemote()` — Does not mark drafts as `synced` after push

### SDD Core — API Client

#### `packages/core/src/remote/api-client.ts`

- **New** `markDocEnriched(config, docId, content)` → `POST /cli/docs/:id/enriched`
- **New** `markCREnriched(config, crId, body)` → `POST /cli/crs/:id/enriched`
- **New** `markBugEnriched(config, bugId, body)` → `POST /cli/bugs/:id/enriched`

### SDD CLI

#### `packages/cli/src/commands/mark-drafts-enriched.ts` (new)

- New command `sdd mark-drafts-enriched [files...]`

#### `packages/cli/src/commands/status.ts`

- Shows draft count with magenta color

#### `packages/cli/src/commands/cr.ts`

- Supports `draft` (◇ magenta) and `pending` (● yellow) state display

#### `packages/cli/src/commands/bug.ts`

- Supports `draft` (◇ magenta) state display

#### `packages/cli/src/ui/format.ts`

- Added `◇` icon and magenta label for `draft` status in the status table
