---
title: "Landing page design-system refactor and product preview refresh"
status: applied
author: "user"
created-at: "2026-09-05T08:30:00.000Z"
revision: "3"
---

# CR-038: Landing Page Design-System Refactor and Product Preview Refresh

## Summary

Refactor the public landing page so that it uses the frontend design system introduced by CR-037 and presents an accurate visual preview of the current SDD Flow application.

The landing page still uses a mostly independent, handwritten visual language and displays simulated product screens that predate the new app shell, semantic theme tokens, shadcn/Radix primitives, shared work-item components, updated tables, assignment flows, audit-log expansion, and current responsive navigation.

The goal is not to redesign the authenticated product again. The goal is to make the public site a truthful, maintainable presentation of the product that now exists, while reducing the chance that its mockups become stale after every frontend refactor.

## Context

CR-037 changed the authenticated frontend substantially:

- the application shell was split into focused top-bar, sidebar, navigation, breadcrumb, mobile-navigation, and user-menu components;
- semantic CSS tokens became the source of truth for light and dark surfaces;
- code-owned shadcn/Radix primitives replaced handwritten dialogs, menus, selects, buttons, cards, badges, inputs, and tables in shared workflows;
- Bugs and Change Requests now share list, creation, comments, transition, and assignment components;
- audit-log rows expose structured details through inline expansion;
- route loading preserves the themed app shell;
- route-level code splitting reduced the initial application bundle;
- all application source filenames now use kebab-case.

The public landing page was not included deeply enough in that visual refactor. It still contains its own representations of the old application and repeats substantial presentation markup instead of using the new system.

BUG-011 established that `/` remains accessible to both anonymous and authenticated visitors. This CR must preserve that behavior:

- anonymous visitors see Log in, Sign Up, and Get Started Free;
- authenticated visitors see Open app and Go to dashboard;
- resolving the current session must not redirect or replace the landing page.

## Audit of the current landing implementation

The landing implementation currently spans approximately **1,343 lines** under `src/components/landing/`, with **27 handwritten inline SVG elements** and multiple repeated card, heading, CTA, badge, and mock-application patterns.

### 1. Hero product mockup no longer matches the application

`hero-section.tsx` renders a generic browser frame containing:

- an unnamed skeleton-style header rather than the current SDD Flow top bar;
- three generic statistic cards;
- a flat list of hardcoded CR/bug rows;
- statuses and colors that do not use the current shared badge components;
- no tenant switcher, project navigation, breadcrumbs, author metadata, comment counts, or responsive shell.

The current authenticated product has a recognizable shell, but its information hierarchy has two distinct states. **Open app** first leads to the tenant dashboard, where users choose a project. Project navigation, summary metrics, and recent work-item rows appear only after selecting that project. The hero is therefore no longer a reliable preview of the actual entry state.

### 2. Other simulated surfaces are also independent copies

- `for-teams-section.tsx` contains a custom team list with locally defined badge colors.
- `remote-workers-section.tsx` contains a large custom worker/terminal simulation with its own status, card, and icon styles.
- `features-section.tsx` declares feature icons as large inline SVG blocks and stores raw Tailwind color recipes in data.
- `how-it-works-section.tsx` repeats icon containers, step badges, typography, and spacing.
- `footer-section.tsx` repeats primary CTA markup and always uses anonymous-oriented copy even when the navbar and hero are session-aware.

These sections resemble the product conceptually but are not tied to a shared visual contract. Updating an authenticated component does not make its landing preview visibly stale to TypeScript or tests.

### 3. The landing page bypasses the semantic design system

The landing components rely heavily on direct `slate`, `blue`, `indigo`, `green`, and other utility colors for standard surfaces and text. Some marketing accents are legitimate, but ordinary cards, borders, muted surfaces, foreground text, and controls should use semantic tokens such as:

- `bg-background`, `bg-card`, `bg-muted`;
- `text-foreground`, `text-muted-foreground`;
- `border-border`;
- `bg-primary`, `text-primary`, `text-primary-foreground`.

