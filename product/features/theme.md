---
title: "Theme — Light / Dark Mode"
status: synced
author: "roberto"
last-modified: "2026-03-16T22:30:00.000Z"
version: "1.0"
---

# Theme — Light / Dark Mode

## Overview

The application supports light and dark color schemes with automatic OS preference detection and a manual toggle.

## Features

### System Preference Detection

- On first visit, detect the user's OS color scheme using `window.matchMedia('(prefers-color-scheme: dark)')`
- Default to the detected preference
- Listen for real-time OS preference changes (e.g., macOS auto dark mode at sunset) and update automatically when in "System" mode

### Three-Way Toggle

- A dropdown button in the top navigation bar (between the search button and notification bell)
- Three options:
  - **Light** — sun icon, forces light theme
  - **Dark** — moon icon, forces dark theme
  - **System** — monitor icon, follows OS preference
- Default selection: System

### Persistence

- Store the user's choice in `localStorage` (key: `theme`)
- Persists across page reloads and new sessions
- Falls back to `'system'` if no stored preference

### Theme Application

- Toggle a `dark` class on the `<html>` element
- Use Tailwind CSS dark mode with `darkMode: 'class'` strategy
- All UI surfaces must support both themes:
  - Backgrounds (page, cards, sidebar, modals)
  - Text colors (headings, body, muted)
  - Borders and dividers
  - Form inputs, selects, textareas
  - Buttons (primary, secondary, danger)
  - Badges (status, severity)
  - Markdown editor and renderer
  - Notification bell dropdown
  - Search modal

## Implementation

### ThemeProvider Context

- File: `src/context/ThemeContext.tsx`
- Provides `theme` (`'light' | 'dark' | 'system'`), `resolvedTheme` (`'light' | 'dark'`), and `setTheme()`
- Reads initial theme from `localStorage`, falling back to `'system'`
- Adds/removes the `dark` class on `document.documentElement`
- Subscribes to `matchMedia` change events for real-time OS preference updates
- Wrap the app with `ThemeProvider` in `main.tsx`

### ThemeToggle Component

- File: `src/components/ThemeToggle.tsx`
- Dropdown with three options: Light (sun icon), Dark (moon icon), System (monitor icon)
- Placed in the `Layout.tsx` header bar

### Tailwind Configuration

- Set `darkMode: 'class'` in `tailwind.config.js`
- Add `dark:` variant classes to all components and pages

### Markdown Editor Integration

- Configure `@uiw/react-md-editor` to respect the current theme via its `data-color-mode` prop using `resolvedTheme`
