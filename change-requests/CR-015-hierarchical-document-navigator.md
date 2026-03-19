---
title: "Improve document navigation with minimal folder grouping"
status: applied
author: roberto
created-at: 2026-03-19T00:00:00Z
---

# CR-015: Improve Document Navigation with Minimal Folder Grouping

## Summary

Keep the current simple document list experience, but make it easier to scan when projects contain many documents and nested paths. This CR introduces lightweight folder grouping, search, and clearer path presentation without replacing the existing single-page flow with a heavy document browser.

## Problem

The current implementation displays all project documents in a flat list, ignoring the logical folder hierarchy that exists in their file paths. The problem is real, but the earlier tree-browser proposal added too much structure for a view that currently works well because of its simplicity.

1. Documents with logical grouping such as `architecture/`, `features/`, and `guides/` are mixed into one long list.
2. Users must read full paths line by line to understand where a document lives.
3. Large document sets become harder to scan, but a full split-pane tree would add visual and interaction complexity.
4. The current page should remain fast and obvious on both desktop and mobile.

### Example Scenario

A project with 60+ docs organized like:
```
docs/
├── architecture/
│   ├── system-overview.md
│   ├── database-schema.md
│   └── api-design.md
├── features/
│   ├── authentication.md
│   ├── permissions.md
│   └── notifications.md
├── guides/
│   ├── getting-started.md
│   ├── deployment.md
│   └── troubleshooting.md
└── api/
    ├── endpoints.md
    └── client-libraries.md
```

Currently, all 12 documents are shown in a single alphabetical list. A user looking for deployment information must either:
- Scroll through all 12 items, or
- Search by keyword

The goal is to preserve the clarity of the old page while making folder structure visible enough to reduce scanning effort.

## Solution

Implement a minimal enhancement to the existing docs page:

1. Keep a single-column list layout.
2. Group documents into compact folder sections derived from their paths.
3. Allow each folder section to collapse and expand.
4. Add a lightweight search field that filters by title and path.
5. Preserve the current create-document flow and direct navigation to document detail pages.

### UX Changes

#### 1. **Single-page list stays intact**
- Keep the existing page structure: header, create button, filters, and one main list area.
- Do not introduce a left/right split layout.
- Do not introduce a dedicated document browser page.

#### 2. **Folder grouping inside the list**
- Derive folder labels from the document path.
- Render documents in compact grouped sections such as `architecture`, `features`, or `guides`.
- Root-level documents appear in a `Root` section.
- Each section shows a document count.

#### 3. **Collapsible sections**
- Each folder section can collapse and expand.
- Default interaction remains simple: users still scroll a list, but can hide groups they do not need.
- When a search is active, matching results remain visible without extra navigation steps.

#### 4. **Lightweight search**
- Add a single search field above the list.
- Search filters by document title and path.
- Keep search behavior immediate and predictable.

#### 5. **Minimal visual cues**
- Keep document rows visually close to the current design.
- Show the full path as secondary metadata.
- Use folder headers only as lightweight separators, not as a complex tree UI.

### Implementation Approach

#### Frontend

1. **Refine the existing docs list page**
  - Add search state.
  - Group loaded documents by folder path.
  - Preserve the current create flow and row layout.

2. **Keep routing unchanged**
  - Continue using the current docs list route and doc detail route.
  - Avoid introducing a second navigation model.

3. **No backend changes required**
  - The frontend can derive folder groupings from existing `path` values.

#### Backend

- No backend change is required for this iteration.

### Interaction Flow

1. User opens project and navigates to `Documents`.
2. The page loads as the same simple list view.
3. Documents are visually grouped by folder.
4. User can collapse a folder section to reduce noise.
5. User can search by title or path to narrow the list.
6. User clicks a document row and navigates to the existing detail page.

### Acceptance Criteria

1. The docs page remains a single-column list view.
2. Documents are grouped by derived folder path.
3. Each folder group shows an accurate document count.
4. Folder groups can collapse and expand.
5. Search filters documents by title and path in real time.
6. Mobile behavior remains simple and usable without introducing drawers or split panes.
7. Existing document creation and document detail navigation continue to work.
8. No regressions in document detail view or editing workflows.

## Affected Files (Expected)

### Frontend

- `code/frontend/src/pages/DocsTreePage.tsx` (refine existing page)
- `code/frontend/e2e/docs.spec.ts` (extend existing docs coverage if needed)

## Notes

1. This CR focuses on navigation clarity while preserving the current lightweight docs UX.
2. File paths in the data model are assumed to be present and parsable.
3. This CR intentionally avoids a tree browser, drawer navigation, or folder-management features.
4. Future enhancements could introduce deeper navigation only if this lighter approach proves insufficient.

## Related CRs

- CR-009: Rich Markdown Viewer for Docs, Change Requests, and Bugs (viewer enhancement)
- CR-006: Global Search for All Entities (complementary search functionality)
