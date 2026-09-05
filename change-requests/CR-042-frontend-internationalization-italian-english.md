---
title: "Frontend internationalization with Italian and English"
status: applied
author: "user"
created-at: "2026-09-05T12:37:13.000Z"
---

# CR-042: Frontend Internationalization with Italian and English

## Summary

Introduce complete frontend internationalization in `code/frontend/` and make the SDD Flow interface available in:

- English (`en`);
- Italian (`it`).

Adopt `i18next`, `react-i18next`, `i18next-browser-languagedetector`, typed JSON resources grouped by namespace, initialization before React renders, and an immediately accessible language selector.

The migration must cover all user-visible frontend copy, not only navigation and authentication. English remains the fallback language. The selected language is persisted locally and dates, times, status labels, validation feedback, accessibility labels, notifications, errors, dialogs, empty states, and public landing content must follow it.

No backend API or persisted domain-data migration is required.

## User need

As a user, I want to choose Italian or English and use the whole SDD Flow interface consistently in that language, so that I can understand public pages, authentication, tenant and project workflows, documentation, CRs, bugs, workers, audit information, notifications, profile settings, and platform administration without encountering a mixture of languages.

## Current-state audit

The frontend currently has no i18n dependencies or initialization. User-facing strings are embedded directly in components, pages, hooks, and utilities. The audited source contains more than 100 TSX files and hundreds of likely literal-bearing lines, including visible copy and accessibility attributes.

Examples of cross-cutting hard-coded content include:

- desktop, mobile, landing, workspace, and user-menu navigation;
- public landing-page headings, CTAs, previews, and footer copy;
- authentication and invitation flows;
- buttons, field labels, placeholders, table headers, filters, pagination, and empty/loading/error states;
- toast messages and API-error fallbacks;
- status, severity, role, event, and worker-job labels;
- dialog content and destructive-action confirmations;
- `aria-label`, `title`, and screen-reader-only text;
- date and date-time formatting through browser-default locale behavior.

This CR treats internationalization as a complete frontend concern rather than adding a language button over a partially translated application.

## Product decisions

### Supported locales

The first release supports exactly:

| Locale | Display name | Role |
| --- | --- | --- |
| `en` | English | Default and fallback language |
| `it` | Italiano | Fully supported language |

Locale variants are normalized to their base language: for example, `en-US` and `en-GB` resolve to `en`, while `it-IT` resolves to `it`. Any unsupported locale resolves to English.

Adding other languages is out of scope, but the resource organization must allow a new locale to be added without changing feature components.

### Detection and persistence

Resolve the initial language in this order:

1. persisted selection in `localStorage` under a documented key such as `sdd-flow-language`;
2. browser language through `navigator.languages` / `navigator.language`;
3. English fallback.

Use `i18next-browser-languagedetector` rather than custom detection logic. Persist only supported normalized locale values. A manual selection takes effect immediately and survives reloads and later sessions in the same browser.

Language preference remains browser-local in this iteration. It is not added to the user entity and is not synchronized between devices.

### Selector placement and behavior

Create one reusable `language-selector.tsx` component using existing shadcn/Radix primitives and Lucide where appropriate.

The selector must:

- be available on the public landing header and authentication-related pages;
- be available in the authenticated app top bar, adjacent to the theme control;
- remain reachable in responsive/mobile layouts;
- show the active language clearly using `English` / `Italiano` and optionally compact `EN` / `IT` trigger text;
- expose translated accessible names and selected-state semantics;
- support keyboard navigation, focus management, and dark mode;
- change language without navigation or page reload.

Both public and authenticated shells must compose the same selector instead of implementing separate toggles.

### Scope of translated content

Translate all application-owned frontend copy, including:

- landing, privacy, not-found, and authentication pages;
- tenant, project, dashboard, settings, and profile pages;
- documentation tree/viewer/editor actions;
- change-request and bug create/list/detail workflows;
- comments, transitions, assignment, worker jobs, and terminal controls;
- notifications, search, audit log, and platform-admin pages;
- shared UI states, pagination, confirmations, validation messages, and toasts;
- navigation, breadcrumbs, workspace switcher, theme selector, language selector, and user menu;
- user-facing status, severity, role, event-type, and job-state labels;
- `aria-label`, `aria-description`, `title`, image alternative text, and screen-reader-only labels;
- client-owned API error fallbacks and session-expiry messages;
- static text shown in landing-page product previews.

