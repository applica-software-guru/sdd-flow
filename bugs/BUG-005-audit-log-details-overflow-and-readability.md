---
title: "Audit log details overflow table bounds and need monospace formatting"
status: resolved
author: "roberto"
created-at: "2026-03-19T00:00:00.000Z"
---

## Description

On the Audit Log page, the `details` column does not handle very long content correctly. When the details payload is large, the text expands beyond the table cell and visually breaks the table layout.

In addition, the `details` content contains structured log data and should be rendered with a monospace font to improve readability and scanning.

## Steps to reproduce

1. Open the application and navigate to the Audit Log page.
2. Ensure there is at least one audit log entry with a long `details` payload (for example a large JSON-like object or a long serialized change summary).
3. Observe the `details` column in the table.

## Expected behavior

1. The `details` column should remain constrained inside the table layout.
2. Long content should wrap, truncate, scroll, or otherwise remain visually contained without overflowing outside the table.
3. The `details` content should use a monospace font to better represent structured log payloads.

## Actual behavior

1. Very long `details` values extend outside the table bounds.
2. The table becomes harder to read because one oversized cell distorts the layout.
3. The `details` content is displayed with the same proportional font used for regular UI text, which reduces readability for structured values.

## Root cause hypothesis

The Audit Log table likely does not apply overflow constraints to the `details` cell or its inner content.

Possible contributing causes:

- the column does not have a width constraint or max width
- the cell content does not use `break-words`, `break-all`, `overflow-hidden`, or similar containment styles
- the table layout allows content-driven expansion instead of enforcing a stable column layout
- the `details` renderer uses standard body typography instead of a monospace font class

A likely implementation area is `code/frontend/src/pages/system/AuditLogPage.tsx`.

## Suggested fix

1. Constrain the `details` column width so large payloads cannot expand the table beyond its container.
2. Apply safe overflow handling for long content, such as wrapping or a scrollable inner container depending on the desired UX.
3. Render the `details` value with a monospace font for better readability.
4. Verify the result with both compact and very large log payloads.
5. Confirm the table remains usable on smaller desktop widths as well.

## Notes

- This is both a layout bug and a readability issue.
- The best UX may be a constrained cell with wrapping plus monospace styling, rather than allowing unconstrained inline text.
- If some payloads are exceptionally large, a future enhancement could introduce expandable details or a tooltip/modal view, but the immediate bug is that the content must stay inside the table.