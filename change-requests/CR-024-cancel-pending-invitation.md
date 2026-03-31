---
title: "Cancel pending invitation"
status: applied
author: "user"
created-at: "2026-03-31T00:00:00.000Z"
---

## Summary

Owners and Admins must be able to cancel a pending invitation before it is accepted.

Member removal already works end-to-end (backend `DELETE /tenants/:tenant_id/members/:user_id` + frontend confirmation dialog). This CR only addresses the missing cancellation of **pending invitations**.

---

## Analysis

### What exists

- `POST /tenants/:tenant_id/invitations` — creates invitation, sends email
- `GET /tenants/:tenant_id/invitations` — lists invitations with computed status (`pending` / `accepted` / `expired`)
- `DELETE /tenants/:tenant_id/members/:user_id` — removes an existing member (Owner/Admin only, owner-protected)
- Frontend `SettingsPage` renders the invitations list and the member list with a remove button per member
- MongoDB TTL index on `TenantInvitation.expires_at` auto-deletes expired documents after 7 days

### What is missing

- `DELETE /tenants/:tenant_id/invitations/:invitation_id` — no endpoint to revoke a pending invitation
- No cancel button in the frontend invitations list

### Side effects and edge cases

| Scenario | Behaviour |
|---|---|
| Invitation already accepted | Endpoint returns `400` — accepted invitations cannot be cancelled (the membership already exists; use member removal instead) |
| Invitation already expired | MongoDB TTL may have already deleted the document; endpoint returns `404`, which is acceptable |
| User clicks the invite link after cancellation | `POST /invitations/:token/accept` returns `404` — handled naturally since the document is deleted |
| Accept and cancel race | If the accept transaction completes first, `accepted_at` is set; the cancel endpoint checks this and returns `400` before deleting |
| Audit trail | A `invitation.cancelled` event must be logged (same pattern as `invitation.created`) |
| Email on cancellation | No notification email is sent — keep it simple; the invitee's link simply stops working |
| Permissions | Only Owner or Admin may cancel, consistent with invitation creation |

---

## Required changes

### `system/interfaces.md`

Add the following endpoint in the Tenants section, after the existing `POST /tenants/:tenant_id/invitations` block:

```
### DELETE /tenants/:tenant_id/invitations/:invitation_id

Cancel a pending invitation. Owner or Admin only.

**Response:** `204`

Validation and behaviour:
- Returns `404` if the invitation does not exist or belongs to a different tenant
- Returns `400` if the invitation has already been accepted (use member removal instead)
```

### `product/features/tenants.md`

In the **Invitation Lifecycle** section, add:

> - Owner or Admin can cancel a pending invitation at any time before it is accepted; the acceptance link becomes immediately invalid

In the **Invitation Error States** section, add:

> - Attempting to accept a cancelled invitation returns not found

In the **Tenant Settings** section, update the invitation management bullet:

> - Invitation management: send, cancel pending invitations, with clear success/error feedback

### `system/entities.md`

In the **AuditLogEntry** event catalogue, add `invitation.cancelled` alongside `invitation.created`.

---

### Frontend — `SettingsPage`

The invitations list currently renders email, role metadata, and a status badge only. No action is available on individual rows.

Add a **Cancel** button on each invitation row where `status === 'pending'`:

- Clicking it opens a `ConfirmDialog` ("Cancel invitation", "The invitation link will stop working immediately.")
- On confirm, calls the new `useCancelInvitation` hook and invalidates the invitations query
- The button is not rendered for `accepted` or `expired` invitations
- Consistent with the existing "Remove" button pattern used in the members list (same red text style, same `ConfirmDialog` component)

New state needed in `SettingsPage`:
- `cancellingInvitationId: string | null` — mirrors the existing `removingMemberId` pattern

### Frontend — `useTenants.ts`

Add a `useCancelInvitation(tenantId)` hook:

- Calls `DELETE /api/v1/tenants/:tenant_id/invitations/:invitation_id`
- On success, invalidates the `['tenants', tenantId, 'invitations']` query key
- Same shape as the existing `useRemoveMember` hook
