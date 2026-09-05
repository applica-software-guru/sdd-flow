---
title: "Localization — Italian and English"
status: synced
author: "user"
last-modified: "2026-09-05T14:20:00.000Z"
version: "1.1"
---

# Localization — Italian and English

## Overview

The complete SDD Flow frontend is available in English (`en`) and Italian (`it`). English is the default and fallback language. Locale variants are normalized to a supported base language; unsupported languages fall back to English.

## Detection and persistence

The initial language is selected in this order:

1. the supported language stored in `localStorage` under `sdd-flow-language`;
2. the browser language;
3. English.

A manual change applies without a reload and persists in the same browser across reloads, navigation, login, and logout. Language preference is browser-local and is not stored in the user profile or synchronized between devices.

## Language selector

One shared, accessible language selector is available:

- in the public landing header;
- on authentication-related pages;
- in authenticated desktop and mobile app navigation, beside the theme control.

The selector identifies the current language, supports keyboard and focus behavior through the shared UI primitives, and remains usable in light and dark themes and at responsive widths.

## Translated content

All application-owned frontend copy is localized, including:

- public, authentication, tenant, project, documentation, CR, bug, worker, audit, notification, profile, platform-administration, and installable-PWA experiences;
- navigation, breadcrumbs, forms, filters, tables, dialogs, validation, empty/loading/error states, confirmations, toasts, offline notices, install prompts, and update-available notifications;
- status, severity, role, event, and job-state presentation labels;
- accessibility labels, titles, alternative text, and screen-reader-only content;
- locale-sensitive dates, date-times, counts, interpolation, and plural forms.

Brand names, user-generated content, tenant/project names, stored documents, CR/bug/comment bodies, slugs, identifiers, paths, API values, raw server data, and terminal output remain unchanged.

## Catalog quality

English and Italian use matching domain-oriented namespaces and key structures. English is the canonical TypeScript resource shape. Automated validation rejects missing namespaces or keys, incompatible leaf shapes, and mismatched interpolation or plural variables.

Fallback behavior is a safety mechanism, not a substitute for a complete Italian catalog. Both catalogs must remain complete when frontend copy changes.

## Accessibility and layout

Translated visible and accessibility-only copy must be delivered together. Controls retain semantic names, selected states, keyboard behavior, and focus management in either language. Responsive layouts must accommodate longer Italian text without hiding required controls or information.

## Boundaries

Localization is a frontend presentation concern. API payloads, query keys, routes, enum wire values, slugs, identifiers, and persisted domain content are language-neutral. Arbitrary backend prose is not translated through fragile full-string matching; known conditions use localized presentation and unknown conditions use a safe localized fallback.