Brand names such as `SDD Flow`, protocol/technology names, user-entered content, document/CR/bug bodies, project and tenant names, paths, slugs, identifiers, terminal output, and raw server data must not be machine-translated.

Known enums and event types must be rendered through translation keys while preserving their raw values in APIs and filtering logic. Unknown backend messages or enum values must have a safe localized fallback and may expose the original value when needed for diagnosis.

## Technical design

### Dependencies and bootstrap

Add compatible versions of:

```text
i18next
react-i18next
i18next-browser-languagedetector
```

Create `src/i18n.ts` and import it from `src/main.tsx` before the React root is rendered. Configure:

- `initReactI18next`;
- browser language detection and local persistence;
- `fallbackLng: "en"`;
- `supportedLngs: ["en", "it"]`;
- locale normalization / non-explicit supported language matching;
- `defaultNS: "common"`;
- `interpolation.escapeValue: false` because React escapes values;
- development diagnostics without noisy production logging.

Changing language must update `document.documentElement.lang` to `en` or `it`. The initial language should be resolved before visible application copy paints, avoiding a flash from one language to another.

### Resource organization

Organize translation resources into domain-oriented namespaces:

```text
src/locales/
├── en/
│   ├── common.json
│   ├── navigation.json
│   ├── auth.json
│   ├── landing.json
│   ├── tenants.json
│   ├── projects.json
│   ├── docs.json
│   ├── change-requests.json
│   ├── bugs.json
│   ├── workers.json
│   ├── notifications.json
│   ├── audit.json
│   ├── admin.json
│   ├── profile.json
│   └── errors.json
└── it/
    └── <the same namespace files>
```

Namespace boundaries may be adjusted during implementation if the final structure remains domain-oriented and avoids one oversized catalog. Both locale trees must have the same namespaces and key structure.

Keys must describe meaning rather than repeat source copy, for example:

```text
common.actions.save
common.states.loading
auth.login.title
bugs.severity.critical
workers.jobs.confirmCancel
errors.sessionExpired
```

Do not use complete English sentences as translation keys. Repeated cross-domain copy belongs in `common`; domain-specific copy stays in its namespace.

### Type safety and catalog consistency

Create `src/i18n.d.ts` using the English resources as the canonical TypeScript resource shape. Translation calls in components must therefore reject unknown namespaces and keys during type checking.

Add an automated catalog-consistency test or validation script that recursively compares English and Italian resources and fails when:

- a namespace exists in only one locale;
- a key is missing from either locale;
- a leaf has an incompatible shape;
- interpolation variables or plural forms differ between languages.

Both catalogs must be complete; relying on English fallback to hide missing Italian copy does not satisfy this CR.

### Component and non-component usage

React components use `useTranslation()` with explicit namespaces. Shared static configuration such as navigation must store translation keys or be built inside a translation-aware hook/component; it must not capture translated values once at module initialization.

Code outside React components may use the configured i18n instance when translation at the presentation boundary is unavoidable, such as client-owned interceptor messages. Domain and API layers should otherwise return typed error/state information and let the UI translate it.

Hooks that emit user-visible notifications may use `useTranslation`, but translation concerns must not leak into query keys, request payloads, persisted entities, or backend contracts.

### Interpolation, plurals, and formatting

Use i18next interpolation and pluralization rather than string concatenation. Dynamic values must remain escaped by React and preserve natural word order in both languages.

Make formatting locale-aware:

- extend the central functions in `src/lib/format.ts` to accept or derive the active supported locale;
- format date-only and date-time values with `Intl.DateTimeFormat` using the active locale;
- use `Intl.NumberFormat` for user-facing counts or numbers where locale formatting matters;
- keep machine values, ISO timestamps, IDs, paths, and API parameters unchanged;
- do not introduce relative-time behavior unless already required by a feature.

Formatting helpers must be deterministic in tests by allowing an explicit locale and options where appropriate.

### Errors and backend boundaries

Do not translate arbitrary backend-provided prose by matching full strings. Prefer stable error codes when already available and map those codes to frontend translation keys. For contracts that expose only a message, retain the existing message behavior with a localized generic fallback.

