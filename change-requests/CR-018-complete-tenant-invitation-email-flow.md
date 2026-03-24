---
title: "Complete tenant invitation flow with email delivery and token acceptance UX"
status: applied
author: "roberto"
created-at: "2026-03-24T00:00:00.000Z"
---

# CR-018: Complete Tenant Invitation Flow

## Summary

Transform tenant invitations from a partial API-only mechanism into a complete product feature:

1. invite creation from tenant settings
2. email delivery with secure acceptance link
3. frontend acceptance page and route
4. robust validation and user feedback
5. full backend/frontend/e2e test coverage

## Problem

Current invitation flow is incomplete and not production-ready:

1. Frontend and backend endpoint mismatch causes invite failures in UI.
2. No automatic email is sent to invited users.
3. No dedicated frontend route/page to consume invitation token from an email link.
4. Error handling is generic and does not expose actionable details to users.

The required correction is broader than a single fix and should be implemented as a full feature.

## Goals

1. Make tenant invitation usable end-to-end without manual API calls.
2. Deliver invitations by email with a secure tokenized link.
3. Provide a first-class acceptance UX in the web app.
4. Preserve security checks (email ownership, expiry, single-use).
5. Add strong regression coverage.

## Proposed Solution

### Backend

1. Keep invitation domain model (`tenant_invitations`) and token-based acceptance.
2. Confirm/create endpoint contract:
   - `POST /api/v1/tenants/{tenant_id}/invitations`
   - request: `{ email, role }`
   - response: invitation metadata (without exposing sensitive internals beyond what is required)
3. Introduce invitation email delivery service:
   - build acceptance URL based on frontend base URL
   - send templated email with tenant name, inviter identity, role, expiry, accept CTA
4. Keep acceptance endpoint:
   - `POST /api/v1/tenants/invitations/{token}/accept`
   - enforce existing checks: token exists, not accepted, not expired, matching logged-in email
5. Improve error semantics for UI consumption:
   - explicit details for already member, expired token, wrong email, invitation not found

### Frontend

1. Fix invite mutation endpoint in tenant hooks:
   - from `/tenants/{id}/members`
   - to `/tenants/{id}/invitations`
2. Add invitation acceptance route/page:
   - route example: `/invitations/:token`
   - if unauthenticated, redirect to login preserving return path
   - after login, call accept endpoint and show success/failure states
3. Improve invite/accept UX:
   - map backend errors to clear user messages
   - maintain toast feedback for success/failure

### Configuration

1. Add backend email configuration variables (provider/SMTP, sender, frontend base URL).
2. Provide safe defaults for local/dev (log-only mode or disabled mail send with clear warning).
3. Document required env vars for production deployment.

## Required Changes

### Backend code

1. `code/backend/app/api/tenants.py`
   - ensure invite endpoint remains canonical and wired to mail service
   - keep robust accept endpoint behavior
2. `code/backend/app/services/` (new mail service module)
   - email sender abstraction
   - invitation email template builder
3. `code/backend/app/config.py`
   - email and frontend URL settings
4. `code/backend/deploy/env.template`
   - add required env vars for invitation email flow

### Frontend code

1. `code/frontend/src/hooks/useTenants.ts`
   - switch invite endpoint to `/invitations`
   - improve surfaced error detail
2. `code/frontend/src/pages/` and router setup
   - add invitation acceptance page
   - register route in app router
3. Login redirect handling (if needed)
   - preserve target route for post-login accept flow

### Documentation

1. `product/features/tenants.md`
   - define full invitation lifecycle
2. `product/features/auth.md`
   - document invite acceptance auth constraints
3. `system/interfaces.md`
   - ensure endpoint contracts are explicit and synchronized

## Testing Strategy

### Backend tests (pytest)

1. `test_invite_member_success`:
   - owner/admin creates invitation
   - assert 201 and persisted invitation data
2. `test_invite_member_already_member_conflict`:
   - inviting existing member returns 409
3. `test_invite_member_requires_owner_or_admin`:
   - unauthorized role receives 403
4. `test_accept_invitation_success`:
   - matching logged-in email accepts token and becomes tenant member
5. `test_accept_invitation_expired`:
   - expired token returns 400
6. `test_accept_invitation_wrong_email`:
   - different user email returns 403
7. `test_invitation_email_dispatch_called`:
   - mock mail sender and assert send invocation on invite creation

### Frontend tests (vitest)

1. Hook test for `useInviteMember`:
   - posts to `/tenants/:tenantId/invitations`
2. Tenant settings invite form test:
   - success and error states
3. Invitation acceptance page tests:
   - success flow
   - unauthenticated redirect flow
   - invalid/expired token error rendering

### E2E tests (playwright)

1. Owner invites user from tenant settings and sees success feedback.
2. Invited user opens acceptance link, authenticates, joins tenant successfully.
3. Reusing the same invitation token fails with clear message.

## Acceptance Criteria

1. Tenant invite from UI succeeds and targets canonical invitations endpoint.
2. Invitation email is sent with a valid acceptance link.
3. Invited user can accept from browser through dedicated frontend route.
4. Role and tenant membership are created exactly once on acceptance.
5. Expired, invalid, already accepted, and wrong-email scenarios return clear errors.
6. Backend + frontend + e2e regression tests cover the full flow.

## Risks and Mitigations

1. Risk: email provider misconfiguration blocks delivery.
   - Mitigation: startup/config validation and clear logs/health diagnostics.
2. Risk: token link points to wrong frontend origin.
   - Mitigation: explicit `FRONTEND_BASE_URL` configuration and environment-specific tests.
3. Risk: invitation abuse/spam.
   - Mitigation: add request throttling/rate-limit at API gateway or backend middleware.

## Rollout Plan

1. Implement endpoint contract alignment and tests first.
2. Add mail service in non-blocking mode for development.
3. Add frontend acceptance route and UX.
4. Enable production mail provider and run e2e smoke test.
5. Announce feature availability in release notes.