---
title: "Seed default admin user on first startup"
status: applied
author: "user"
created-at: "2026-03-16T00:00:00.000Z"
---

# Seed default admin user on first startup

## Problem

When the application starts for the first time, there is no user account available. The only way to create one is via the register API, but there is no admin user to manage tenants and projects.

## Solution

Add a startup routine in the backend that runs on application boot. On first launch (when the `users` table is empty), it should:

1. Create a default admin user with:
   - Email: `admin@sddflow.dev`
   - Password: randomly generated (16 chars)
   - Display name: `Admin`
   - `email_verified`: true
2. Create a default tenant named "Default" (slug: `default`)
3. Add the admin user as **Owner** of that tenant
4. Print the credentials to stdout in a clearly visible format, e.g.:

```
============================================
  SDD Flow — First Run Setup
============================================
  Admin account created:
    Email:    admin@sddflow.dev
    Password: <random-password>

  Default tenant: "Default"

  ⚠ Change this password after first login!
============================================
```

5. If the `users` table is **not empty**, skip silently — do nothing.

## Affected files

- `system/architecture.md` — document the seed behavior
- `product/features/auth.md` — mention the default admin
- `code/backend/app/main.py` — add startup lifespan hook
- `code/backend/app/services/seed.py` — new file with the seed logic
