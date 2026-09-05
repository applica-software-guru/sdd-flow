---
title: "Frontend design system, reuse, accessibility and quality gates"
status: applied
author: "user"
created-at: "2026-09-04T20:20:00.000Z"
revision: "2"
---

# CR-037: Frontend Design System, Reuse, Accessibility and Quality Gates

## Summary

Refactor `code/frontend/` incrementally to adopt shadcn/ui correctly, remove repeated UI and domain flows, strengthen type safety and accessibility, split oversized modules, and enforce lint, formatting, type checking, tests and production builds locally and in CI.

The refactor must preserve routes, API contracts, dark mode, responsive behaviour and existing product functionality. It is a structural and visual-consistency change, not a redesign of business workflows.

## Audit baseline

The audit covered all source and configuration files under `code/frontend/` and compared the setup with `../../applica/calzedonia-takt/code/frontend/`.

Current verification is green:

- `npm run lint`: passes;
- `npm run build`: passes;
- `npm test`: 7 files and 44 tests pass;
- TypeScript already uses `strict`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch` and `forceConsistentCasingInFileNames`.

The production build nevertheless reports an oversized main bundle: approximately **2.27 MB minified / 659 kB gzip**. The source contains approximately 11,640 lines, 77 native buttons, 39 native inputs, 13 native selects, 7 native tables and 106 inline SVG elements.

## Findings

### 1. shadcn/ui is not currently installed or used

The current frontend uses React and handwritten Tailwind markup. It has none of the standard shadcn/ui integration points:

- no `components.json`;
- no `src/components/ui/` primitives;
- no `src/lib/utils.ts` with `cn()`;
- no `class-variance-authority`, `clsx`, `tailwind-merge`, Radix UI or Lucide dependencies;
- no shadcn CSS-variable design tokens;
- no imports from `@/components/ui/*`.

Therefore this is not an incorrect use of shadcn: **shadcn is not being used at all**. The current visual style imitates a component library by repeating Tailwind class strings directly in pages.

The calzedonia-takt frontend has the expected code-owned shadcn structure: `components.json`, `components/ui/*`, `cn()`, Radix primitives, CVA, `tailwind-merge` and Lucide. That is the model to adopt. shadcn must remain code owned; do not add a runtime `shadcn` UI package or wrap every primitive without a concrete product-level reason.

### 2. Repeated presentation and state patterns

The audit found high repetition, including:

- the same field label class 46 times;
- the same standard input class 12 times, with several near-identical variants;
- the same primary button class 11 times plus additional near-identical variants;
- repeated card, table heading, empty-result and spinner markup;
- duplicated native modal overlays without a common accessible dialog primitive;
- three custom click-outside dropdown/menu implementations;
- repeated inline icons instead of a shared icon library;
- inconsistent direct date formatting despite the presence of `lib/format.ts`.

The Bugs and Change Requests create, list and detail pages are structurally very similar. They duplicate slug handling, form layout, loading/error states, tables, comments, transitions, assignment bands, edit forms and worker actions. Their React Query hooks also duplicate query-key construction, invalidation and CRUD mutation boilerplate.

### 3. Structure and maintainability issues

- `components/Layout.tsx` is 636 lines and contains persistence, authorization derivation, desktop navigation, mobile navigation, top bar, breadcrumbs and user-menu behaviour.
- `pages/system/ProfilePage.tsx` is 442 lines; project/tenant dashboards and settings pages are also large.
- `types/index.ts` is a 289-line cross-domain type bucket.
- `App.tsx` eagerly imports every route.
- Most imports ignore the configured `@/*` alias and use deep relative paths.
- There are 71 non-null assertions on route identifiers; route parameter validation is implicit and spread across pages.
- API responses are often accepted as untyped Axios data and cast with `as Model`, so compile-time types do not validate runtime payloads.
- Query keys are repeated as raw arrays, which makes cache invalidation fragile.
- `getApiErrorMessage` lives in `useTenants.ts` but is used by unrelated authentication pages.
- Build/test configuration duplicates alias configuration.
- Generated local cache/report directories exist in the working tree and should be covered consistently by ignore rules, even though they are not tracked.

### 4. Accessibility gaps

Handwritten dialogs and menus do not consistently provide the behaviour supplied by Radix/shadcn primitives:

- focus trapping and focus restoration;
- Escape-to-close;
- dialog title/description associations;
- keyboard navigation for menus/selects;
- robust outside-interaction handling;
- explicit accessible labels for icon-only controls.

Clickable backdrop `div` elements and visual popovers are not substitutes for dialog/menu semantics. Tables also need a shared responsive overflow strategy, and loading indicators need a consistent accessible label or status treatment.

### 5. Quality tooling is only partially enforced

The frontend has a useful ESLint configuration and strict TypeScript options, but:

- no explicit `typecheck` script exists; type checking only happens as part of `build`;
- no formatter or `format:check` command exists;
- ESLint is not type-aware and has no JSX accessibility rules;
- CI runs Vitest only, not lint, type checking, formatting checks or a production build;
- the frontend has no command equivalent to the backend `cli.sh check` workflow;
- the calzedonia-takt frontend itself demonstrates shadcn and split TS configs, but its frontend does not currently provide a formatter. Formatting should therefore follow the stronger backend-style command UX while using TypeScript-native tools.

## Target design

### A. shadcn/ui foundation

Add the standard shadcn integration:

1. Add `components.json` configured for Vite/React, TypeScript, the existing `@/*` alias, CSS variables and Lucide.
2. Add `src/lib/utils.ts` with `cn()` implemented through `clsx` and `tailwind-merge`.
3. Add the required dependencies: Radix primitives selected by generated components, `class-variance-authority`, `clsx`, `tailwind-merge` and `lucide-react`.
4. Introduce semantic CSS variables for background, foreground, card, popover, primary, secondary, muted, accent, destructive, border, input and ring. Preserve the existing slate/blue visual identity and class-based dark mode.
5. Generate only primitives that are actually used. The initial set is:
   - `Button`, `Input`, `Textarea`, `Label`;
   - `Select`;
   - `Dialog` and `AlertDialog`;
   - `DropdownMenu`;
   - `Card`, `Badge`, `Alert`, `Table`;
   - `Skeleton` or a shared `Spinner`/loading primitive, based on the final loading UX.
6. Replace inline SVGs with Lucide where an equivalent icon exists. Keep bespoke brand artwork, diagrams and the Google mark local.

Files under `components/ui/` are the project-owned primitives. Product components compose them; they must not duplicate their base styling or hide useful primitive props.

### B. Reusable product components

Create a clear distinction between low-level UI and product components:

```text
src/
├── components/
│   ├── ui/                 # shadcn-owned primitives
│   ├── layout/             # AppShell, Sidebar, MobileNav, TopBar, Breadcrumbs
│   └── shared/             # PageHeader, BackLink, LoadingState, ErrorState,
│                           # EmptyState, DataTable shell, Pagination,
│                           # FormField, CommentsSection, TransitionControls
├── features/
│   ├── bugs/
│   ├── change-requests/
│   ├── projects/
│   ├── tenants/
│   └── workers/
├── hooks/                  # reusable React hooks and query adapters
├── api/                    # typed transport functions and query-key factories
├── lib/                    # pure cross-cutting utilities
└── types/                  # domain-specific type modules
```

This migration is incremental; existing route files may remain under `pages/`, but they should become thin route composition modules.

Required reuse work:

- extract `PageHeader`, `BackLink`, `LoadingState`, `ErrorState`, `FormField`, responsive table shell and standard action rows;
- create a shared `CommentsSection` used by Bugs and CRs;
- create shared transition and assignment sections;
- represent Bugs/CR differences through typed configuration and small domain-specific components rather than copying whole pages;
- share slug auto-generation in a `useEditableSlug` hook and a pure `slugify` utility;
- centralize date/date-time formatters;
- keep `StatusBadge`, `SeverityBadge`, worker badges and user presentation as product components composed from shadcn `Badge`/other primitives;
- avoid speculative generic abstractions: extract only stable repeated behaviour, and retain domain-specific validation and actions in each feature.

### C. App shell and routing

Split `Layout.tsx` into focused components and hooks:

- `AppShell`;
- `Sidebar` and a data-driven navigation configuration shared with `MobileNav`;
- `TopBar`;
- `ProjectBreadcrumbs`;
- `UserMenu`;
- a tested last-tenant persistence hook.

Desktop and mobile navigation must consume the same navigation model so labels, permissions, paths and icons cannot drift. Do not update React state during render; persistence and external-storage synchronization must use a dedicated hook with explicit semantics.

Convert route modules in `App.tsx` to `React.lazy`/dynamic imports with route-level suspense. Lazy-load heavy editors, syntax highlighting and Mermaid rendering so they are not part of the initial authenticated shell bundle. Loading fallbacks must use the shared loading component and must not introduce layout jumps.

### D. Typed data layer and React Query conventions

Components must continue to access server state only through hooks. Internally, split transport concerns from React Query concerns:

- `src/api/client.ts`: Axios instance, typed refresh interceptor and shared API error normalization;
- domain API modules with typed request/response functions;
- `src/api/queryKeys.ts`: hierarchical query-key factories for tenant, project, CR, bug, document, worker, notification and audit resources;
- hooks compose domain API functions with React Query and own user-facing mutation effects.

Remove raw query-key arrays from hooks and use factories for both queries and invalidations. Type Axios calls at their source rather than casting returned `data`. Move generic error parsing out of `useTenants.ts`. Split `types/index.ts` by domain and expose deliberate barrel exports only where useful.

Add a route-parameter helper or typed feature route context that validates required tenant/project/entity IDs once. Remove unjustified non-null assertions from route pages and render a not-found/error state when required context is absent.

Runtime schema validation is recommended at external boundaries with Zod, starting with authentication and mutation responses; it may be introduced incrementally and must not duplicate TypeScript declarations manually.

### E. Forms

For simple filter controls, controlled React state remains sufficient. For create/edit/auth/profile forms, adopt `react-hook-form` with Zod schemas when the form has cross-field validation, repeated validation logic or server errors. Do not migrate trivial one-field controls solely for uniformity.

Forms must provide:

- associated labels and descriptions;
- field-level validation messages;
- a shared API error presentation;
- disabled and pending semantics;
- consistent submit-button loading treatment;
- focus on the first invalid field.

### F. Toolchain and developer workflow

Add the following package scripts:

```json
{
  "lint": "eslint . --max-warnings 0",
  "lint:fix": "eslint . --fix",
  "typecheck": "tsc --noEmit",
  "format": "prettier --write .",
  "format:check": "prettier --check .",
  "test": "vitest run",
  "build": "tsc --noEmit && vite build",
  "check": "npm run lint && npm run typecheck && npm run format:check && npm run test && npm run build"
}
```

Add Prettier and `prettier-plugin-tailwindcss`, with a checked-in configuration and ignore file. Formatting owns layout/whitespace; ESLint owns correctness. The Tailwind plugin must normalize class order, including classes passed through `cn()`/CVA where supported.

Upgrade ESLint configuration to:

- use the current flat config;
- apply type-aware TypeScript rules to source code;
- retain React Hooks and Vite Fast Refresh rules;
- add JSX accessibility checks;
- reject floating promises and unsafe type escapes where practical;
- use targeted overrides for tests and configuration files rather than global disables.

Split TypeScript configuration into `tsconfig.app.json` and `tsconfig.node.json`, referenced by `tsconfig.json`, so Vite/Vitest/Playwright configuration is also type checked with Node types. Keep strict mode and existing no-unused/no-fallthrough checks.

Add a frontend `cli.sh` or equivalent documented command wrapper, aligned with the backend command vocabulary: `install`, `start`, `test`, `lint`, `format`, `typecheck`, `check`, `build`, `help`. It must delegate to package scripts rather than duplicate their logic and work from any current directory.

Update `.github/workflows/ci.yml` so the frontend job runs `npm ci` followed by `npm run check`. The deployment workflow may keep its build step, but CI must catch lint, type, formatting, unit-test and production-build failures before deployment.

### G. Testing and accessibility verification

Add Testing Library, `user-event`, jsdom and an automated accessibility matcher such as `vitest-axe`. Preserve existing tests and add behavioural coverage for:

- dialogs: focus trap/restoration, Escape and confirm/cancel;
- dropdown and mobile navigation keyboard operation;
- shared form validation and server errors;
- Bugs/CR shared create, list, comments and transition components;
- required route-parameter handling;
- query-key factories and invalidation;
- light/dark token behaviour where meaningful.

Do not unit-test generated shadcn internals. Test project wrappers and user-observable behaviour. Keep Playwright for critical responsive navigation and end-to-end workflows.

### H. Bundle and repository hygiene

- enforce **kebab-case for every application source filename**, including components, hooks, contexts, pages, features, utilities and tests (for example `Layout.tsx` → `layout.tsx`, `BackLink.tsx` → `back-link.tsx`, `useApiKeys.ts` → `use-api-keys.ts`, `AuditLogDetails.test.tsx` → `audit-log-details.test.tsx`);
- retain ecosystem-mandated conventional names only where tooling requires them, such as `package.json`, `tsconfig*.json`, `vite.config.ts`, `index.html`, `Dockerfile` and `README.md`;
- update all imports atomically and add a lint/CI check that rejects newly introduced non-kebab-case source filenames;
- lazy-load routes and heavy Markdown/Mermaid/editor dependencies;
- avoid importing an entire icon or syntax-highlighting catalogue;
- keep the initial route chunk below Vite's 500 kB warning threshold, or document any measured exception with a deliberate split strategy;
- consolidate alias configuration where possible and use `@/*` consistently after migration;
- ignore `.vite/`, coverage, Playwright reports/results, Vitest output and TypeScript build info;
- remove local generated artefacts before final verification;
- add a short frontend README documenting architecture, shadcn component generation and quality commands.

## Implementation plan

### Phase 1 — Quality gates and measurable baseline

1. Record current bundle sizes and run lint, typecheck, unit and E2E smoke tests.
2. Add explicit scripts, Prettier/Tailwind formatting, split TS configs, type-aware ESLint and accessibility linting.
3. Add the frontend command wrapper and update CI to run `npm run check`.
4. Apply formatting as an isolated commit so later functional diffs remain reviewable.

### Phase 2 — shadcn foundation

5. Add `components.json`, `cn()`, semantic tokens and required dependencies.
6. Generate the initial UI primitives and preserve the existing visual identity.
7. Add representative tests for project wrappers around Dialog, DropdownMenu and form controls.

### Phase 3 — Mechanical primitive migration

8. Migrate buttons, fields, cards, badges, alerts, dialogs, dropdowns and tables by component/feature, not with a single unreviewable rewrite.
9. Replace equivalent inline SVGs with Lucide.
10. Verify dark mode, focus states and responsive layouts after every feature migration.

### Phase 4 — Product-level reuse

11. Extract shared page, loading/error, form, comment, transition, assignment and table components.
12. Consolidate Bugs and Change Requests around typed shared building blocks while retaining domain rules.
13. Split `Layout.tsx`, Profile and settings/dashboard modules into focused components.

### Phase 5 — Data/type structure

14. Add typed API modules and query-key factories; migrate hooks domain by domain.
15. Split domain types, centralize API errors and date formatting, and eliminate unjustified route-ID assertions and response casts.
16. Introduce schema-backed forms/boundary validation incrementally.

### Phase 6 — Performance and final verification

17. Rename all application source files to kebab-case, update imports atomically and enforce the convention in the quality gate.
18. Lazy-load routes and heavy editor/renderer dependencies and compare production bundles with the baseline.
19. Run filename validation, formatter check, ESLint, typecheck, unit tests, Playwright and production build.
20. Update architecture, tech-stack and CI documentation; run `sdd validate`, mark synced and commit according to the SDD workflow.

## Documentation changes to apply

When this CR becomes pending and is applied:

- `system/architecture.md`:
  - document the shadcn `ui` layer, shared product layer and feature organization;
  - clarify that components consume API data only through hooks, while typed transport functions live under `api/`;
  - document query-key factories, route lazy-loading, typed route context and the split app shell;
  - document frontend quality commands and accessibility expectations.
- `system/tech-stack.md`:
  - add shadcn/ui (code-owned), Radix UI, Lucide, CVA/`tailwind-merge`, Prettier, Testing Library and the chosen schema/form tools;
  - keep versions consistent with the implemented lockfile rather than upgrading React/Tailwind solely for parity with another project.
- `system/ci-pipeline.md`:
  - replace the frontend Vitest-only step with the complete `npm run check` gate;
  - describe lint, formatting, typecheck, unit-test and production-build requirements.
- `product/features/theme.md`:
  - document semantic CSS variables mapped to the existing light/dark palette and shadcn primitives.

## Out of scope

- React 19, React Router 7 or Tailwind 4 upgrades solely to match calzedonia-takt;
- API or backend contract changes;
- a visual rebrand;
- replacing the Markdown editor unless profiling demonstrates a concrete need;
- forcing react-hook-form/Zod into trivial controls;
- abstracting every page into one universal renderer.

## Acceptance criteria

1. `components.json`, `src/components/ui/` and `src/lib/utils.ts` exist and conform to shadcn's Vite conventions.
2. Shared interactive controls use shadcn/Radix primitives; no new handwritten modal, select or dropdown implementation is introduced.
3. Existing dark mode and responsive behaviour remain functional, with semantic design tokens replacing repeated raw surface/control colours.
4. Bugs and Change Requests share create/detail/list building blocks for slug handling, comments, transitions, loading/error states and common table presentation; domain differences remain typed and explicit.
5. `Layout.tsx` is split into focused app-shell components with one shared desktop/mobile navigation model.
6. Query keys are produced by typed factories; API calls are typed at the transport boundary; generic API errors no longer live in a domain hook.
7. Required route parameters are validated without pervasive non-null assertions.
8. `npm run lint`, `npm run typecheck`, `npm run format:check`, `npm test`, `npm run build` and the composed `npm run check` all pass with zero warnings/errors.
9. CI runs the complete frontend check, not Vitest alone.
10. Automated interaction/accessibility tests cover project dialogs, menus, forms and responsive navigation; existing unit and Playwright workflows remain green.
11. The initial application chunk is below 500 kB minified, or an explicit measured exception is documented and approved; heavy editor/Mermaid code is not loaded on routes that do not need it.
12. Every application source file uses kebab-case; tooling-mandated configuration/document names are the only documented exceptions, and CI rejects regressions.
13. Generated caches/reports are ignored and absent from tracked files.
14. `system/architecture.md`, `system/tech-stack.md`, `system/ci-pipeline.md` and `product/features/theme.md` reflect the implemented design, and `sdd validate` passes.
