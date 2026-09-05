---
title: "Public Landing Page"
status: synced
author: ""
last-modified: "2026-09-05T09:35:00.000Z"
version: "1.2"
---

# Public Landing Page

## Overview

The public landing page presents SDD Flow accurately to anonymous and authenticated visitors. It uses the same semantic visual language as the application while keeping all product previews static, deterministic, and independent from tenant data.

## Access and Session-Aware Actions

- `/` remains public for anonymous and authenticated visitors
- Anonymous visitors see Log in, Sign Up, and Get Started Free actions
- Authenticated visitors see Open app in the navbar and Go to dashboard in primary CTA locations; both lead to `/tenants`
- Session resolution reserves CTA dimensions and causes no redirect or significant layout shift
- Prominent lower-page and footer actions must not contradict the active session

## Product Presentation

- The hero shows the tenant dashboard users reach through Open app: tenant context, tenant navigation, KPI cards, a strong KPI-to-projects divider, compact project search/sort controls, project list, and project creation action
- A separate preview shows the project overview that appears only after selecting a project, including project navigation, summary metrics, recent Change Requests, and recent Bugs
- Primary visual examples cover the tenant dashboard, selected-project overview, shared work-item collaboration, and remote workers
- Documentation and audit-log behavior may appear as compact supporting examples
- Preview content uses current labels, statuses, severity, metadata, comment counts, assignment behavior, and expandable audit details
- The tenant-dashboard preview must stay aligned with the implemented tenant dashboard layout: header, KPI cards, divider, then projects. It must not show removed first-version panels such as projects-needing-attention, recent-activity details, or worker sidebars.
- Marketing copy must not claim functionality that is absent from the current product

## Design System

- Standard surfaces, text, borders, and controls use semantic theme tokens
- Landing controls compose the code-owned shadcn primitives where applicable
- Lucide provides standard interface icons; custom SVG is reserved for intentional branded illustration
- Repeated containers, section headings, CTAs, feature cards, and product-preview frames use reusable landing composition components
- Preview fixture data is typed and centralized rather than embedded throughout large render functions
- Branded gradients and feature accents may supplement, but not replace, semantic application surfaces

## Preview Architecture

- Product previews are static presentation components and never execute API hooks
- Previews reuse low-level visual primitives but do not mount routed pages or the authenticated application layout
- Preview dimensions may be simplified for marketing legibility while preserving current information hierarchy and the distinction between tenant-level and project-level navigation
- Fixture content remains deterministic and avoids timestamps or labels that become visibly stale

## Accessibility and Responsive Behavior

- Heading hierarchy and page landmarks remain valid
- Interactive controls support keyboard navigation and visible focus states
- Decorative preview regions are hidden from assistive technology when their content would be redundant
- Previews adapt intentionally at 320px, 375px, tablet, and desktop widths without document overflow or unreadably scaled text
- Light and dark modes use opaque, readable surfaces
- Entrance effects respect `prefers-reduced-motion`

## Quality and Performance

- Semantic Playwright checks cover anonymous/authenticated CTAs, preview structure, dark mode, and responsive overflow
- The full frontend quality gate and Playwright suite must pass
- The landing route remains lazy-loaded and should not regress materially from the recorded baseline of approximately 37.4 kB minified / 8.9 kB gzip without a documented reason

## Agent Notes

- Keep previews compact; do not create a second implementation of authenticated pages
- Update preview contracts whenever a frontend visual change materially changes the concepts promoted on the landing page
- Do not add live tenant/project data, a CMS, page builder, screenshot service, or animation framework for this feature