This CR does not require changing backend responses. If implementation discovers that a critical workflow cannot be localized safely without stable backend error codes, document it and create a separate backend CR rather than expanding this CR silently.

## Implementation plan

### Phase 1 — Inventory and foundation

1. Record a reproducible inventory of user-visible literals under `src/`, including JSX text, placeholders, labels, titles, accessibility attributes, toast/error strings, enum-label maps, and landing preview fixtures.
2. Classify strings by namespace and identify content that must remain untranslated.
3. Add i18next dependencies, initialization, language detection, persistence, HTML `lang` synchronization, and typed resource declarations.
4. Seed structurally identical English and Italian catalogs and add catalog-parity validation before migrating components.
5. Add focused tests for detection, unsupported-language fallback, persistence, language changes, and document-language updates.

### Phase 2 — Shared shell and cross-cutting UI

6. Implement the reusable language selector in public, auth, desktop, and mobile shells.
7. Translate navigation, breadcrumbs, workspace switcher, user menu, theme selector, search, notification shell, pagination, shared loading/error/empty states, dialogs, status/severity badges, and common actions.
8. Make centralized date, date-time, number, role, status, and event-label formatters locale-aware.
9. Translate accessibility-only copy at the same time as visible copy so no inaccessible English-only controls remain.

### Phase 3 — Public and authentication experiences

10. Migrate the landing page and all product-preview fixtures, preserving anchor targets and routes.
11. Migrate login, registration, password recovery/reset, invitation acceptance, privacy, and not-found pages.
12. Verify that the language control is usable before authentication and that selection survives login/logout transitions.

### Phase 4 — Authenticated domains

13. Migrate tenant and project dashboards, lists, create/settings flows, and profile pages.
14. Migrate docs, change requests, bugs, comments, transitions, assignments, and shared work-item features.
15. Migrate workers, audit, notifications, search, and global platform-administration views.
16. Translate hook-generated toasts, confirmation messages, validation feedback, and client-owned API error fallbacks.

### Phase 5 — Quality and completeness

17. Run a second literal audit and allowlist only brand names, technical tokens, test fixtures, and explicitly documented non-translatable content.
18. Add component/integration coverage that renders representative public, auth, tenant/project, work-item, worker, audit, and admin flows in both locales.
19. Verify responsive behavior, keyboard access, focus behavior, dark mode, long Italian labels, interpolation, plurals, and locale-specific formatting.
20. Run `npm run check` and Playwright smoke tests in both languages, then update frontend documentation with the resource and contributor workflow.

Implementation may be split into reviewable commits by phase, but both languages and all in-scope areas must be complete before the SDD documentation is marked synced.

## Testing strategy

### Unit tests

Cover:

- language detection precedence and normalization;
- fallback to English for unsupported locales;
- local persistence and immediate language switching;
- synchronization of `<html lang>`;
- key and interpolation parity between locale catalogs;
- date, date-time, number, plural, enum, and fallback formatting;
- translated labels emitted outside direct JSX where applicable.

### Component and integration tests

Render representative shared and domain components under both locales and assert behavior rather than duplicating the full catalogs in snapshots. Include:

- language selector keyboard and selected-state behavior;
- public/authenticated/mobile placement;
- navigation, forms, validation, dialogs, tables, empty/error/loading states, and toasts;
- long Italian labels without clipping or inaccessible truncation;
- language persistence across remounts.

### End-to-end tests

At minimum, verify in English and Italian:

1. landing page to login/registration;
2. authenticated navigation and workspace selection;
3. one create/list/detail work-item flow;
4. profile/settings and logout;
5. persistence after reload.

Automated tests must not rely on English-only accessible names unless the test intentionally selects the English locale.

## Documentation changes to apply

When this CR is enriched, made pending, and applied:

- create `product/features/localization.md`:
  - document supported languages, fallback, browser detection, manual selection, persistence, selector locations, translated-content scope, and non-translated domain content;
  - document equal catalog completeness and accessibility expectations.
- update `system/architecture.md`:
  - document i18n bootstrap, namespace/resource layout, typed keys, presentation-boundary translation, locale-aware formatting, HTML-language synchronization, and frontend-only persistence;
  - state that API payloads, query keys, slugs, identifiers, and persisted domain content remain language-neutral.
