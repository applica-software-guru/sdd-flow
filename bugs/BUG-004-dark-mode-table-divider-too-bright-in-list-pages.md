---
title: "Dark mode table divider appears too bright on list pages"
status: resolved
author: "roberto"
created-at: "2026-03-18T00:00:00.000Z"
---

## Description

In dark mode, a horizontal divider line in table/list views is visibly too bright and breaks visual consistency.

The issue is clearly visible in Change Requests list view, near the pagination section (line above paginator controls).

## Reproduction

1. Open the app in dark mode.
2. Navigate to Change Requests list page.
3. Scroll to the bottom of the table.
4. Observe the horizontal divider above pagination controls.

## Expected behavior

Dividers and table separators should use dark-theme border tones consistent with the surrounding surface.

## Actual behavior

At least one divider line renders with a light border color in dark mode, making it too bright and visually distracting.

## Root cause hypothesis

The likely root cause is missing dark-mode border classes in shared pagination/table container styles.

In particular, `code/frontend/src/components/Pagination.tsx` uses:

- `border-t border-slate-200`

without a matching dark variant (for example `dark:border-slate-700`), so the top divider remains too bright in dark mode.

## Resolution plan

1. Update shared pagination border styling in `code/frontend/src/components/Pagination.tsx`:
   - add dark border variant to the top divider (`dark:border-slate-700` or design-system equivalent)
2. Review pagination controls in dark mode:
   - button backgrounds, ring/border colors, and hover states (`ring-slate-300`, `bg-white`, `text-slate-900`) to ensure dark-theme parity
3. Verify the fix across all pages reusing `Pagination` (CR list, bug list, and other paginated tables)
4. Add a visual regression check (Playwright screenshot or lightweight style assertion) for dark-mode list pages
5. Confirm no regressions in light mode

## Notes

- The issue appears stylistic and low-risk but impacts perceived polish and readability in dark mode.
- Because `Pagination` is shared, a single fix should improve multiple pages.