Without this alignment, changes to the product palette do not propagate to the public site and dark-mode behavior must be maintained twice.

### 4. Reusable landing composition is missing

Every section independently defines:

- maximum-width containers;
- vertical section spacing;
- eyebrow labels;
- headings and descriptions;
- feature cards;
- CTA links;
- decorative icon containers;
- preview browser/card frames.

The duplication makes spacing and typography inconsistent and encourages future sections to copy another large block.

### 5. Product accuracy is not tested

Current tests verify that the landing page is accessible in anonymous and authenticated sessions, but do not verify that product previews expose current concepts or that obsolete preview labels disappear. There is no explicit contract for what the hero preview represents.

## Objectives

1. Align the landing page with the semantic design system and shared primitives from CR-037.
2. Replace stale mock product screens with current, recognizable previews.
3. Introduce reusable landing-specific composition components without coupling the public page to API-fetching authenticated pages.
4. Make preview fixture content typed, centralized, and easy to update.
5. Preserve session-aware CTAs, public routing, dark mode, accessibility, responsiveness, and current marketing anchors.
6. Reduce handwritten icon and repeated styling markup.
7. Add tests that make intentional preview changes explicit.

## Proposed target design

### 1. Shared landing composition layer

Create small, presentation-only components under a focused location such as:

```text
src/components/landing/
├── landing-container.tsx
├── landing-section.tsx
├── section-heading.tsx
├── landing-cta.tsx
├── feature-card.tsx
├── preview-frame.tsx
├── previews/
│   ├── dashboard-preview.tsx
│   ├── project-overview-preview.tsx
│   ├── work-item-preview.tsx
│   ├── docs-preview.tsx
│   └── worker-preview.tsx
└── preview-data.ts
```

These are product-level presentation components, not replacements for `components/ui/`. They should compose the existing `Button`, `Card`, `Badge`, table primitives, Lucide icons, `cn()`, and semantic theme tokens.

Do not create wrappers that merely rename one shadcn primitive. A landing component is justified only when it captures recurring marketing layout or a stable preview concept.

### 2. Accurate, maintainable product previews

Replace generic mockups with static previews modeled on the current application:

#### Hero: tenant dashboard entry state

The primary hero preview should represent the screen reached immediately after entering the application:

- SDD Flow top bar and tenant context;
- tenant-level Dashboard, Settings, and Audit Log navigation;
- instruction to choose a project;
- tenant heading and project-management context;
- New project action;
- representative project card.

Project navigation, breadcrumbs, summary metrics, and recent work-item rows must not appear in this entry-state preview.

#### Selected-project overview

A separate preview should represent the screen shown after choosing a project:

- project breadcrumb and heading;
- project-specific Overview, Change Requests, Bugs, Docs, Workers, and Settings navigation;
- Change Request, Bug, Document, and Worker summary cards;
- recent Change Request and Bug rows;
- author, date-only metadata, comment counts, and current status/severity treatment.

Both previews must remain static and deterministic. They must not mount the actual `Layout`, execute API hooks, or require authentication. They should reuse low-level visual primitives and typed fixture data rather than importing complete routed pages.

#### Work-item collaboration preview

At least one section should accurately demonstrate the shared work-item experience introduced by CR-037:

- title and status/severity;
- transition action;
- assignee/author context;
- comments or discussion count;
- optional worker enrichment action where appropriate.

A single representative preview is preferable to separate duplicated Bug and Change Request mockups.

#### Documentation and worker previews

Documentation and remote-worker sections should show current concepts and controls without reproducing entire production pages. Previews should be compact, use the same semantic surfaces, and avoid terminal/status visuals that no longer exist in the product.

#### Audit log, if retained in feature messaging

If the landing page visually promotes audit history, it should reflect the current compact row and expandable structured-detail model rather than a raw JSON/details column.

### 3. Typed fixture data instead of scattered literals

