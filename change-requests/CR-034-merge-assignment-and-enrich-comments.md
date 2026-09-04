---
title: "Merge assignment into transition row and enrich comment metadata"
status: applied
author: "user"
created-at: "2026-09-04T00:00:00.000Z"
---

# CR-034: Merge Assignment into the Transition Row and Enrich Comment Metadata

## Summary

Two UI refinements to the CR/bug detail pages:

1. **Merge AUTHOR / ASSIGNEE / ASSIGN TO into the transition row** — the assignment metadata currently renders as a separate card below the "Transition to" card. It should be integrated into the same row as the transition controls, removing the extra card and the wasted vertical space.
2. **Enrich comment metadata** — comments currently show a placeholder "?" avatar and only a date (`04/09/2026`). They should show the commenter's avatar initials and display name, plus the timestamp with both date and time.

## Problem

1. On CR/bug detail pages the layout is: a metadata/body card → a "Transition to" card → a third, separate card for AUTHOR / ASSIGNEE / ASSIGN TO. This produces an unnecessary extra card and pushes the comments section further down, exactly the problem the scroll-to-comments feature was meant to alleviate.
2. Comments render a generic "?" circle in place of the author avatar and only display `toLocaleDateString()` (date, no time). The commenter's identity and the precise time are not visible, which weakens review collaboration (knowing who said what and when).

## Goals

1. Combine the AUTHOR / ASSIGNEE / ASSIGN TO fields into the transition row so the detail page shows one compact control band instead of a separate card.
2. Render each comment with the commenter's avatar initials, their display name, and a date + time timestamp.
3. Preserve existing behavior: assignment still flows through the same assign endpoint, transition still works, assignment history stays available.

## Proposed Solution

### Fix 1 — Merge assignment into the transition row

- On both CR and bug detail pages, render AUTHOR, ASSIGNEE, and ASSIGN TO inside the same bordered section that contains "Transition to:", aligned to the right (or as a grid) rather than as a standalone card.
- Keep the "Transition to:" label and buttons on the left; place a compact author/assignee/assign-to group on the right (or below, wrapped responsively).
- Keep the append-only **assignment history** expandable, but inside this merged section (a `<details>` block) rather than a separate card — so no history is lost.
- The merged band shows: author name, current assignee (or "Unassigned"), and the "Assign to" select.

### Fix 2 — Enrich comment metadata

- **Backend**: include the resolved `author` (`UserBrief`: id, display_name, email) on comment responses so the frontend no longer has a missing identity.
  - `list_comments` batch-resolves comment authors and attaches `author` to each `CommentResponse`.
  - `add_comment` also returns the comment with its resolved `author`.
  - `CommentResponse` gains an optional `author: UserBrief | None`.
- **Frontend**: render each comment with:
  - avatar circle showing the author's initials (reusing the `UserCell`-style initials logic, with the same color scheme),
  - the author's display name,
  - the timestamp as both date and time (`toLocaleString()`).
  - Fall back to the placeholder only when the author is unresolved.

## Required Changes

### Backend

1. `code/backend/app/schemas/comments.py`
   - add `author: UserBrief | None = None` to `CommentResponse`.
2. `code/backend/app/api/change_requests.py` (list_comments, add_comment) and `app/api/bugs.py`
   - batch-resolve comment authors via `resolve_user_briefs` and attach `author`.

### Frontend

1. `code/frontend/src/components/AssignmentPanel.tsx`
   - refactor into a compact inline band used inside the transition row (no standalone card shell, no `mb-6`), keeping the assign select and history `<details>`.
2. `code/frontend/src/pages/change-requests/DetailPage.tsx`, `code/frontend/src/pages/bugs/DetailPage.tsx`
   - move the assignment group into the transition section, aligned with the transition buttons.
   - render comment avatar initials, display name and `toLocaleString()` timestamp.

### Documentation

1. `product/features/change-requests.md` — describe the merged assignment/transition band and the enriched comment metadata (avatar, name, date+time).
2. `product/features/bugs.md` — same for bugs.

## Testing Strategy

### Backend (pytest)

1. `test_comments_include_author` — `list_comments` returns each comment with a resolved `author.display_name`.
2. `test_add_comment_returns_author` — `add_comment` response includes `author`.

### Frontend (vitest)

1. Comment metadata renders the author initials, display name, and a timestamp containing an AM/PM time (not just the date).

### E2E (playwright)

1. On a CR detail page, the AUTHOR / ASSIGNEE / ASSIGN TO fields are visible in the same section as "Transition to:" (assert their labels are present and the standalone assignment card is gone).
2. Adding a comment shows the commenter's initials and display name.

## Acceptance Criteria

1. On CR/bug detail pages, AUTHOR, ASSIGNEE, and ASSIGN TO appear in the same section as "Transition to:"; there is no separate assignment card.
2. The assignment history remains accessible (inside the merged section).
3. Each comment shows the commenter's avatar initials, display name, and a date + time timestamp.
4. Assignment and transition behavior is unchanged (same endpoints, same side effects).

## Risks and Mitigations

1. **Risk**: merging the two sections makes the control band crowded.
   - Mitigation: use a responsive layout (grid that collapses to stacked on small screens), keep "Transition to" prominent on the left and assignment on the right.
2. **Risk**: comment author resolution adds a query.
   - Mitigation: batch-resolve all comment authors in a single query (no N+1), using the existing `resolve_user_briefs`.

## Rollout Plan

1. Fix 1: refactor `AssignmentPanel` into an inline band and wire it into both detail pages.
2. Fix 2: backend comment author resolution + tests.
3. Fix 2: frontend comment metadata rendering + tests.
4. Verify e2e and run the full backend/frontend suites.
