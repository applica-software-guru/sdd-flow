---
title: "User menu email overflows dropdown bounds when too long"
status: resolved
author: "roberto"
created-at: "2026-03-18T00:00:00.000Z"
---

## Description

In the top-right user menu, when the authenticated user has a very long email address, the email text exceeds the dropdown panel width and renders outside its visual bounds.

## Steps to reproduce

1. Log in with a user account whose email local-part is very long (for example: `averyveryveryveryveryveryverylongaddress@example.com`).
2. Open the user menu from the top-right avatar button.
3. Observe the email in the profile header section of the dropdown.

## Expected behavior

The email should remain constrained within the dropdown, using truncation or wrapping without breaking layout boundaries.

## Actual behavior

The email is displayed as a single unbroken string and visually overflows the dropdown box.

## Root cause

In `code/frontend/src/components/Layout.tsx`, the dropdown has a fixed width (`w-48`) while the email paragraph has no overflow handling classes (no `truncate`, `break-all`, `break-words`, or wrapping constraints). Long, non-breaking content therefore exceeds the container width.

## Suggested fix

Apply overflow-safe text handling on the email element (for example `truncate` with a `title` tooltip, or `break-all`/`break-words`) and optionally increase responsive dropdown width where needed.