Move preview data into `preview-data.ts` or colocated typed constants:

- use explicit preview-only interfaces;
- keep sample names and statuses neutral and realistic;
- use valid current status/severity values;
- avoid timestamps that appear live or become visibly outdated;
- do not import backend DTOs solely to make a marketing fixture compile if the preview needs only a smaller shape.

Components should map typed fixtures into reusable rows/cards. Large arrays and status-to-class maps should not remain embedded inside section render functions.

### 4. Semantic visual language

Use semantic tokens for standard application surfaces, text, borders, and controls. Branded gradients and deliberate feature accent colors may remain when they serve marketing hierarchy, but they must not redefine generic card/input/button behavior.

Required principles:

- application previews use the same light/dark surface hierarchy as the product;
- shadcn primitives own interaction states and focus treatment;
- status and severity meaning remains consistent with authenticated pages;
- dark mode must not introduce transparent panels, low-contrast borders, or light flashes;
- decorative styling must respect `prefers-reduced-motion`.

### 5. Icon and illustration strategy

Replace handwritten interface icons with Lucide wherever a suitable icon exists. Keep custom SVG only for genuinely branded or explanatory illustrations that Lucide cannot represent.

Decorative icons must use `aria-hidden="true"`; meaningful controls require accessible names. Repeated browser chrome, arrows, checks, folders, bug icons, and dashboard icons should not each carry custom SVG path markup.

### 6. Session-aware CTA consistency

Centralize or consistently compose landing CTAs so BUG-011 behavior applies beyond the navbar and hero:

- authenticated visitors must not see prominent Sign Up/Get Started CTAs later in the page that contradict their session;
- the lower-page CTA should become **Go to dashboard** or equivalent when authenticated;
- anonymous visitors retain registration-oriented messaging;
- loading state reserves CTA dimensions and avoids layout shift;
- the footer may keep passive Log in/Register links only if their authenticated-state behavior is explicitly decided and tested.

Avoid issuing redundant `/auth/me` requests. Multiple consumers may use the same React Query key, but session-aware presentation should have one clear source of truth or a focused shared hook/component contract.

### 7. Responsive preview behavior

The hero and section previews must be designed for narrow screens rather than merely scaled down:

- collapse or hide the preview sidebar intentionally;
- avoid unreadably small text;
- prevent horizontal document overflow;
- preserve meaningful labels at mobile widths;
- keep touch targets at least 44px for interactive controls;
- previews that are decorative should not become keyboard-interactive.

## Implementation plan

1. Capture screenshots or inspect the current authenticated dashboard, work-item detail, docs tree, worker list, and audit log in light and dark mode as the visual source of truth.
2. Inventory landing claims and remove or rewrite claims for functionality that is absent or materially different in the current product.
3. Define typed preview fixtures and a small set of reusable preview components.
4. Introduce shared landing container, section heading, CTA, feature-card, and preview-frame patterns where they remove concrete duplication.
5. Rebuild the hero preview around the tenant dashboard entry state and add a distinct selected-project overview preview.
6. Refresh collaboration, documentation, team, and remote-worker previews to match current product concepts.
7. Migrate generic landing surfaces to semantic tokens and shared UI primitives.
8. Replace suitable inline SVGs with Lucide icons.
9. Make all prominent CTAs session-aware, preserving the routing behavior established by BUG-011.
10. Verify mobile layouts, dark mode, keyboard navigation, reduced motion, and loading-state stability.
11. Add focused component and Playwright coverage for content, CTA variants, preview accessibility, and responsive overflow.
12. Run `npm run check` and the complete Playwright suite.

## Acceptance criteria

### Product fidelity

- The hero preview visibly represents the tenant dashboard users reach before selecting a project.
- A distinct selected-project preview represents the actual project overview and project-specific navigation.
- Previewed work-item, documentation, worker, team, and audit concepts match currently implemented product behavior.
- No preview conflates tenant-level and project-level navigation or uses obsolete labels, layouts, statuses, or controls.
- Marketing copy does not claim unavailable functionality.

