---
title: "Installable PWA"
status: synced
author: "user"
last-modified: "2026-09-05T14:20:00.000Z"
version: "1.0"
---

# Installable PWA

## Overview

SDD Flow is installable as a Progressive Web App from supported desktop browsers. Users can install it from the browser UI and launch it from the operating-system app launcher, dock, taskbar, or desktop shortcut in a focused standalone window.

The PWA uses the same hosted frontend, backend APIs, authentication cookies, tenant/project routes, theme setting, and language setting as the normal browser experience. It does not require Electron, Tauri, native installers, or app-store distribution.

## Desktop installability

The frontend exposes a complete web app manifest with:

- stable app identity (`id`, `name`, `short_name`, and `description`);
- `start_url` and `scope` rooted at the frontend app;
- `display: standalone` for installed windows;
- SDD Flow theme and background colours;
- PNG launcher icons for normal and maskable icon surfaces.

Supported desktop browsers that implement PWA installation, especially Chromium-based browsers, should offer SDD Flow as installable when the app is served over HTTPS or localhost.

## App identity and icons

The SDD Flow favicon remains available for browser tabs. The installable app uses dedicated PNG assets under the frontend public icon folder:

- Apple touch icon, 180x180;
- rounded 192x192 and 512x512 icons for normal launcher surfaces;
- maskable 192x192 and 512x512 icons with safe padding for adaptive launchers.

Icon assets are generated from the SDD Flow brand mark and validated by automated checks so the manifest never references missing or incorrectly sized icon files.

## Service worker and application shell

Production builds register a service worker that precaches the static Vite build assets and the application shell. Frontend route navigations fall back to `index.html`, so installed-mode launches and deep-link refreshes continue to work for tenant, project, document, CR, bug, worker, profile, and admin routes.

The service worker is a production feature. Local development must document how to avoid stale service-worker caches and how to unregister an old worker during debugging.

## Offline limitations

SDD Flow is not offline-first. It is a collaborative, authenticated, server-backed workspace, so server data and mutations require network connectivity.

The service worker must not serve stale protected backend data. API, authentication, websocket, worker, and notification traffic remain network-only or network-first without stale-cache fallback. When connectivity is unavailable, users see a clear offline indication and network-dependent operations fail visibly instead of being reported as successful.

## Updates

Installed users may keep SDD Flow open for long sessions. When a new frontend version is available, the app detects the waiting service worker and shows an accessible update notification. The user chooses when to reload so active edits in documents, CRs, bugs, comments, and forms are not lost unexpectedly.

## Localization and theme

PWA install, offline, and update messages are translated in English and Italian. Theme and language preferences remain independent local browser settings and continue to work in browser and installed modes.

The manifest colours provide safe install-surface defaults. Runtime theme-colour metadata remains coherent with the current light/dark theme bootstrap.

## User guidance

Users install SDD Flow through their browser's standard install action, such as "Install app" or "Create shortcut". Availability and wording depend on the browser and operating system. If the browser does not expose a programmable install prompt, the application relies on browser-native install affordances rather than showing misleading repeated prompts.
