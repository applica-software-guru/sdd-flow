---
title: "Add light/dark mode with system preference detection and manual toggle"
status: applied
author: roberto
created-at: 2026-03-16T22:30:00Z
---

## Problem

The application currently only supports a light color scheme. Users working in low-light environments or who prefer dark interfaces have no way to switch themes. Modern desktop operating systems expose a preferred color scheme setting (`prefers-color-scheme`), but the app does not respect it.

## Solution

Implement a theme system that:

1. **Detects the user's OS preference** on first visit using `window.matchMedia('(prefers-color-scheme: dark)')` and defaults to that.
2. **Provides a toggle button** in the top navigation bar (next to the notification bell) allowing users to switch between Light, Dark, and System (auto) modes.
3. **Persists the choice** in `localStorage` so it survives page reloads and new sessions.
4. **Applies the theme** by toggling a `dark` class on the `<html>` element, leveraging Tailwind CSS's built-in dark mode support (`darkMode: 'class'`).
5. **Themes all UI surfaces** including:
   - Backgrounds (page, cards, sidebar, modals)
   - Text colors (headings, body, muted)
   - Borders and dividers
   - Form inputs, selects, textareas
   - Buttons (primary, secondary, danger)
   - Badges (status, severity)
   - Markdown editor and renderer
   - Notification bell dropdown
   - Search modal
6. **Listens for OS preference changes** in real-time (e.g., macOS auto dark mode at sunset) and updates automatically when the user is in "System" mode.

### Implementation steps

1. Update `tailwind.config.js` — set `darkMode: 'class'`.
2. Create a `ThemeProvider` context (`src/context/ThemeContext.tsx`) that:
   - Reads initial theme from `localStorage` (key: `theme`), falling back to `'system'`.
   - Exposes `theme` (`'light' | 'dark' | 'system'`), `resolvedTheme` (`'light' | 'dark'`), and `setTheme()`.
   - Adds/removes the `dark` class on `document.documentElement`.
   - Subscribes to `matchMedia` change events for real-time system preference updates.
3. Create a `ThemeToggle` component (`src/components/ThemeToggle.tsx`) with a dropdown offering three options: Light (sun icon), Dark (moon icon), System (monitor icon).
4. Add `ThemeToggle` to the `Layout.tsx` header bar, between the search button and notification bell.
5. Add `dark:` variant classes to all components and pages for dark mode styling.
6. Configure the markdown editor (`@uiw/react-md-editor`) to respect the current theme via its `data-color-mode` prop.

## Affected files

### New files
- `code/frontend/src/context/ThemeContext.tsx` — Theme provider with system detection
- `code/frontend/src/components/ThemeToggle.tsx` — Three-way toggle (Light / Dark / System)

### Modified files
- `code/frontend/tailwind.config.js` — Add `darkMode: 'class'`
- `code/frontend/src/main.tsx` — Wrap app with `ThemeProvider`
- `code/frontend/src/components/Layout.tsx` — Add `ThemeToggle` to header
- `code/frontend/src/components/MarkdownEditor.tsx` — Use `resolvedTheme` for `data-color-mode`
- `code/frontend/src/components/StatusBadge.tsx` — Add `dark:` classes
- `code/frontend/src/components/SeverityBadge.tsx` — Add `dark:` classes
- `code/frontend/src/components/ConfirmDialog.tsx` — Add `dark:` classes
- `code/frontend/src/components/SearchModal.tsx` — Add `dark:` classes
- `code/frontend/src/components/NotificationBell.tsx` — Add `dark:` classes
- `code/frontend/src/index.css` — Add dark mode base styles and transitions
- `code/frontend/src/pages/*.tsx` — Add `dark:` variant classes to all pages