### Design-system alignment

- Standard landing surfaces use semantic theme tokens.
- Shared shadcn primitives are used for applicable buttons, cards, badges, and interactive elements.
- Suitable interface icons use Lucide; custom SVGs remain only where documented as intentional illustrations.
- Repeated section layout, heading, CTA, feature-card, and preview-frame patterns are extracted when used in more than one place.
- Preview data is typed and is not scattered through large JSX render functions.

### Session behavior

- `/` remains accessible to authenticated users.
- Anonymous and authenticated CTA variants remain consistent in the navbar, hero, and lower-page CTA.
- Session resolution causes neither redirect nor significant layout shift.
- Login, registration, and Open app/Go to dashboard destinations remain unchanged.

### Accessibility and responsive behavior

- All interactive controls are keyboard accessible with visible focus states.
- Decorative preview content is hidden appropriately from assistive technology when it would otherwise create noise.
- Heading hierarchy and landmark structure remain valid.
- Light and dark modes have readable contrast and opaque surfaces.
- Landing sections and previews do not overflow at 320px, 375px, 768px, or desktop widths.
- Motion respects `prefers-reduced-motion`.

### Quality and performance

- Existing frontend tests remain green.
- New tests cover anonymous/authenticated CTAs and the expected preview structure.
- The complete Playwright suite passes in light and dark mode for the affected landing flows.
- `npm run check` passes.
- The landing route chunk does not regress materially from the current baseline of approximately **37.4 kB minified / 8.9 kB gzip** without an explicit documented reason.
- No backend or API changes are required.

## Out of scope

- Redesigning authenticated workflows or API contracts.
- Adding new product features solely because the landing page mentions them.
- Introducing a CMS, page builder, Storybook, animation framework, or screenshot service.
- Embedding live tenant/project data in the public landing page.
- Replacing the established visual brand or rewriting all marketing copy without separate product approval.
- Changing `/`, `/login`, `/register`, or `/tenants` route semantics established by BUG-011.

## Risks and mitigations

### Preview components become a second product implementation

**Risk:** high-fidelity previews can grow into duplicated application pages.

**Mitigation:** keep them static, compact, presentation-only, and built from typed fixtures plus low-level shared primitives. Do not import API hooks or complete routed pages.

### Product previews become stale again

**Risk:** static previews can still drift after future application changes.

**Mitigation:** document the preview contract, colocate fixture data, test current labels/statuses, and include landing preview review in future frontend visual change requests.

### Excessive abstraction obscures marketing layout

**Risk:** extracting every wrapper can make sections harder to understand.

**Mitigation:** extract only recurring patterns with a stable purpose; keep one-off branded compositions local.

### Bundle growth

**Risk:** importing large authenticated components or broad icon modules can increase the public route chunk.

**Mitigation:** import Lucide icons individually, avoid API-aware application pages, preserve route-level lazy loading, and compare the production chunk against the recorded baseline.

## Decisions confirmed for implementation

1. **Preview scope:** tenant dashboard, selected-project overview, work item, and worker are the primary visuals; docs and audit are compact supporting examples.
2. **Visual fidelity:** previews preserve production information hierarchy, including the boundary between tenant and project contexts, and semantic visual tokens while simplifying dimensions for marketing-page legibility.
3. **Lower-page authenticated CTA:** authenticated visitors see Go to dashboard instead of Get Started Free.
4. **Footer auth links:** authenticated visitors do not see contradictory Log in/Register actions; they receive an Open app entry point instead.
5. **Copy review:** factual corrections are permitted where current copy describes unavailable or materially changed behavior, without changing product positioning.
6. **Visual regression testing:** semantic and responsive Playwright coverage is used; screenshot baselines remain out of scope.
7. **Animation:** subtle entrance animation remains, with `prefers-reduced-motion` fallbacks.
