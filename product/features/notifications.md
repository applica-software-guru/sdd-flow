---
title: "Notifications"
status: synced
author: ""
last-modified: "2026-03-16T00:00:00.000Z"
version: "1.0"
---

# Notifications

## Overview

Users receive notifications for events relevant to them. Notifications appear in the web UI and can optionally be sent via email.

## Events That Trigger Notifications

- **Assigned to you**: a CR or bug is assigned to you
- **Status change**: a CR or bug you created or are assigned to changes status
- **New comment**: someone comments on a CR or bug you're involved in
- **Invitation**: you're invited to a tenant
- **Mention**: someone mentions you in a comment (`@username`)

## Features

### In-App Notifications

- Bell icon in the header with unread count badge
- Dropdown panel showing recent notifications
- Mark as read / mark all as read
- Click notification to navigate to the relevant item

### Email Notifications

- Optional — users can enable/disable per event type in their profile settings
- Sent as plain text emails with a link to the item
- Batched: if multiple events happen within 5 minutes, send one summary email

### Notification Preferences

- Per-user settings in profile:
  - In-app: always on
  - Email: toggle per event type (default: off)
