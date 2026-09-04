---
title: "Notifications"
status: synced
author: ""
last-modified: "2026-07-17T00:00:00.000Z"
version: "1.1"
---

# Notifications

## Overview

Users receive notifications for events relevant to them. Notifications appear in the web UI and can optionally be sent via email.

## Events That Trigger Notifications

- **Assigned to you** (`assigned`): a CR or bug is assigned to you
- **Status change** (`status_changed`): a CR or bug you created or are assigned to changes status
- **New comment** (`comment_added`): someone comments on a CR or bug you're involved in
- **Content change** (`content_changed`): the title or body of a CR or bug you're involved in is actually modified (no-op saves trigger nothing)
- **Invitation**: you're invited to a tenant
- **Mention**: someone mentions you in a comment (`@username`)
- **Worker jobs**: a worker job you created completes or fails, or asks you a question

The **actors** of a CR/bug are the union of its author, its current assignee (if any), and all distinct users who commented on it — excluding the user who triggered the event and inactive tenant members.

## Features

### In-App Notifications

- Bell icon in the header with unread count badge
- Dropdown panel showing recent notifications
- Mark as read / mark all as read
- Click notification to navigate to the relevant item

### Email Notifications

- Optional — users can enable/disable per event type in their profile settings
- Sent as plain text emails with a link to the item
- Deep links for CR/bug notifications point to the item route with the `#comments` anchor so the page opens directly at the comments section
- Coalescing: multiple `comment_added` events for the same item within a 5-minute window are batched into one email per recipient
- Notification/email dispatch failures never fail the triggering action (fire-and-forget with error logging)

### Notification Preferences

- Per-user settings in profile:
  - In-app: always on
  - Email: toggle per event type
- Defaults: `comment_added` email is **on** by default; all other event types default to **off** (`content_changed` in particular is strictly opt-in)
