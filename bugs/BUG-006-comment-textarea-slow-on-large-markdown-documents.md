---
title: "Comment textarea input is slow on large markdown documents"
status: resolved
author: "user"
created-at: "2026-07-16T00:00:00.000Z"
---

## Description

When typing a comment on any entity that renders a large markdown body (CR, bug), text input in the comment textarea becomes progressively slower. The more content the document contains, the more noticeable the lag. On documents with several hundred lines of markdown the UI feels unresponsive on every keystroke.

The issue does not occur when the document body is short or empty.

## Reproduction

1. Open the app and navigate to a CR or bug with a long markdown body (e.g. a CR with several sections, code blocks, and tables).
2. Scroll to the Comments section.
3. Click the comment textarea and start typing.
4. Notice that each keystroke takes a visible moment to appear — the lag increases with the length of the document body.

## Expected behavior

The comment textarea should respond instantly to keystrokes regardless of the size of the document body being displayed on the same page.

## Actual behavior

Each keystroke in the comment textarea triggers a noticeable render delay. The delay scales with the size of the markdown document displayed above the comment box.

## Root cause

The `commentBody` state is declared at the top level of `DetailPage` in both CR and bug detail views:

```typescript
// code/frontend/src/pages/change-requests/DetailPage.tsx
// code/frontend/src/pages/bugs/DetailPage.tsx
const [commentBody, setCommentBody] = useState('');
```

Every keystroke calls `setCommentBody`, which re-renders the entire `DetailPage` component tree. This causes `MarkdownRenderer` — which parses and renders the full markdown body — to re-execute on every keystroke. The larger the document, the more expensive this re-render is.

`MarkdownRenderer` is a pure presentational component: its output depends only on its props (`content`, `basePath`, `docs`, `docsRouteBase`), none of which change while the user types a comment. It is therefore an ideal candidate for memoisation.

## Resolution plan

Wrap `MarkdownRenderer` with `React.memo` so that React skips re-rendering it when its props have not changed:

```typescript
// code/frontend/src/components/MarkdownRenderer.tsx
const MarkdownRenderer = React.memo(function MarkdownRenderer({
  content,
  basePath,
  docs,
  docsRouteBase,
}: MarkdownRendererProps) {
  // ... existing implementation unchanged
});

export default MarkdownRenderer;
```

The `docs` prop is an array. `React.memo` uses shallow equality by default, so a new array reference with the same contents would still cause a re-render. To avoid this, the callers (`DetailPage` for both CR and bug) should stabilise the `docs` reference with `useMemo`:

```typescript
// code/frontend/src/pages/change-requests/DetailPage.tsx
// code/frontend/src/pages/bugs/DetailPage.tsx
const { data: docsData } = useDocs(tenantId, projectId);
const docs = useMemo(() => docsData ?? [], [docsData]);
```

This ensures the array reference is stable between re-renders unless the fetched data actually changes, so `React.memo` can correctly skip the `MarkdownRenderer` re-render while the user is typing.

## Notes

- The fix is purely additive: `React.memo` does not alter behaviour, only skips unnecessary renders.
- The same pattern should be applied consistently to all `MarkdownRenderer` usages on the page (CR/bug body and each comment rendered in the list), since they are all affected by the same re-render cascade.
- `MermaidBlock` is already isolated inside `MarkdownRenderer` and does not need separate memoisation.
