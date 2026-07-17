---
title: "Severity filter not working on Bugs page"
status: resolved
severity: major
---

## Description

On the Bugs list page, the Severity filter dropdown has no effect: selecting any severity (Critical, Major, Minor, Trivial) shows all bugs regardless.

## Steps to Reproduce

1. Navigate to the Bugs page
2. Open the Severity filter dropdown
3. Select any severity (e.g. "Critical")
4. Observe that the bug list is not filtered

## Expected Behaviour

Only bugs matching the selected severity are displayed.

## Actual Behaviour

The full bug list is shown regardless of the selected severity.

## Root Cause

The frontend correctly sends `?severity=<value>` as a query parameter, but the backend `GET /tenants/{tenant_id}/projects/{project_id}/bugs` endpoint did not declare or apply the `severity` filter. The parameter was silently ignored.

## Fix

In `code/backend/app/api/bugs.py`:
- Imported `BugSeverity` from `app.models.bug`
- Added `severity_filter: BugSeverity | None = Query(None, alias="severity")` to `list_bugs`
- Added `query["severity"] = severity_filter.value` to the MongoDB query when the filter is set
