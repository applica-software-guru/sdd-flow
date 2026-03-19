---
title: "Improve project-context clarity in project navigation"
status: applied
author: roberto
created-at: 2026-03-19T00:00:00Z
---

# CR-013: Improve project-context clarity in project navigation

## Summary

Users often lose context after opening project-level navigation because the UI does not clearly communicate which project is currently active. This CR introduces a persistent and explicit "current project" indicator across project pages and menus.

## Problem

When a user clicks a project and the project submenu appears, the active project context is visually weak and easy to miss. This creates recurring confusion:

1. Users are not sure which project they are currently browsing.
2. Users can mistakenly perform actions (create CRs, bugs, docs) in the wrong project.
3. Navigation confidence drops, especially when switching quickly between projects.

## Solution

Introduce a clear, redundant project-context system combining location, hierarchy, and active-state cues.

### UX changes

1. **Persistent project context bar**
   - Show a compact bar at the top of all project-scoped pages.
   - Content: `Project: <project_name>` and project slug.
   - Include quick action: "Switch project".

2. **Strong active project styling in sidebar**
   - In the project list, the active project row gets a distinct background, left accent border, and bold label.
   - Keep this style visible both when submenu is expanded and collapsed.

3. **Project breadcrumb in content header**
   - Add breadcrumb pattern: `Projects / <project_name> / <section>`.
   - Clicking `Projects` returns to project list.

4. **Project-aware submenu heading**
   - Project submenu starts with a heading like `Inside <project_name>`.
   - All submenu links remain grouped under this heading.

5. **Route guard for stale context**
   - If URL project id/slug does not match loaded context, show a small warning state and auto-sync to the route project.

### Interaction details

1. Switching project updates all context surfaces immediately (sidebar highlight, context bar, breadcrumb, submenu heading).
2. On mobile drawer navigation, the active project indicator is shown at the top of the drawer as well.
3. Keyboard focus order includes the context bar and switch action for accessibility.

## Acceptance criteria

1. From any project page, users can identify the active project in less than 1 second via at least two independent UI cues.
2. Active project is always visible in sidebar and header context bar on desktop.
3. Active project is visible inside the mobile navigation drawer.
4. Breadcrumb always reflects the correct project and section.
5. Switching project updates context indicators without requiring full page refresh.
6. No regressions in existing navigation tests; add coverage for active project visibility and project switching.

## Affected files (expected)

### Frontend
- `code/frontend/src/components/Layout.tsx`
- `code/frontend/src/components/Sidebar.tsx` (or equivalent navigation component)
- `code/frontend/src/pages/projects/*` (project-scoped header/breadcrumb integration)
- `code/frontend/src/styles/*` (active-state + context bar styles)
- `code/frontend/e2e/navigation.spec.ts`
- `code/frontend/e2e/responsive.spec.ts`

## Notes

This CR is focused on navigation clarity and context awareness. It does not change project permissions, project data model, or routing structure beyond context synchronization behavior.