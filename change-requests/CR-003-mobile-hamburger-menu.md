---
title: "Add hamburger menu for mobile/responsive navigation"
status: applied
author: roberto
created-at: 2026-03-16T23:00:00Z
---

## Problem

On mobile and tablet viewports, the sidebar navigation is hidden (`hidden lg:block`) and there is no way to access it. Users on small screens cannot navigate to any section of the app — they are stuck on whatever page they landed on.

## Solution

Add a hamburger menu button to the top navigation bar that is only visible on small screens (`lg:hidden`). Tapping it opens a slide-over drawer containing the full sidebar navigation. The drawer should:

1. **Show a hamburger icon** (three horizontal lines) on the left side of the header, visible only on screens smaller than `lg` breakpoint.
2. **Open a slide-over drawer** from the left side when tapped, overlaying the page content with a semi-transparent backdrop.
3. **Contain the full sidebar navigation** — same links as the desktop sidebar (Dashboard, Settings, Audit Log, and project-level links when inside a project).
4. **Close when**:
   - The user taps the backdrop
   - The user taps the close (X) button
   - The user navigates to a new page (clicks a link)
5. **Include the tenant switcher** at the top of the drawer (since it's also hidden on small screens).

### Implementation steps

1. Add a `mobileMenuOpen` state to `Layout.tsx`.
2. Add a hamburger button to the header, visible only below `lg` breakpoint (`lg:hidden`).
3. Render a drawer/overlay panel that slides in from the left, containing:
   - Close button
   - Tenant switcher
   - All sidebar nav links (same as desktop sidebar)
4. Close the drawer on route change (use `useEffect` watching `location.pathname`).
5. Add proper `dark:` classes to the drawer for dark mode support.

## Affected files

### Modified files
- `code/frontend/src/components/Layout.tsx` — Add hamburger button, mobile drawer with sidebar navigation