- update `system/tech-stack.md`:
  - add `i18next`, `react-i18next`, and `i18next-browser-languagedetector` with their purposes.
- update `product/features/theme.md` only as needed to document the language selector beside the theme control without coupling theme and language state.

No backend entity or interface documentation change is expected unless a separate CR introduces server-side language preference or stable localized error contracts.

## Out of scope

- languages other than Italian and English;
- automatic or machine translation of user-generated content;
- translating stored documents, CRs, bugs, comments, project names, tenant names, slugs, or terminal output;
- backend-generated emails or server-side templates;
- adding language preference to the user profile or synchronizing it between devices;
- locale-prefixed routes such as `/it/...` and `/en/...`;
- changing API values, enum wire formats, or URL structures;
- server-side rendering or localized SEO metadata;
- redesigning components unrelated to accommodating translated copy.

## Acceptance criteria

1. `i18next`, `react-i18next`, and `i18next-browser-languagedetector` are installed and initialized before React renders.
2. English and Italian are the only supported locales; locale variants normalize correctly and unsupported locales fall back to English.
3. Initial language detection follows persisted choice, browser preference, then English fallback.
4. Manual selection changes all rendered application copy immediately and persists under a documented local-storage key.
5. A single accessible language selector is available on public/auth pages and in authenticated desktop and mobile navigation.
6. The active locale is reflected in `document.documentElement.lang` on startup and after every language change.
7. English and Italian resources use matching domain-oriented namespaces and identical key/interpolation structures.
8. Translation keys are TypeScript-checked using the English catalog as the canonical resource type.
9. Automated validation fails on missing locale files, missing keys, incompatible shapes, or mismatched interpolation/plural variables.
10. All application-owned visible strings in the frontend are translated, including landing, auth, tenants, projects, docs, CRs, bugs, workers, audit, notifications, profile, administration, shared states, dialogs, and toasts.
11. Accessibility copy—including `aria-label`, titles, alternative text, and screen-reader text—is available in both languages.
12. Statuses, severities, roles, event types, and worker states display localized labels without changing raw API values or filtering logic.
13. Dates, date-times, relevant numbers, interpolation, and plurals use the active locale and central formatting helpers.
14. User-generated content, identifiers, paths, slugs, source documents, and raw terminal/server data remain unchanged.
15. Known client/API error conditions have localized presentation; unknown errors retain a safe localized fallback without fragile full-message matching.
16. Language choice survives reload, login, logout, and route changes in the same browser.
17. Responsive layouts remain usable with longer Italian copy; translated labels do not obscure required controls or information.
18. The selector and translated interface preserve keyboard operation, focus behavior, dark mode, and existing accessibility semantics.
19. Unit, component/integration, and Playwright smoke tests cover both locales and the required language lifecycle.
20. A final literal audit contains no unexplained user-facing English literals outside locale resources.
21. `npm run check`, production build, and relevant Playwright suites pass.
22. `product/features/localization.md`, `system/architecture.md`, `system/tech-stack.md`, and any necessary theme-placement documentation describe the implemented behavior, and `sdd validate` passes.

## Risks and mitigations

- **Partial migration and mixed-language screens:** enforce a literal inventory, catalog parity validation, and a final allowlisted audit.
- **Italian copy causing layout regressions:** test representative long labels at mobile and desktop widths; wrap or resize containers rather than shortening meaning arbitrarily.
- **Stale translations in module-level configuration:** store keys or resolve labels during render instead of translating once at import time.
- **Unstable tests tied to English labels:** initialize locale explicitly per test and add locale-aware helpers where appropriate.
- **Translation logic leaking into domain/data code:** keep API values language-neutral and translate only at presentation boundaries.
- **Missing dynamic variables:** compare interpolation/plural signatures automatically between catalogs.

## Open questions for enrichment

1. Should the compact selector trigger show the destination language or the currently selected language with a dropdown? The recommended choice is a dropdown showing the current language because selected state is clearer and future extension remains straightforward.
2. Should privacy-policy legal copy receive a product/legal review after Italian translation? This is recommended even though implementation includes the translation.
3. Should backend emails be localized in a later CR using a persisted user-language preference?
