---
title: "Upgrade markdown viewing experience for docs, change requests, and bugs"
status: draft
author: "roberto"
created-at: "2026-03-18T00:00:00.000Z"
---

# CR-009: Rich Markdown Viewer for Docs, Change Requests, and Bugs

## Summary

Replace the current minimal markdown renderer with a richer shared viewer for documentation pages, change request details, bug details, and markdown-based comments.

The new viewer should support the markdown features users expect in technical content, including GitHub-flavored markdown, syntax-highlighted code blocks, better heading rendering, tables, task lists, blockquotes, and consistent typography.

## Problem

The current frontend renders markdown through a very thin wrapper around `react-markdown` with only default behavior. This is too limited for SDD content because docs, CRs, and bugs often contain:

1. fenced code blocks
2. tables
3. task lists
4. deep heading structure
5. technical notes with links and blockquotes

As a result, technical content is readable but not pleasant to consume, and structured markdown loses part of its value in the UI.

The markdown authoring experience also has a typography issue: the markdown input area uses the general application font instead of a monospaced editing font. For technical writing, this makes source markdown harder to scan, align, and edit comfortably.

## Current State

- `code/frontend/src/components/MarkdownRenderer.tsx` renders `react-markdown` without plugins or custom components
- `DocViewPage`, `CRDetailPage`, and `BugDetailPage` reuse this renderer for primary body content
- CR and bug comments also reuse the same renderer
- `code/frontend/src/components/MarkdownEditor.tsx` is used for markdown authoring, but the input typography does not currently guarantee a proper monospaced editing experience
- The editor already exists, but the read/view experience is much weaker than the editing experience

## Proposed Solution

Adopt a richer shared markdown viewer built on the existing `react-markdown` stack and extend it with focused plugins and styling, instead of introducing a full second editor framework only for reading.

### Viewer capabilities

1. Support GitHub-flavored markdown via `remark-gfm`
   - tables
   - task lists
   - strikethrough
   - autolink literals
2. Support syntax-highlighted fenced code blocks
3. Improve heading rendering and anchorability
4. Improve list, table, blockquote, inline code, and link styling
5. Preserve safe rendering rules and avoid unsafe raw HTML execution unless explicitly sanitized and approved
6. Use the same viewer for:
   - documents
   - change requests
   - bugs
   - comments on CRs and bugs

### Preferred implementation direction

Use the current `react-markdown` foundation and upgrade it with a set of battle-tested plugins and custom renderers:

- `remark-gfm`
- `rehype-slug`
- `rehype-autolink-headings` or equivalent heading anchor support
- a syntax highlighter integration for fenced code blocks

This keeps the solution lightweight, React-native, and consistent with the current codebase while materially improving readability.

## UX Requirements

1. Code blocks must be visually distinct and horizontally scrollable when needed.
2. Tables must render with borders, spacing, and overflow handling on mobile.
3. Task lists must render as checkable-looking lists in read mode.
4. The markdown input area must use a monospaced font stack suitable for technical writing.
5. The monospaced editor styling must apply consistently in all markdown authoring surfaces, including document editing, CR creation, and bug creation.
6. Long pages must remain readable with clear heading hierarchy.
7. External links should remain visually obvious and accessible.
8. The viewer and editor must work well in both light and dark themes.
9. The same markdown content should look consistent across docs, CRs, bugs, and comments.

## Security Requirements

1. Do not render unsafe raw HTML by default.
2. If HTML rendering is later enabled, it must be sanitized explicitly.
3. Links should be rendered safely with appropriate external-link behavior.

## Changes Required

### Frontend

#### `code/frontend/package.json`

- Add the markdown-viewer dependencies required for GFM, heading anchors, and code highlighting.

#### `code/frontend/src/components/MarkdownRenderer.tsx`

- Refactor the component into a richer shared markdown viewer.
- Add plugin configuration.
- Add custom renderers for code blocks, links, tables, and headings.

#### `code/frontend/src/index.css`

- Extend prose and markdown-specific styling for:
  - headings
  - tables
  - blockquotes
  - inline code
  - fenced code blocks
   - monospaced markdown editor typography
  - dark mode parity

#### `code/frontend/src/components/MarkdownEditor.tsx`

- Ensure the editor input uses an explicit monospaced font stack instead of inheriting the general application font.
- Apply the typography at the correct editor DOM layer so it affects typed markdown content reliably.

#### `code/frontend/src/pages/DocViewPage.tsx`

- Continue using the shared viewer for document content.
- Verify layout spacing works for long-form technical docs.

#### `code/frontend/src/pages/CRDetailPage.tsx`

- Continue using the shared viewer for CR body and comments.

#### `code/frontend/src/pages/BugDetailPage.tsx`

- Continue using the shared viewer for bug body and comments.

### Product documentation

#### `product/features/sdd-docs.md`

- Clarify that the documentation viewer supports richer markdown rendering.

#### `product/features/change-requests.md`

- Clarify that CR content and comments are rendered with the shared markdown viewer.

#### `product/features/bugs.md`

- Clarify that bug details and comments are rendered with the shared markdown viewer.

## Implementation Plan

1. Audit current markdown rendering usage.
   - Confirm all viewer entry points and identify where the shared component is reused.
2. Select the viewer enhancement stack.
   - Keep `react-markdown` as the base.
   - Add GFM, heading-anchor, and code-highlighting support.
3. Refactor the shared viewer component.
   - Centralize plugin wiring and custom renderers in `MarkdownRenderer.tsx`.
4. Fix markdown editor typography.
   - Apply an explicit monospaced font stack to the markdown input surface and confirm it works in every authoring flow.
5. Add markdown-specific styling.
   - Improve typography, code blocks, tables, blockquotes, and dark-mode parity.
6. Validate all consuming pages.
   - Check docs, CR details, bug details, comment rendering, and markdown editing surfaces for consistency.
7. Add or update tests.
   - Cover GFM tables, task lists, code fences, link rendering, and editor typography if practical.
8. Update product documentation.
   - Document the richer viewer behavior where markdown content is part of the feature.

## Acceptance Criteria

1. Documents render GitHub-flavored markdown correctly, including tables and task lists.
2. CR bodies and bug bodies render code fences with syntax highlighting.
3. CR and bug comments use the same shared viewer and styling.
4. All markdown input fields use a monospaced font while editing.
5. Markdown remains readable and visually consistent in both light and dark themes.
6. Long code blocks and wide tables remain usable on mobile through overflow handling.
7. Unsafe raw HTML is not executed by default.
8. Existing markdown pages and authoring flows continue to work without regression.

## Risks and Mitigations

- Risk: Adding too many markdown plugins increases bundle size.
  - Mitigation: keep the stack minimal and prefer targeted integrations over a heavy all-in-one viewer.
- Risk: Syntax highlighting may create inconsistent colors between themes.
  - Mitigation: choose a theme pair that matches the current UI and verify dark mode explicitly.
- Risk: Custom markdown styling may differ across pages.
  - Mitigation: keep all viewing behavior in one shared component and one shared style surface.

## Rollout Notes

1. Ship the shared viewer upgrade behind the existing renderer API so pages do not need broad structural changes.
2. Verify representative content samples from docs, CRs, bugs, and comments before closing the CR.